import { type FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { MemoriesApi } from '../api/generated/apis/MemoriesApi';
import { MediaType } from '../api/generated/models/MediaType';
import type { MemoryDetail } from '../api/generated/models/MemoryDetail';
import {
  memoryDateInputValue,
  memoryIfMatch,
  memoryUpdatePayload,
  type MemoryEditValues,
} from '../client/memoryProduct';
import { normalizeClientError } from '../client/problemDetails';
import {
  appRoutePath,
  memoryDetailPath,
  memoryEditPath,
} from '../client/routes';
import { resolvedLocale, useTranslation } from '../i18n';
import { MemoryPreview } from './MemoryPreview';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

export type MemoryProductMode = 'detail' | 'edit';

function formatDateOnly(value: Date): string {
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'long',
    timeZone: 'UTC',
  }).format(value);
}

function formatCreatedAt(value: Date): string {
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
  }).format(value);
}

export function MemoryProductPage({
  mode,
  memoriesApi,
  spaceId,
  loadMemoryImage,
}: {
  mode: MemoryProductMode;
  memoriesApi: MemoriesApi;
  spaceId: string;
  loadMemoryImage: (memoryId: string, attachmentId: string) => Promise<string>;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const params = useParams();
  const queryClient = useQueryClient();
  const memoryId = params.memoryId;
  const memoryKey = ['memory', spaceId, memoryId] as const;
  const [confirmDelete, setConfirmDelete] = useState(false);

  const memoryQuery = useQuery({
    queryKey: memoryKey,
    queryFn: async () => {
      if (!memoryId) throw new Error('Missing memory route parameter.');
      try {
        return await memoriesApi.getMemory({ spaceId, memoryId });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    enabled: Boolean(memoryId),
    retry: false,
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      memory,
      values,
    }: {
      memory: MemoryDetail;
      values: MemoryEditValues;
    }) => {
      try {
        return await memoriesApi.updateMemory({
          spaceId,
          memoryId: memory.id,
          ifMatch: memoryIfMatch(memory),
          memoryUpdate: memoryUpdatePayload(values),
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (memory) => {
      queryClient.setQueryData(memoryKey, memory);
      await queryClient.invalidateQueries({ queryKey: ['story', spaceId] });
      navigate(memoryDetailPath(memory.id), { replace: true });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (memory: MemoryDetail) => {
      try {
        await memoriesApi.deleteMemory({
          spaceId,
          memoryId: memory.id,
          ifMatch: memoryIfMatch(memory),
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: memoryKey });
      await queryClient.invalidateQueries({ queryKey: ['story', spaceId] });
      navigate(appRoutePath('story'), { replace: true });
    },
  });

  async function reloadCurrentMemory() {
    updateMutation.reset();
    deleteMutation.reset();
    setConfirmDelete(false);
    await memoryQuery.refetch();
  }

  if (!memoryId) {
    return (
      <UiState
        kind="error"
        title={t('states.unknown.title')}
        body={t('states.unknown.body')}
      />
    );
  }

  if (memoryQuery.isLoading) {
    return <UiState kind="loading" title={t('memoryProduct.loading')} />;
  }

  if (memoryQuery.error) {
    return (
      <ProblemState
        error={memoryQuery.error}
        onRetry={() => void memoryQuery.refetch()}
      />
    );
  }

  const memory = memoryQuery.data;
  if (!memory) return null;

  if (mode === 'edit') {
    if (!memory.capabilities.canEdit) {
      return (
        <div className="page">
          <PageHeader
            before={
              <Link className="back-link" to={memoryDetailPath(memory.id)}>
                {t('memoryProduct.detailEyebrow')}
              </Link>
            }
            eyebrow={t('memoryProduct.editEyebrow')}
            title={t('memoryProduct.editHeading')}
            description={t('memoryProduct.editIntro')}
          />
          <UiState
            kind="permission"
            title={t('memoryProduct.editNotAllowedTitle')}
            body={t('memoryProduct.editNotAllowedBody')}
          />
        </div>
      );
    }

    function submit(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      updateMutation.mutate({
        memory,
        values: {
          title: String(data.get('title') || ''),
          body: String(data.get('body') || ''),
          happenedOn: String(data.get('happenedOn') || ''),
        },
      });
    }

    return (
      <div className="page create-page">
        <PageHeader
          before={
            <Link className="back-link" to={memoryDetailPath(memory.id)}>
              {t('memoryProduct.backToStory')}
            </Link>
          }
          eyebrow={t('memoryProduct.editEyebrow')}
          title={t('memoryProduct.editHeading')}
          description={t('memoryProduct.editIntro')}
          className="create-heading"
        />

        <section className="form-card" aria-labelledby="memory-edit-heading">
          <h2 id="memory-edit-heading" className="sr-only">
            {t('memoryProduct.formAria')}
          </h2>
          <form
            key={memory.version}
            onSubmit={submit}
            className="form-grid memory-form"
          >
            <div className="field-group">
              <label htmlFor="memory-edit-title">{t('memory.titleLabel')}</label>
              <input
                id="memory-edit-title"
                name="title"
                required
                maxLength={200}
                defaultValue={memory.title}
              />
            </div>
            <div className="field-group">
              <label htmlFor="memory-edit-body">{t('memory.bodyLabel')}</label>
              <textarea
                id="memory-edit-body"
                name="body"
                rows={6}
                defaultValue={memory.body}
              />
            </div>
            <div className="field-group">
              <label htmlFor="memory-edit-date">{t('memory.dateLabel')}</label>
              <input
                id="memory-edit-date"
                name="happenedOn"
                type="date"
                defaultValue={memoryDateInputValue(memory.happenedOn)}
              />
            </div>
            <div className="form-actions">
              <Link
                className="button-link secondary-link"
                to={memoryDetailPath(memory.id)}
              >
                {t('common.cancel')}
              </Link>
              <button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending
                  ? t('memoryProduct.saving')
                  : t('memoryProduct.save')}
              </button>
            </div>
          </form>
          {updateMutation.error ? (
            <ProblemState
              error={updateMutation.error}
              onRetry={() => void reloadCurrentMemory()}
            />
          ) : null}
        </section>
      </div>
    );
  }

  const imageAttachments = memory.attachments
    .filter(
      (attachment) =>
        attachment.mediaType === MediaType.IMAGE && attachment.status === 'READY',
    )
    .sort((left, right) => left.position - right.position);

  return (
    <div className="page memory-product-page">
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('story')}>
            {t('memoryProduct.backToStory')}
          </Link>
        }
        eyebrow={t('memoryProduct.detailEyebrow')}
        title={memory.title}
        description={t('memoryProduct.detailIntro')}
        action={
          memory.capabilities.canEdit ? (
            <Link className="button-link secondary-link" to={memoryEditPath(memory.id)}>
              {t('memoryProduct.edit')}
            </Link>
          ) : undefined
        }
      />

      <article className="story-surface memory-detail-card">
        <dl className="memory-meta-grid">
          <div>
            <dt>{t('memoryProduct.authorLabel')}</dt>
            <dd>{memory.author.displayName}</dd>
          </div>
          <div>
            <dt>{t('memoryProduct.happenedOnLabel')}</dt>
            <dd>
              {memory.happenedOn
                ? formatDateOnly(memory.happenedOn)
                : t('memoryProduct.noDate')}
            </dd>
          </div>
          <div>
            <dt>{t('memoryProduct.createdAtLabel')}</dt>
            <dd>{formatCreatedAt(memory.createdAt)}</dd>
          </div>
        </dl>

        <p className="memory-detail-body">
          {memory.body || t('memoryProduct.noBody')}
        </p>

        <section aria-labelledby="memory-photos-heading">
          <div className="section-head memory-section-head">
            <div>
              <p className="section-kicker">{t('memory.photoLabel')}</p>
              <h2 id="memory-photos-heading">{t('memoryProduct.photosHeading')}</h2>
            </div>
          </div>
          {imageAttachments.length > 0 ? (
            <div className="memory-gallery" aria-label={t('memoryProduct.galleryAria')}>
              {imageAttachments.map((attachment) => (
                <MemoryPreview
                  key={attachment.id}
                  memoryId={memory.id}
                  attachmentId={attachment.id}
                  loadImage={loadMemoryImage}
                />
              ))}
            </div>
          ) : (
            <p className="muted">{t('memoryProduct.noPhotos')}</p>
          )}
        </section>

        {memory.capabilities.canDelete ? (
          <section className="memory-danger-zone" aria-labelledby="memory-delete-heading">
            {!confirmDelete ? (
              <button
                type="button"
                className="secondary"
                onClick={() => setConfirmDelete(true)}
              >
                {t('memoryProduct.delete')}
              </button>
            ) : (
              <div className="memory-delete-confirmation" role="alert">
                <div>
                  <h2 id="memory-delete-heading">
                    {t('memoryProduct.deleteConfirmTitle')}
                  </h2>
                  <p>{t('memoryProduct.deleteConfirmBody')}</p>
                </div>
                <div className="memory-actions">
                  <button
                    type="button"
                    className="tertiary"
                    onClick={() => setConfirmDelete(false)}
                    disabled={deleteMutation.isPending}
                  >
                    {t('memoryProduct.deleteCancel')}
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteMutation.mutate(memory)}
                    disabled={deleteMutation.isPending}
                  >
                    {deleteMutation.isPending
                      ? t('memoryProduct.deleting')
                      : t('memoryProduct.deleteConfirm')}
                  </button>
                </div>
              </div>
            )}
            {deleteMutation.error ? (
              <ProblemState
                error={deleteMutation.error}
                onRetry={() => void reloadCurrentMemory()}
              />
            ) : null}
          </section>
        ) : null}
      </article>
    </div>
  );
}
