import { type FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { MilestoneDetail } from '../api/generated/models/MilestoneDetail';
import {
  MilestoneDetailFromJSON,
  MilestoneDetailToJSON,
} from '../api/generated/models/MilestoneDetail';
import type { MilestoneUpdate } from '../api/generated/models/MilestoneUpdate';
import {
  deleteProductReadCacheEntry,
  loadProductWithReadCache,
} from '../client/productReadCache';
import { normalizeClientError } from '../client/problemDetails';
import type { ReferenceApis } from '../client/referenceFlow';
import {
  appRoutePath,
  milestoneDetailPath,
  milestoneEditPath,
} from '../client/routes';
import { invalidateDashboard } from '../client/dashboardQueries';
import { authorSummaryQueryKeys } from '../client/authorSummaryConsumers';
import { resolvedLocale, useTranslation } from '../i18n';
import { CommentsPanel } from './CommentsPanel';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

export type MilestoneProductMode = 'create' | 'detail' | 'edit';

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

export function MilestoneProductPage({
  mode,
  apis,
  spaceId,
  currentAccountId,
}: {
  mode: MilestoneProductMode;
  apis: ReferenceApis;
  spaceId: string;
  currentAccountId: string;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const params = useParams();
  const queryClient = useQueryClient();
  const milestoneId = params.milestoneId;
  const queryKey = authorSummaryQueryKeys.milestone(spaceId, milestoneId);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const milestoneQuery = useQuery({
    queryKey,
    queryFn: async () => {
      if (!milestoneId) throw new Error('Missing Milestone route parameter.');
      return loadProductWithReadCache({
        accountId: currentAccountId,
        spaceId,
        kind: 'milestone',
        resourceId: milestoneId,
        load: () => apis.milestones.getMilestone({ spaceId, milestoneId }),
        serialize: MilestoneDetailToJSON,
        deserialize: (payload) => MilestoneDetailFromJSON(payload),
      });
    },
    enabled: mode !== 'create' && Boolean(milestoneId),
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: async (values: {
      title: string;
      body?: string;
      happenedOn: Date;
    }) => {
      try {
        return await apis.milestones.createMilestone({
          spaceId,
          milestoneCreate: values,
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (milestone) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['story', spaceId] }),
        invalidateDashboard(queryClient, spaceId),
      ]);
      navigate(milestoneDetailPath(milestone.id), {
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
      current: MilestoneDetail;
      update: MilestoneUpdate;
    }) => {
      try {
        return await apis.milestones.updateMilestone({
          spaceId,
          milestoneId: current.id,
          ifMatch: String(current.version),
          milestoneUpdate: update,
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
          title: update.title ?? current.title,
          body: update.body === undefined ? current.body : update.body,
          happenedOn: update.happenedOn ?? current.happenedOn,
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
    onSuccess: async (milestone) => {
      queryClient.setQueryData(queryKey, {
        value: milestone,
        source: 'network',
      });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['story', spaceId] }),
        queryClient.invalidateQueries({ queryKey }),
        invalidateDashboard(queryClient, spaceId),
      ]);
      navigate(milestoneDetailPath(milestone.id), { replace: true });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (milestone: MilestoneDetail) => {
      try {
        await apis.milestones.deleteMilestone({
          spaceId,
          milestoneId: milestone.id,
          ifMatch: String(milestone.version),
        });
        await deleteProductReadCacheEntry(
          currentAccountId,
          spaceId,
          'milestone',
          milestone.id,
        );
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['story', spaceId] }),
        invalidateDashboard(queryClient, spaceId),
      ]);
      navigate(appRoutePath('story'), { replace: true });
    },
  });

  if (mode === 'create') {
    function submitCreate(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const happenedOn = String(data.get('happenedOn') || '');
      if (!happenedOn) return;
      const body = String(data.get('body') || '').trim();
      createMutation.mutate({
        title: String(data.get('title') || '').trim(),
        body: body || undefined,
        happenedOn: new Date(`${happenedOn}T00:00:00Z`),
      });
    }

    return (
      <div className="page page-reading create-page product-editor-page">
        <PageHeader
          before={
            <Link className="back-link" to={appRoutePath('story')}>
              {t('milestoneProduct.backToStory')}
            </Link>
          }
          eyebrow={t('milestoneProduct.createEyebrow')}
          title={t('milestoneProduct.createHeading')}
          description={t('milestoneProduct.createIntro')}
        />
        <section
          className="form-card product-sheet"
          aria-labelledby="milestone-create-heading"
        >
          <h2 id="milestone-create-heading" className="sr-only">
            {t('milestoneProduct.createHeading')}
          </h2>
          <form className="form-grid" onSubmit={submitCreate}>
            <MilestoneFields />
            <div className="form-actions">
              <Link
                className="button-link secondary-link"
                to={appRoutePath('story')}
              >
                {t('common.cancel')}
              </Link>
              <button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending
                  ? t('milestoneProduct.saving')
                  : t('milestoneProduct.save')}
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

  if (!milestoneId) {
    return (
      <UiState
        kind="error"
        title={t('states.unknown.title')}
        body={t('states.unknown.body')}
      />
    );
  }
  if (milestoneQuery.isLoading) {
    return <UiState kind="loading" title={t('milestoneProduct.loading')} />;
  }
  if (milestoneQuery.error) {
    return (
      <ProblemState
        error={milestoneQuery.error}
        onRetry={() => void milestoneQuery.refetch()}
      />
    );
  }
  const result = milestoneQuery.data;
  if (!result) return null;
  const milestone = result.value;
  const offline = result.source === 'cache';

  if (mode === 'edit') {
    if (!milestone.capabilities.canEdit || offline) {
      return (
        <div className="page page-reading">
          <PageHeader
            before={
              <Link
                className="back-link"
                to={milestoneDetailPath(milestone.id)}
              >
                {t('milestoneProduct.backToMilestone')}
              </Link>
            }
            eyebrow={t('milestoneProduct.editEyebrow')}
            title={t('milestoneProduct.editHeading')}
            description={t('milestoneProduct.editIntro')}
          />
          <UiState
            kind={offline ? 'offline' : 'permission'}
            title={
              offline
                ? t('states.offline.title')
                : t('milestoneProduct.editNotAllowedTitle')
            }
            body={
              offline
                ? t('states.offline.body')
                : t('milestoneProduct.editNotAllowedBody')
            }
          />
        </div>
      );
    }

    function submitEdit(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const happenedOn = String(data.get('happenedOn') || '');
      const body = String(data.get('body') || '').trim();
      updateMutation.mutate({
        current: milestone,
        update: {
          title: String(data.get('title') || '').trim(),
          body: body || null,
          happenedOn: new Date(`${happenedOn}T00:00:00Z`),
        },
      });
    }

    return (
      <div className="page page-reading create-page product-editor-page">
        <PageHeader
          before={
            <Link className="back-link" to={milestoneDetailPath(milestone.id)}>
              {t('milestoneProduct.backToMilestone')}
            </Link>
          }
          eyebrow={t('milestoneProduct.editEyebrow')}
          title={t('milestoneProduct.editHeading')}
          description={t('milestoneProduct.editIntro')}
        />
        <section
          className="form-card product-sheet"
          aria-labelledby="milestone-edit-heading"
        >
          <h2 id="milestone-edit-heading" className="sr-only">
            {t('milestoneProduct.formAria')}
          </h2>
          <form className="form-grid" onSubmit={submitEdit}>
            <MilestoneFields milestone={milestone} />
            <div className="form-actions">
              <Link
                className="button-link secondary-link"
                to={milestoneDetailPath(milestone.id)}
                onClick={() => setConfirmDelete(false)}
              >
                {t('common.cancel')}
              </Link>
              <button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending
                  ? t('milestoneProduct.saving')
                  : t('milestoneProduct.save')}
              </button>
            </div>
          </form>
          {updateMutation.error ? (
            <ProblemState error={updateMutation.error} />
          ) : null}

          {milestone.capabilities.canDelete && !offline ? (
            <div
              className="memory-danger-zone"
              aria-label={t('milestoneProduct.delete')}
              style={{ marginTop: 'var(--space-8)' }}
            >
              {!confirmDelete ? (
                <button
                  type="button"
                  className="secondary"
                  onClick={() => setConfirmDelete(true)}
                >
                  {t('milestoneProduct.delete')}
                </button>
              ) : (
                <div className="memory-delete-confirmation" role="alert">
                  <div>
                    <h2>{t('milestoneProduct.deleteConfirmTitle')}</h2>
                    <p>{t('milestoneProduct.deleteConfirmBody')}</p>
                  </div>
                  <div className="memory-actions">
                    <button
                      type="button"
                      className="tertiary"
                      onClick={() => setConfirmDelete(false)}
                      disabled={deleteMutation.isPending}
                    >
                      {t('milestoneProduct.deleteCancel')}
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteMutation.mutate(milestone)}
                      disabled={deleteMutation.isPending}
                    >
                      {deleteMutation.isPending
                        ? t('milestoneProduct.deleting')
                        : t('milestoneProduct.deleteConfirm')}
                    </button>
                  </div>
                </div>
              )}
              {deleteMutation.error ? (
                <ProblemState error={deleteMutation.error} />
              ) : null}
            </div>
          ) : null}
        </section>
      </div>
    );
  }

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
            {t('milestoneProduct.backToStory')}
          </Link>
        }
        eyebrow={t('milestoneProduct.detailEyebrow')}
        title={milestone.title}
        description={formatDateOnly(milestone.happenedOn)}
        action={
          milestone.capabilities.canEdit && !offline ? (
            <Link
              className="button-link secondary-link"
              to={milestoneEditPath(milestone.id)}
            >
              {t('milestoneProduct.edit')}
            </Link>
          ) : undefined
        }
      />

      <div className="layout-split layout-split-lead-rail">
        <aside
          className="layout-rail layout-rail-sticky"
          aria-label={t('milestoneProduct.detailMetaAria')}
        >
          <div className="layout-panel">
            <dl className="detail-meta-list">
              <div>
                <dt>{t('milestoneProduct.authorLabel')}</dt>
                <dd>{milestone.author.displayName}</dd>
              </div>
              <div>
                <dt>{t('milestoneProduct.happenedOnLabel')}</dt>
                <dd>{formatDateOnly(milestone.happenedOn)}</dd>
              </div>
              <div>
                <dt>{t('milestoneProduct.createdAtLabel')}</dt>
                <dd>{formatCreatedAt(milestone.createdAt)}</dd>
              </div>
            </dl>
          </div>
        </aside>

        <div className="layout-main">
          <article className="story-surface product-detail-card">
            <p className="memory-detail-body">
              {milestone.body || t('milestoneProduct.noBody')}
            </p>

            <CommentsPanel
              commentsApi={apis.comments}
              spaceId={spaceId}
              parentKind="milestone"
              parentId={milestone.id}
              currentAccountId={currentAccountId}
              canComment={milestone.capabilities.canComment}
              offline={offline}
            />


          </article>
        </div>
      </div>
    </div>
  );
}

function MilestoneFields({ milestone }: { milestone?: MilestoneDetail }) {
  const { t } = useTranslation();
  return (
    <>
      <div className="field-group">
        <label htmlFor="milestone-title">
          {t('milestoneProduct.titleLabel')}
        </label>
        <input
          id="milestone-title"
          name="title"
          required
          maxLength={200}
          defaultValue={milestone?.title}
          placeholder={t('milestoneProduct.titlePlaceholder')}
        />
      </div>
      <div className="field-group">
        <label htmlFor="milestone-body">
          {t('milestoneProduct.bodyLabel')}
        </label>
        <textarea
          id="milestone-body"
          name="body"
          rows={5}
          defaultValue={milestone?.body ?? ''}
          placeholder={t('milestoneProduct.bodyPlaceholder')}
        />
      </div>
      <div className="field-group">
        <label htmlFor="milestone-date">
          {t('milestoneProduct.happenedOnLabel')}
        </label>
        <input
          id="milestone-date"
          name="happenedOn"
          type="date"
          required
          defaultValue={
            milestone ? dateInputValue(milestone.happenedOn) : undefined
          }
        />
      </div>
    </>
  );
}
