import { type FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { HeartEmotion } from '../api/generated/models/HeartEmotion';
import type { HeartMomentDetail } from '../api/generated/models/HeartMomentDetail';
import {
  HeartMomentDetailFromJSON,
  HeartMomentDetailToJSON,
} from '../api/generated/models/HeartMomentDetail';
import type { HeartMomentUpdate } from '../api/generated/models/HeartMomentUpdate';
import {
  deleteProductReadCacheEntry,
  loadProductWithReadCache,
} from '../client/productReadCache';
import { normalizeClientError } from '../client/problemDetails';
import type { ReferenceApis } from '../client/referenceFlow';
import {
  appRoutePath,
  heartMomentDetailPath,
  heartMomentEditPath,
} from '../client/routes';
import { useAttachmentDrafts } from '../client/useAttachmentDrafts';
import { resolvedLocale, useTranslation } from '../i18n';
import { AttachmentDraftPicker } from './AttachmentDraftPicker';
import { CommentsPanel } from './CommentsPanel';
import { MediaGallery } from './MediaGallery';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

export type HeartMomentProductMode = 'create' | 'detail' | 'edit';

type HeartEmotionValue = (typeof HeartEmotion)[keyof typeof HeartEmotion];
type ContentVisibilityValue =
  (typeof ContentVisibility)[keyof typeof ContentVisibility];

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

function dateInputValue(value: Date): string {
  return value.toISOString().slice(0, 10);
}

export function HeartMomentProductPage({
  mode,
  apis,
  apiBaseUrl,
  accessToken,
  spaceId,
  currentAccountId,
  loadAttachment,
}: {
  mode: HeartMomentProductMode;
  apis: ReferenceApis;
  apiBaseUrl: string;
  accessToken: string;
  spaceId: string;
  currentAccountId: string;
  loadAttachment: (
    heartMomentId: string,
    attachmentId: string,
  ) => Promise<string>;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const params = useParams();
  const queryClient = useQueryClient();
  const heartMomentId = params.heartMomentId;
  const queryKey = ['heartMoment', spaceId, heartMomentId] as const;
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [removeExistingPhoto, setRemoveExistingPhoto] = useState(false);
  const attachments = useAttachmentDrafts({
    apis,
    apiBaseUrl,
    accessToken,
    spaceId,
  });

  const heartMomentQuery = useQuery({
    queryKey,
    queryFn: async () => {
      if (!heartMomentId)
        throw new Error('Missing HeartMoment route parameter.');
      return loadProductWithReadCache({
        accountId: currentAccountId,
        spaceId,
        kind: 'heartMoment',
        resourceId: heartMomentId,
        load: () =>
          apis.heartMoments.getHeartMoment({ spaceId, heartMomentId }),
        serialize: HeartMomentDetailToJSON,
        deserialize: (payload) => HeartMomentDetailFromJSON(payload),
      });
    },
    enabled: mode !== 'create' && Boolean(heartMomentId),
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: async (values: {
      text: string;
      emotion: HeartEmotionValue;
      happenedOn: Date;
      visibility: ContentVisibilityValue;
      attachmentId?: string;
    }) => {
      try {
        return await apis.heartMoments.createHeartMoment({
          spaceId,
          heartMomentCreate: values,
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (heartMoment) => {
      attachments.clear();
      await queryClient.invalidateQueries({ queryKey: ['story', spaceId] });
      navigate(heartMomentDetailPath(heartMoment.id), {
        replace: true,
        state: { saved: true },
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      current,
      update,
    }: {
      current: HeartMomentDetail;
      update: HeartMomentUpdate;
    }) => {
      try {
        return await apis.heartMoments.updateHeartMoment({
          spaceId,
          heartMomentId: current.id,
          ifMatch: String(current.version),
          heartMomentUpdate: update,
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onMutate: async ({ current, update }) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData(queryKey);
      queryClient.setQueryData(queryKey, {
        value: {
          ...current,
          text: update.text ?? current.text,
          emotion: update.emotion ?? current.emotion,
          happenedOn: update.happenedOn ?? current.happenedOn,
          attachment: update.attachmentId === null ? null : current.attachment,
          updatedAt: new Date(),
        },
        source: 'network',
      });
      return { previous };
    },
    onError: (_error, _variables, context) => {
      if (context?.previous)
        queryClient.setQueryData(queryKey, context.previous);
    },
    onSuccess: async (heartMoment) => {
      attachments.clear();
      setRemoveExistingPhoto(false);
      queryClient.setQueryData(queryKey, {
        value: heartMoment,
        source: 'network',
      });
      await queryClient.invalidateQueries({ queryKey: ['story', spaceId] });
      await queryClient.invalidateQueries({ queryKey });
      navigate(heartMomentDetailPath(heartMoment.id), { replace: true });
    },
  });

  const visibilityMutation = useMutation({
    mutationFn: async ({
      current,
      visibility,
    }: {
      current: HeartMomentDetail;
      visibility: ContentVisibilityValue;
    }) => {
      try {
        return await apis.heartMoments.changeHeartMomentVisibility({
          spaceId,
          heartMomentId: current.id,
          ifMatch: String(current.version),
          heartMomentVisibilityChange: { visibility },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey });
      return { previous: queryClient.getQueryData(queryKey) };
    },
    onError: (_error, _variables, context) => {
      if (context?.previous)
        queryClient.setQueryData(queryKey, context.previous);
    },
    onSuccess: async (heartMoment) => {
      queryClient.setQueryData(queryKey, {
        value: heartMoment,
        source: 'network',
      });
      await queryClient.invalidateQueries({ queryKey: ['story', spaceId] });
      await queryClient.invalidateQueries({
        queryKey: ['comments', spaceId, 'heartMoment', heartMoment.id],
      });
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (heartMoment: HeartMomentDetail) => {
      try {
        await apis.heartMoments.deleteHeartMoment({
          spaceId,
          heartMomentId: heartMoment.id,
          ifMatch: String(heartMoment.version),
        });
        await deleteProductReadCacheEntry(
          currentAccountId,
          spaceId,
          'heartMoment',
          heartMoment.id,
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey });
      await queryClient.invalidateQueries({ queryKey: ['story', spaceId] });
      navigate(appRoutePath('story'), { replace: true });
    },
  });

  if (mode === 'create') {
    function submitCreate(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      if (attachments.hasPending) return;
      const data = new FormData(event.currentTarget);
      const happenedOn = String(data.get('happenedOn') || '');
      if (!happenedOn) return;
      createMutation.mutate({
        text: String(data.get('text') || '').trim(),
        emotion: String(data.get('emotion')) as HeartEmotionValue,
        happenedOn: new Date(`${happenedOn}T00:00:00Z`),
        visibility: String(data.get('visibility')) as ContentVisibilityValue,
        attachmentId: attachments.readyIds[0],
      });
    }

    return (
      <div className="page create-page product-editor-page">
        <PageHeader
          before={
            <Link className="back-link" to={appRoutePath('story')}>
              {t('heartMomentProduct.backToStory')}
            </Link>
          }
          eyebrow={t('heartMomentProduct.createEyebrow')}
          title={t('heartMomentProduct.createHeading')}
          description={t('heartMomentProduct.createIntro')}
        />
        <section
          className="form-card product-sheet"
          aria-labelledby="heart-moment-create-heading"
        >
          <h2 id="heart-moment-create-heading" className="sr-only">
            {t('heartMomentProduct.createHeading')}
          </h2>
          <form className="form-grid" onSubmit={submitCreate}>
            <HeartMomentFields />
            <div className="field-group">
              <label htmlFor="heart-moment-create-visibility">
                {t('heartMomentProduct.visibilityLabel')}
              </label>
              <select
                id="heart-moment-create-visibility"
                name="visibility"
                defaultValue={ContentVisibility.SHARED}
              >
                <option value={ContentVisibility.SHARED}>
                  {t('heartMomentProduct.visibilityShared')}
                </option>
                <option value={ContentVisibility.PRIVATE}>
                  {t('heartMomentProduct.visibilityPrivate')}
                </option>
              </select>
            </div>
            <AttachmentDraftPicker
              id="heart-moment-create-photo"
              attachments={attachments}
              multiple={false}
            />
            <div className="form-actions">
              <Link
                className="button-link secondary-link"
                to={appRoutePath('story')}
              >
                {t('common.cancel')}
              </Link>
              <button
                type="submit"
                disabled={createMutation.isPending || attachments.hasPending}
              >
                {createMutation.isPending
                  ? t('heartMomentProduct.saving')
                  : t('heartMomentProduct.save')}
              </button>
            </div>
          </form>
          {createMutation.error ? (
            <ProblemState error={createMutation.error} />
          ) : null}
        </section>
      </div>
    );
  }

  if (!heartMomentId) {
    return (
      <UiState
        kind="error"
        title={t('states.unknown.title')}
        body={t('states.unknown.body')}
      />
    );
  }
  if (heartMomentQuery.isLoading) {
    return <UiState kind="loading" title={t('heartMomentProduct.loading')} />;
  }
  if (heartMomentQuery.error) {
    return (
      <ProblemState
        error={heartMomentQuery.error}
        onRetry={() => void heartMomentQuery.refetch()}
      />
    );
  }
  const result = heartMomentQuery.data;
  if (!result) return null;
  const heartMoment = result.value;
  const offline = result.source === 'cache';

  if (mode === 'edit') {
    if (!heartMoment.capabilities.canEdit || offline) {
      return (
        <div className="page">
          <PageHeader
            before={
              <Link
                className="back-link"
                to={heartMomentDetailPath(heartMoment.id)}
              >
                {t('heartMomentProduct.backToHeartMoment')}
              </Link>
            }
            eyebrow={t('heartMomentProduct.editEyebrow')}
            title={t('heartMomentProduct.editHeading')}
            description={t('heartMomentProduct.editIntro')}
          />
          <UiState
            kind={offline ? 'offline' : 'permission'}
            title={
              offline
                ? t('states.offline.title')
                : t('heartMomentProduct.editNotAllowedTitle')
            }
            body={
              offline
                ? t('states.offline.body')
                : t('heartMomentProduct.editNotAllowedBody')
            }
          />
        </div>
      );
    }

    function submitEdit(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      if (attachments.hasPending) return;
      const data = new FormData(event.currentTarget);
      const happenedOn = String(data.get('happenedOn') || '');
      const replacementAttachmentId = attachments.readyIds[0];
      const update: HeartMomentUpdate = {
        text: String(data.get('text') || '').trim(),
        emotion: String(data.get('emotion')) as HeartEmotionValue,
        happenedOn: new Date(`${happenedOn}T00:00:00Z`),
      };
      if (replacementAttachmentId)
        update.attachmentId = replacementAttachmentId;
      else if (removeExistingPhoto) update.attachmentId = null;

      updateMutation.mutate({ current: heartMoment, update });
    }

    return (
      <div className="page create-page product-editor-page">
        <PageHeader
          before={
            <Link
              className="back-link"
              to={heartMomentDetailPath(heartMoment.id)}
            >
              {t('heartMomentProduct.backToHeartMoment')}
            </Link>
          }
          eyebrow={t('heartMomentProduct.editEyebrow')}
          title={t('heartMomentProduct.editHeading')}
          description={t('heartMomentProduct.editIntro')}
        />
        <section
          className="form-card product-sheet"
          aria-labelledby="heart-moment-edit-heading"
        >
          <h2 id="heart-moment-edit-heading" className="sr-only">
            {t('heartMomentProduct.formAria')}
          </h2>
          <form className="form-grid" onSubmit={submitEdit}>
            <HeartMomentFields heartMoment={heartMoment} />
            {heartMoment.attachment && !removeExistingPhoto ? (
              <div className="field-group">
                <span>{t('heartMomentProduct.photoLabel')}</span>
                <MediaGallery
                  items={[
                    {
                      id: heartMoment.attachment.id,
                      mediaType: heartMoment.attachment.mediaType,
                    },
                  ]}
                  loadMedia={(attachmentId) =>
                    loadAttachment(heartMoment.id, attachmentId)
                  }
                />
                <button
                  type="button"
                  className="tertiary"
                  onClick={() => setRemoveExistingPhoto(true)}
                >
                  {t('memory.photoRemove')}
                </button>
              </div>
            ) : null}
            <AttachmentDraftPicker
              id="heart-moment-edit-photo"
              attachments={attachments}
              multiple={false}
            />
            <div className="form-actions">
              <Link
                className="button-link secondary-link"
                to={heartMomentDetailPath(heartMoment.id)}
              >
                {t('common.cancel')}
              </Link>
              <button
                type="submit"
                disabled={updateMutation.isPending || attachments.hasPending}
              >
                {updateMutation.isPending
                  ? t('heartMomentProduct.saving')
                  : t('heartMomentProduct.save')}
              </button>
            </div>
          </form>
          {updateMutation.error ? (
            <ProblemState error={updateMutation.error} />
          ) : null}
        </section>
      </div>
    );
  }

  const shared = heartMoment.visibility === ContentVisibility.SHARED;
  const changingVisibility = visibilityMutation.isPending;

  return (
    <div className="page product-detail-page">
      {offline ? (
        <div className="inline-message" role="status">
          {t('offlineCache.banner')}
        </div>
      ) : null}
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('story')}>
            {t('heartMomentProduct.backToStory')}
          </Link>
        }
        eyebrow={t('heartMomentProduct.detailEyebrow')}
        title={heartMoment.text}
        description={t(`heartEmotion.${heartMoment.emotion}`)}
        action={
          heartMoment.capabilities.canEdit && !offline ? (
            <Link
              className="button-link secondary-link"
              to={heartMomentEditPath(heartMoment.id)}
            >
              {t('heartMomentProduct.edit')}
            </Link>
          ) : undefined
        }
      />

      <article className="story-surface product-detail-card">
        <dl className="memory-meta-grid">
          <div>
            <dt>{t('heartMomentProduct.authorLabel')}</dt>
            <dd>{heartMoment.author.displayName}</dd>
          </div>
          <div>
            <dt>{t('heartMomentProduct.happenedOnLabel')}</dt>
            <dd>{formatDateOnly(heartMoment.happenedOn)}</dd>
          </div>
          <div>
            <dt>{t('heartMomentProduct.createdAtLabel')}</dt>
            <dd>{formatCreatedAt(heartMoment.createdAt)}</dd>
          </div>
          <div>
            <dt>{t('heartMomentProduct.visibilityLabel')}</dt>
            <dd>
              <span
                className={`visibility-badge ${
                  shared
                    ? 'visibility-badge-shared'
                    : 'visibility-badge-private'
                }`}
              >
                {shared
                  ? t('heartMomentProduct.visibilityShared')
                  : t('heartMomentProduct.visibilityPrivate')}
              </span>
            </dd>
          </div>
        </dl>

        {heartMoment.attachment ? (
          <section aria-label={t('heartMomentProduct.photoLabel')}>
            <MediaGallery
              items={[
                {
                  id: heartMoment.attachment.id,
                  mediaType: heartMoment.attachment.mediaType,
                },
              ]}
              loadMedia={(attachmentId) =>
                loadAttachment(heartMoment.id, attachmentId)
              }
            />
          </section>
        ) : (
          <p className="muted">{t('heartMomentProduct.noPhoto')}</p>
        )}

        {heartMoment.capabilities.canEdit && !offline ? (
          <section
            className="visibility-panel"
            aria-labelledby="visibility-change-heading"
          >
            <h2 id="visibility-change-heading">
              {t('heartMomentProduct.visibilityChangeHeading')}
            </h2>
            <p>{t('heartMomentProduct.visibilityChangeWarning')}</p>
            <button
              type="button"
              className="secondary"
              onClick={() =>
                visibilityMutation.mutate({
                  current: heartMoment,
                  visibility: shared
                    ? ContentVisibility.PRIVATE
                    : ContentVisibility.SHARED,
                })
              }
              disabled={changingVisibility}
            >
              {changingVisibility
                ? t('heartMomentProduct.visibilityChanging')
                : shared
                  ? t('heartMomentProduct.makePrivate')
                  : t('heartMomentProduct.makeShared')}
            </button>
            {visibilityMutation.error ? (
              <ProblemState error={visibilityMutation.error} />
            ) : null}
          </section>
        ) : null}

        {changingVisibility ? (
          <p className="muted" role="status">
            {t('heartMomentProduct.visibilityChanging')}
          </p>
        ) : shared ? (
          <CommentsPanel
            commentsApi={apis.comments}
            spaceId={spaceId}
            parentKind="heartMoment"
            parentId={heartMoment.id}
            currentAccountId={currentAccountId}
            canComment={heartMoment.capabilities.canComment}
            offline={offline}
          />
        ) : (
          <p className="muted">{t('heartMomentProduct.commentsPrivate')}</p>
        )}

        {heartMoment.capabilities.canDelete && !offline ? (
          <section
            className="memory-danger-zone"
            aria-label={t('heartMomentProduct.delete')}
          >
            {!confirmDelete ? (
              <button
                type="button"
                className="secondary"
                onClick={() => setConfirmDelete(true)}
              >
                {t('heartMomentProduct.delete')}
              </button>
            ) : (
              <div className="memory-delete-confirmation" role="alert">
                <div>
                  <h2>{t('heartMomentProduct.deleteConfirmTitle')}</h2>
                  <p>{t('heartMomentProduct.deleteConfirmBody')}</p>
                </div>
                <div className="memory-actions">
                  <button
                    type="button"
                    className="tertiary"
                    onClick={() => setConfirmDelete(false)}
                    disabled={deleteMutation.isPending}
                  >
                    {t('heartMomentProduct.deleteCancel')}
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteMutation.mutate(heartMoment)}
                    disabled={deleteMutation.isPending}
                  >
                    {deleteMutation.isPending
                      ? t('heartMomentProduct.deleting')
                      : t('heartMomentProduct.deleteConfirm')}
                  </button>
                </div>
              </div>
            )}
            {deleteMutation.error ? (
              <ProblemState error={deleteMutation.error} />
            ) : null}
          </section>
        ) : null}
      </article>
    </div>
  );
}

function HeartMomentFields({
  heartMoment,
}: {
  heartMoment?: HeartMomentDetail;
}) {
  const { t } = useTranslation();
  return (
    <>
      <div className="field-group">
        <label htmlFor="heart-moment-text">
          {t('heartMomentProduct.textLabel')}
        </label>
        <textarea
          id="heart-moment-text"
          name="text"
          rows={5}
          required
          maxLength={4000}
          defaultValue={heartMoment?.text ?? ''}
          placeholder={t('heartMomentProduct.textPlaceholder')}
        />
      </div>
      <div className="field-group">
        <label htmlFor="heart-moment-emotion">
          {t('heartMomentProduct.emotionLabel')}
        </label>
        <select
          id="heart-moment-emotion"
          name="emotion"
          defaultValue={heartMoment?.emotion ?? HeartEmotion.LOVED}
        >
          {Object.values(HeartEmotion).map((emotion) => (
            <option key={emotion} value={emotion}>
              {t(`heartEmotion.${emotion}`)}
            </option>
          ))}
        </select>
      </div>
      <div className="field-group">
        <label htmlFor="heart-moment-date">
          {t('heartMomentProduct.happenedOnLabel')}
        </label>
        <input
          id="heart-moment-date"
          name="happenedOn"
          type="date"
          required
          defaultValue={
            heartMoment ? dateInputValue(heartMoment.happenedOn) : undefined
          }
        />
      </div>
    </>
  );
}
