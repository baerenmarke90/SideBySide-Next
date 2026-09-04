import type { FormEvent } from 'react';
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import type { ChapterDetail } from '../api/generated/models/ChapterDetail';
import { normalizeClientError } from '../client/problemDetails';
import { appRoutePath, chapterDetailPath } from '../client/routes';
import {
  dateFromInput,
  loadAllPlaces,
  type SharedPlanningApis,
} from '../client/sharedPlanning';
import { resolvedLocale, useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import './SharedPlanningPages.css';

const PAGE_SIZE = 20;

type PageShape<T> = { items: T[]; nextCursor: string | null };

async function apiCall<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request();
  } catch (error) {
    throw await normalizeClientError(error);
  }
}

function nextCursor<T>(page: PageShape<T>): string | undefined {
  return page.nextCursor ?? undefined;
}

function formatDate(value: Date | null): string | null {
  if (!value) return null;
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(value);
}

export function ChaptersOverviewPage({
  apis,
  spaceId,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const chapters = useInfiniteQuery({
    queryKey: ['m5-s3', 'chapters', spaceId],
    queryFn: ({ pageParam }) =>
      apiCall(() =>
        apis.chapters.listChapters({
          spaceId,
          cursor: pageParam,
          limit: PAGE_SIZE,
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: nextCursor<ChapterDetail>,
    retry: false,
  });

  const placesQuery = useQuery({
    queryKey: ['m5-s3', 'chapter-places', spaceId],
    queryFn: () => apiCall(() => loadAllPlaces(apis, spaceId)),
    staleTime: 30_000,
    retry: false,
  });

  const createChapter = useMutation({
    mutationFn: (values: {
      title: string;
      description?: string;
      startOn?: Date;
      endOn?: Date;
      placeId?: string;
    }) =>
      apiCall(() =>
        apis.chapters.createChapter({ spaceId, chapterCreate: values }),
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'chapters', spaceId],
      });
    },
  });

  const chapterItems = chapters.data?.pages.flatMap((page) => page.items) ?? [];

  function submitChapter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const description = String(data.get('description')).trim();
    const startOn = dateFromInput(String(data.get('startOn')).trim());
    const endOn = dateFromInput(String(data.get('endOn')).trim());
    const placeId = String(data.get('placeId')).trim();
    createChapter.mutate(
      {
        title: String(data.get('title')).trim(),
        description: description || undefined,
        startOn: startOn ?? undefined,
        endOn: endOn ?? undefined,
        placeId: placeId || undefined,
      },
      { onSuccess: () => form.reset() },
    );
  }

  return (
    <div className="page planning-page">
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('story')}>
            {t('m5s3.common.backToStory')}
          </Link>
        }
        eyebrow={t('navigation.story')}
        title={t('m5s3.chapter.heading')}
        description={t('m5s3.chapter.intro')}
      />

      <section className="planning-subsection">
        {chapters.isLoading ? (
          <UiState kind="loading" title={t('states.loading.title')} />
        ) : null}
        {chapters.error ? (
          <ProblemState
            error={chapters.error}
            onRetry={() => void chapters.refetch()}
          />
        ) : null}

        {chapterItems.length === 0 && !chapters.isLoading && !chapters.error ? (
          <p className="planning-empty">{t('m5s3.common.empty')}</p>
        ) : (
          <ul className="planning-list">
            {chapterItems.map((chapter) => (
              <li className="planning-card-item" key={chapter.id}>
                <Link
                  className="planning-card planning-card-link"
                  to={chapterDetailPath(chapter.id)}
                >
                  <div className="planning-card-copy">
                    <h3>{chapter.title}</h3>
                    {formatDate(chapter.startOn) ? (
                      <p className="planning-meta">
                        {formatDate(chapter.startOn)}
                      </p>
                    ) : null}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}

        {chapters.hasNextPage ? (
          <button
            type="button"
            className="tertiary compact-action"
            onClick={() => void chapters.fetchNextPage()}
            disabled={chapters.isFetchingNextPage}
          >
            {chapters.isFetchingNextPage
              ? t('m5s3.common.loadingMore')
              : t('m5s3.common.loadMore')}
          </button>
        ) : null}

        <details className="planning-create" id="chapter-create-details">
          <summary id="chapter-title">{t('m5s3.chapter.create')}</summary>
          <form
            onSubmit={submitChapter}
            className="form-grid planning-create-form"
          >
            <label htmlFor="chapter-name">{t('m5s3.common.title')}</label>
            <input id="chapter-name" name="title" required maxLength={200} />
            <label htmlFor="chapter-desc">{t('m5s3.common.description')}</label>
            <textarea id="chapter-desc" name="description" rows={3} />
            <div className="planning-coordinate-grid">
              <div className="field-group">
                <label htmlFor="chapter-start">
                  {t('m5s3.chapter.startOn')}
                </label>
                <input id="chapter-start" name="startOn" type="date" />
              </div>
              <div className="field-group">
                <label htmlFor="chapter-end">{t('m5s3.chapter.endOn')}</label>
                <input id="chapter-end" name="endOn" type="date" />
              </div>
            </div>
            <label htmlFor="chapter-place">{t('m5s3.common.place')}</label>
            <select
              id="chapter-place"
              name="placeId"
              defaultValue=""
              disabled={placesQuery.isLoading}
            >
              <option value="">{t('m5s3.common.noPlace')}</option>
              {(placesQuery.data ?? []).map((place) => (
                <option key={place.id} value={place.id}>
                  {place.name}
                </option>
              ))}
            </select>
            <button type="submit" disabled={createChapter.isPending}>
              {createChapter.isPending
                ? t('m5s3.common.saving')
                : t('m5s3.common.save')}
            </button>
            {createChapter.error ? (
              <ProblemState error={createChapter.error} />
            ) : null}
          </form>
        </details>
      </section>
    </div>
  );
}
