import { type FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { ContentVisibility } from '../api/generated/models/ContentVisibility';
import type { HeartEmotion } from '../api/generated/models/HeartEmotion';
import type { HeartMomentDetail } from '../api/generated/models/HeartMomentDetail';
import { deleteUnboundAttachment } from '../client/memoryAttachmentDraft';
import { normalizeClientError } from '../client/problemDetails';
import type { ReferenceApis } from '../client/referenceFlow';
import {
  appRoutePath,
  heartMomentDetailPath,
} from '../client/routes';
import { useAttachmentDrafts } from '../client/useAttachmentDrafts';
import { useTranslation } from '../i18n';
import { HeartMomentDetailView } from './HeartMomentDetailView';
import { HeartMomentForm } from './HeartMomentForm';
import { MemoryPreview } from './MemoryPreview';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

export type HeartMomentProductMode = 'create' | 'detail' | 'edit';

export function HeartMomentProductPage({
  mode,
  apis,
  apiBaseUrl,
  accessToken,
  spaceId,
  currentAccountId,
  loadHeartMomentImage,
}: {
  mode: HeartMomentProductMode;
  apis: ReferenceApis;
  apiBaseUrl: string;
  accessToken: string;
  spaceId: string;
  currentAccountId: string;
  loadHeartMomentImage: (
    heartMomentId: string,
    attachmentId: string,
  ) => Promise<string>;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const params = useParams();
  const queryClient = useQueryClient();
  const heartMomentId = params.heartMomentId;
  const detailKey = ['heart-moment', spaceId, heartMomentId] as const;
  const [removeExistingAttachment, setRemoveExistingAttachment] =
    useState(false);
  const attachments = useAttachmentDrafts({
    apis,
    apiBaseUrl,
    accessToken,
    spaceId,
  });

  const detailQuery = useQuery({
    queryKey: detailKey,
    queryFn: async () => {
      if (!heartMomentId) throw new Error('Missing HeartMoment route parameter.');
      try {
        return await apis.heartMoments.getHeartMoment({
          spaceId,
          heartMomentId,
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    enabled: mode !== 'create' && Boolean(heartMomentId),
    retry: false,
  });

  async function invalidateProductQueries() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['story', spaceId] }),
      queryClient.invalidateQueries({ queryKey: ['heart-moments', spaceId] }),
    ]);
  }

  const createMutation = useMutation({
    mutationFn: async ({
      text,
      emotion,
      happenedOn,
      visibility,
    }: {
      text: string;
      emotion: HeartEmotion;
      happenedOn: Date;
      visibility: ContentVisibility;
    }) => {
      try {
        return await apis.heartMoments.createHeartMoment({
          spaceId,
          heartMomentCreate: {
            text,
            emotion,
            happenedOn,
            visibility,
            attachmentId: attachments.readyIds[0] ?? null,
          },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (heartMoment) => {
      attachments.clear();
      await invalidateProductQueries();
      navigate(heartMomentDetailPath(heartMoment.id), { replace: true });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      heartMoment,
      text,
      emotion,
      happenedOn,
    }: {
      heartMoment: HeartMomentDetail;
      text: string;
      emotion: HeartEmotion;
      happenedOn: Date;
    }) => {
      const newAttachmentId = attachments.readyIds[0];
      try {
        return await apis.heartMoments.updateHeartMoment({
          spaceId,
          heartMomentId: heartMoment.id,
          ifMatch: String(heartMoment.version),
          heartMomentUpdate: {
            text,
            emotion,
            happenedOn,
            ...(newAttachmentId
              ? { attachmentId: newAttachmentId }
              : removeExistingAttachment
                ? { attachmentId: null }
                : {}),
          },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (heartMoment) => {
      const previousAttachmentId = detailQuery.data?.attachment?.id;
      const currentAttachmentId = heartMoment.attachment?.id;
      attachments.clear();
      queryClient.setQueryData(detailKey, heartMoment);
      if (
        previousAttachmentId &&
        previousAttachmentId !== currentAttachmentId
      ) {
        void deleteUnboundAttachment(apis, spaceId, previousAttachmentId);
      }
      setRemoveExistingAttachment(false);
      await invalidateProductQueries();
      navigate(heartMomentDetailPath(heartMoment.id), { replace: true });
    },
  });

  const visibilityMutation = useMutation({
    mutationFn: async (visibility: ContentVisibility) => {
      const heartMoment = detailQuery.data;
      if (!heartMoment) throw new Error('HeartMoment is not loaded.');
      try {
        return await apis.heartMoments.changeHeartMomentVisibility({
          spaceId,
          heartMomentId: heartMoment.id,
          ifMatch: String(heartMoment.version),
          heartMomentVisibilityChange: { visibility },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (heartMoment) => {
      queryClient.setQueryData(detailKey, heartMoment);
      await invalidateProductQueries();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      const heartMoment = detailQuery.data;
      if (!heartMoment) throw new Error('HeartMoment is not loaded.');
      try {
        await apis.heartMoments.deleteHeartMoment({
          spaceId,
          heartMomentId: heartMoment.id,
          ifMatch: String(heartMoment.version),
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: detailKey });
      await invalidateProductQueries();
      navigate(appRoutePath('heartMoments'), { replace: true });
    },
  });

  if (mode === 'create') {
    function submit(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      if (attachments.hasPending) return;
      const data = new FormData(event.currentTarget);
      createMutation.mutate({
        text: String(data.get('text') || '').trim(),
        emotion: String(data.get('emotion')) as HeartEmotion,
        happenedOn: new Date(`${String(data.get('happenedOn'))}T00:00:00Z`),
        visibility: String(data.get('visibility')) as ContentVisibility,
      });
    }

    return (
      <div className="page create-page">
        <PageHeader
          before={
            <Link className="back-link" to={appRoutePath('heartMoments')}>
              {t('m5Product.heart.backToList')}
            </Link>
          }
          eyebrow={t('m5Product.heart.createEyebrow')}
          title={t('m5Product.heart.createTitle')}
          description={t('m5Product.heart.createIntro')}
        />
        <section className="form-card">
          <HeartMomentForm
            submitLabel={t('m5Product.heart.save')}
            submitting={createMutation.isPending}
            attachments={attachments}
            onSubmit={submit}
          />
          {createMutation.error ? <ProblemState error={createMutation.error} /> : null}
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
  if (detailQuery.isLoading) {
    return <UiState kind="loading" title={t('m5Product.heart.loading')} />;
  }
  if (detailQuery.error) {
    return (
      <ProblemState
        error={detailQuery.error}
        onRetry={() => void detailQuery.refetch()}
      />
    );
  }
  const heartMoment = detailQuery.data;
  if (!heartMoment) return null;

  if (mode === 'edit') {
    if (!heartMoment.capabilities.canEdit) {
      return (
        <UiState
          kind="permission"
          title={t('m5Product.heart.editDeniedTitle')}
          body={t('m5Product.heart.editDeniedBody')}
        />
      );
    }

    const editableHeartMoment = heartMoment;
    function submit(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      if (attachments.hasPending) return;
      const data = new FormData(event.currentTarget);
      updateMutation.mutate({
        heartMoment: editableHeartMoment,
        text: String(data.get('text') || '').trim(),
        emotion: String(data.get('emotion')) as HeartEmotion,
        happenedOn: new Date(`${String(data.get('happenedOn'))}T00:00:00Z`),
      });
    }

    return (
      <div className="page create-page">
        <PageHeader
          before={
            <Link className="back-link" to={heartMomentDetailPath(heartMoment.id)}>
              {t('m5Product.heart.backToDetail')}
            </Link>
          }
          eyebrow={t('m5Product.heart.editEyebrow')}
          title={t('m5Product.heart.editTitle')}
          description={t('m5Product.heart.editIntro')}
        />
        <section className="form-card">
          {heartMoment.attachment && !removeExistingAttachment ? (
            <div className="existing-attachment">
              <MemoryPreview
                memoryId={heartMoment.id}
                attachmentId={heartMoment.attachment.id}
                loadImage={loadHeartMomentImage}
              />
              <button
                type="button"
                className="tertiary"
                onClick={() => setRemoveExistingAttachment(true)}
              >
                {t('m5Product.heart.removePhoto')}
              </button>
            </div>
          ) : null}
          <HeartMomentForm
            key={heartMoment.version}
            initial={heartMoment}
            submitLabel={t('m5Product.heart.saveChanges')}
            submitting={updateMutation.isPending}
            attachments={attachments}
            onSubmit={submit}
          />
          {updateMutation.error ? (
            <ProblemState
              error={updateMutation.error}
              onRetry={() => void detailQuery.refetch()}
            />
          ) : null}
        </section>
      </div>
    );
  }

  return (
    <HeartMomentDetailView
      heartMoment={heartMoment}
      apis={apis}
      spaceId={spaceId}
      currentAccountId={currentAccountId}
      loadHeartMomentImage={loadHeartMomentImage}
      visibilityPending={visibilityMutation.isPending}
      visibilityError={visibilityMutation.error}
      onVisibilityChange={(visibility) => visibilityMutation.mutate(visibility)}
      deletePending={deleteMutation.isPending}
      deleteError={deleteMutation.error}
      onDelete={() => deleteMutation.mutate()}
      onRetry={() => void detailQuery.refetch()}
    />
  );
}
