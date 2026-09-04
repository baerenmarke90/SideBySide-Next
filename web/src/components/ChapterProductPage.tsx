import { useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { ChapterDetail } from '../api/generated/models/ChapterDetail';
import { normalizeClientError } from '../client/problemDetails';
import {
  dateFromInput,
  dateOnlyInput,
  loadAllPlaces,
  planningIfMatch,
  type SharedPlanningApis,
} from '../client/sharedPlanning';
import { STORY_CHAPTERS_ROUTE } from '../client/routes';
import { authorSummaryQueryKeys } from '../client/authorSummaryConsumers';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { PlanningRelationManager } from './PlanningRelationManager';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import './SharedPlanningPages.css';

async function apiCall<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request();
  } catch (error) {
    throw await normalizeClientError(error);
  }
}

export function ChapterProductPage({
  apis,
  spaceId,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const { chapterId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const key = authorSummaryQueryKeys.chapterDetail(spaceId, chapterId);

  const chapterQuery = useQuery({
    queryKey: key,
    queryFn: () => {
      if (!chapterId) throw new Error('Missing Chapter route parameter.');
      return apiCall(() => apis.chapters.getChapter({ spaceId, chapterId }));
    },
    enabled: Boolean(chapterId),
    retry: false,
  });
  const placesQuery = useQuery({
    queryKey: ['m5-s3', 'chapter-places', spaceId],
    queryFn: () => apiCall(() => loadAllPlaces(apis, spaceId)),
    staleTime: 30_000,
    retry: false,
  });

  const updateMutation = useMutation({
    mutationFn: ({
      chapter,
      title,
      description,
      startOn,
      endOn,
      placeId,
    }: {
      chapter: ChapterDetail;
      title: string;
      description: string | null;
      startOn: Date | null;
      endOn: Date | null;
      placeId: string | null;
    }) =>
      apiCall(() =>
        apis.chapters.updateChapter({
          spaceId,
          chapterId: chapter.id,
          ifMatch: planningIfMatch(chapter),
          chapterUpdate: { title, description, startOn, endOn, placeId },
        }),
      ),
    onSuccess: async (chapter) => {
      queryClient.setQueryData(key, chapter);
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['m5-s3', 'chapters', spaceId],
        }),
        queryClient.invalidateQueries({ queryKey: key }),
      ]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (chapter: ChapterDetail) =>
      apiCall(() =>
        apis.chapters.deleteChapter({
          spaceId,
          chapterId: chapter.id,
          ifMatch: planningIfMatch(chapter),
        }),
      ),
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: key });
      await queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'chapters', spaceId],
      });
      navigate(STORY_CHAPTERS_ROUTE, { replace: true });
    },
  });

  if (!chapterId)
    return (
      <UiState
        kind="error"
        title={t('states.unknown.title')}
        body={t('states.unknown.body')}
      />
    );
  if (chapterQuery.isLoading)
    return <UiState kind="loading" title={t('m5s3.chapter.loading')} />;
  if (chapterQuery.error)
    return (
      <ProblemState
        error={chapterQuery.error}
        onRetry={() => void chapterQuery.refetch()}
      />
    );
  const chapter = chapterQuery.data;
  if (!chapter) return null;

  function submitEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!chapter) return;
    const data = new FormData(event.currentTarget);
    const description = String(data.get('description')).trim();
    const startOn = dateFromInput(String(data.get('startOn')).trim()) ?? null;
    const endOn = dateFromInput(String(data.get('endOn')).trim()) ?? null;
    const placeId = String(data.get('placeId')).trim();
    updateMutation.mutate({
      chapter,
      title: String(data.get('title')).trim(),
      description: description || null,
      startOn,
      endOn,
      placeId: placeId || null,
    });
  }

  return (
    <div className="page planning-page">
      <PageHeader
        before={
          <Link className="back-link" to={STORY_CHAPTERS_ROUTE}>
            {t('m5s3.common.back')}
          </Link>
        }
        eyebrow={t('m5s3.chapter.detailEyebrow')}
        title={chapter.title}
        description={chapter.description || t('m5s3.chapter.noDescription')}
      />

      <section className="planning-subsection">
        <h2>{t('m5s3.common.edit')}</h2>
        {chapter.capabilities.canEdit ? (
          <form className="form-grid" onSubmit={submitEdit}>
            <label htmlFor="chapter-edit-title">{t('m5s3.common.title')}</label>
            <input
              id="chapter-edit-title"
              name="title"
              required
              maxLength={200}
              defaultValue={chapter.title}
            />
            <label htmlFor="chapter-edit-description">
              {t('m5s3.common.description')}
            </label>
            <textarea
              id="chapter-edit-description"
              name="description"
              rows={4}
              defaultValue={chapter.description ?? ''}
            />
            <div className="planning-coordinate-grid">
              <div className="field-group">
                <label htmlFor="chapter-edit-start">
                  {t('m5s3.chapter.startOn')}
                </label>
                <input
                  id="chapter-edit-start"
                  name="startOn"
                  type="date"
                  defaultValue={dateOnlyInput(chapter.startOn)}
                />
              </div>
              <div className="field-group">
                <label htmlFor="chapter-edit-end">
                  {t('m5s3.chapter.endOn')}
                </label>
                <input
                  id="chapter-edit-end"
                  name="endOn"
                  type="date"
                  defaultValue={dateOnlyInput(chapter.endOn)}
                />
              </div>
            </div>
            <label htmlFor="chapter-edit-place">{t('m5s3.common.place')}</label>
            <select
              id="chapter-edit-place"
              name="placeId"
              defaultValue={chapter.placeId ?? ''}
            >
              <option value="">{t('m5s3.common.noPlace')}</option>
              {placesQuery.data?.map((place) => (
                <option key={place.id} value={place.id}>
                  {place.name}
                </option>
              ))}
            </select>
            <button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending
                ? t('m5s3.common.saving')
                : t('m5s3.common.saveChanges')}
            </button>
            {updateMutation.error ? (
              <ProblemState
                error={updateMutation.error}
                onRetry={() => void chapterQuery.refetch()}
              />
            ) : null}
          </form>
        ) : (
          <p className="planning-meta">{t('m5s3.common.readOnly')}</p>
        )}
      </section>

      <PlanningRelationManager
        apis={apis}
        spaceId={spaceId}
        ownerKind="chapter"
        ownerId={chapter.id}
      />

      {chapter.capabilities.canDelete ? (
        <section
          className="planning-danger-zone"
          aria-labelledby="chapter-delete-heading"
        >
          <h2 id="chapter-delete-heading">{t('m5s3.common.deleteHeading')}</h2>
          <p>{t('m5s3.chapter.deleteConsequence')}</p>
          {!confirmDelete ? (
            <button
              type="button"
              className="danger"
              onClick={() => setConfirmDelete(true)}
            >
              {t('m5s3.common.delete')}
            </button>
          ) : (
            <div className="planning-confirm-row">
              <button
                type="button"
                className="danger"
                onClick={() => deleteMutation.mutate(chapter)}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending
                  ? t('m5s3.common.deleting')
                  : t('m5s3.common.confirmDelete')}
              </button>
              <button
                type="button"
                className="tertiary"
                onClick={() => setConfirmDelete(false)}
              >
                {t('common.cancel')}
              </button>
            </div>
          )}
          {deleteMutation.error ? (
            <ProblemState
              error={deleteMutation.error}
              onRetry={() => void chapterQuery.refetch()}
            />
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
