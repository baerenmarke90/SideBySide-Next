import { type FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { MilestoneDetail } from '../api/generated/models/MilestoneDetail';
import { memoryDateInputValue } from '../client/memoryProduct';
import { normalizeClientError } from '../client/problemDetails';
import type { ReferenceApis } from '../client/referenceFlow';
import {
  appRoutePath,
  milestoneDetailPath,
  milestoneEditPath,
} from '../client/routes';
import { resolvedLocale, useTranslation } from '../i18n';
import { CommentsSection } from './CommentsSection';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

export type MilestoneProductMode = 'create' | 'detail' | 'edit';

function formatDate(value: Date): string {
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'long',
    timeZone: 'UTC',
  }).format(value);
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
  const detailKey = ['milestone', spaceId, milestoneId] as const;
  const [confirmDelete, setConfirmDelete] = useState(false);

  const detailQuery = useQuery({
    queryKey: detailKey,
    queryFn: async () => {
      if (!milestoneId) throw new Error('Missing Milestone route parameter.');
      try {
        return await apis.milestones.getMilestone({ spaceId, milestoneId });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    enabled: mode !== 'create' && Boolean(milestoneId),
    retry: false,
  });

  async function invalidateStory() {
    await queryClient.invalidateQueries({ queryKey: ['story', spaceId] });
  }

  const createMutation = useMutation({
    mutationFn: async ({
      title,
      body,
      happenedOn,
    }: {
      title: string;
      body: string;
      happenedOn: Date;
    }) => {
      try {
        return await apis.milestones.createMilestone({
          spaceId,
          milestoneCreate: { title, body: body || undefined, happenedOn },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (milestone) => {
      await invalidateStory();
      navigate(milestoneDetailPath(milestone.id), { replace: true });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      milestone,
      title,
      body,
      happenedOn,
    }: {
      milestone: MilestoneDetail;
      title: string;
      body: string;
      happenedOn: Date;
    }) => {
      try {
        return await apis.milestones.updateMilestone({
          spaceId,
          milestoneId: milestone.id,
          ifMatch: String(milestone.version),
          milestoneUpdate: { title, body: body || null, happenedOn },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async (milestone) => {
      queryClient.setQueryData(detailKey, milestone);
      await invalidateStory();
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
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: detailKey });
      await invalidateStory();
      navigate(appRoutePath('story'), { replace: true });
    },
  });

  if (mode === 'create') {
    function submit(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      createMutation.mutate({
        title: String(data.get('title') || '').trim(),
        body: String(data.get('body') || '').trim(),
        happenedOn: new Date(`${String(data.get('happenedOn'))}T00:00:00Z`),
      });
    }
    return (
      <MilestoneFormPage
        title={t('m5Product.milestone.createTitle')}
        intro={t('m5Product.milestone.createIntro')}
        submitLabel={t('m5Product.milestone.save')}
        submitting={createMutation.isPending}
        error={createMutation.error}
        onSubmit={submit}
      />
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
  if (detailQuery.isLoading) {
    return <UiState kind="loading" title={t('m5Product.milestone.loading')} />;
  }
  if (detailQuery.error) {
    return (
      <ProblemState
        error={detailQuery.error}
        onRetry={() => void detailQuery.refetch()}
      />
    );
  }
  const milestone = detailQuery.data;
  if (!milestone) return null;

  if (mode === 'edit') {
    if (!milestone.capabilities.canEdit) {
      return (
        <UiState
          kind="permission"
          title={t('m5Product.milestone.editDeniedTitle')}
          body={t('m5Product.milestone.editDeniedBody')}
        />
      );
    }
    function submit(event: FormEvent<HTMLFormElement>) {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      updateMutation.mutate({
        milestone,
        title: String(data.get('title') || '').trim(),
        body: String(data.get('body') || '').trim(),
        happenedOn: new Date(`${String(data.get('happenedOn'))}T00:00:00Z`),
      });
    }
    return (
      <MilestoneFormPage
        title={t('m5Product.milestone.editTitle')}
        intro={t('m5Product.milestone.editIntro')}
        submitLabel={t('m5Product.milestone.saveChanges')}
        submitting={updateMutation.isPending}
        error={updateMutation.error}
        initial={milestone}
        onSubmit={submit}
      />
    );
  }

  return (
    <div className="page m5-product-page">
      <PageHeader
        before={
          <Link className="back-link" to={appRoutePath('story')}>
            {t('m5Product.milestone.backToStory')}
          </Link>
        }
        eyebrow={t('m5Product.milestone.detailEyebrow')}
        title={milestone.title}
        description={t('m5Product.milestone.detailIntro')}
        action={
          milestone.capabilities.canEdit ? (
            <Link
              className="button-link secondary-link"
              to={milestoneEditPath(milestone.id)}
            >
              {t('m5Product.milestone.edit')}
            </Link>
          ) : undefined
        }
      />

      <article className="story-surface memory-detail-card">
        <dl className="memory-meta-grid">
          <div>
            <dt>{t('m5Product.milestone.dateLabel')}</dt>
            <dd>{formatDate(milestone.happenedOn)}</dd>
          </div>
          <div>
            <dt>{t('m5Product.milestone.authorLabel')}</dt>
            <dd>{milestone.author.displayName}</dd>
          </div>
        </dl>
        <p className="memory-detail-body">
          {milestone.body || t('m5Product.milestone.noBody')}
        </p>

        <CommentsSection
          apis={apis}
          spaceId={spaceId}
          parentKind="MILESTONE"
          parentId={milestone.id}
          canComment={milestone.capabilities.canComment}
          currentAccountId={currentAccountId}
        />

        {milestone.capabilities.canDelete ? (
          <section className="memory-danger-zone">
            {!confirmDelete ? (
              <button
                type="button"
                className="secondary"
                onClick={() => setConfirmDelete(true)}
              >
                {t('m5Product.milestone.delete')}
              </button>
            ) : (
              <div className="memory-delete-confirmation" role="alert">
                <p>{t('m5Product.milestone.deleteWarning')}</p>
                <div className="memory-actions">
                  <button
                    type="button"
                    className="tertiary"
                    onClick={() => setConfirmDelete(false)}
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    type="button"
                    disabled={deleteMutation.isPending}
                    onClick={() => deleteMutation.mutate(milestone)}
                  >
                    {t('m5Product.milestone.confirmDelete')}
                  </button>
                </div>
              </div>
            )}
            {deleteMutation.error ? (
              <ProblemState
                error={deleteMutation.error}
                onRetry={() => void detailQuery.refetch()}
              />
            ) : null}
          </section>
        ) : null}
      </article>
    </div>
  );
}

function MilestoneFormPage({
  title,
  intro,
  submitLabel,
  submitting,
  error,
  initial,
  onSubmit,
}: {
  title: string;
  intro: string;
  submitLabel: string;
  submitting: boolean;
  error: unknown;
  initial?: MilestoneDetail;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="page create-page">
      <PageHeader
        before={
          <Link
            className="back-link"
            to={initial ? milestoneDetailPath(initial.id) : appRoutePath('story')}
          >
            {initial
              ? t('m5Product.milestone.backToDetail')
              : t('m5Product.milestone.backToStory')}
          </Link>
        }
        eyebrow={t('m5Product.milestone.formEyebrow')}
        title={title}
        description={intro}
      />
      <section className="form-card">
        <form className="form-grid" onSubmit={onSubmit}>
          <div className="field-group">
            <label htmlFor="milestone-title">
              {t('m5Product.milestone.titleLabel')}
            </label>
            <input
              id="milestone-title"
              name="title"
              required
              maxLength={200}
              defaultValue={initial?.title ?? ''}
            />
          </div>
          <div className="field-group">
            <label htmlFor="milestone-body">
              {t('m5Product.milestone.bodyLabel')}
            </label>
            <textarea
              id="milestone-body"
              name="body"
              rows={5}
              defaultValue={initial?.body ?? ''}
            />
          </div>
          <div className="field-group">
            <label htmlFor="milestone-date">
              {t('m5Product.milestone.dateLabel')}
            </label>
            <input
              id="milestone-date"
              name="happenedOn"
              type="date"
              required
              defaultValue={
                initial ? memoryDateInputValue(initial.happenedOn) : undefined
              }
            />
          </div>
          <button type="submit" disabled={submitting}>
            {submitting ? t('m5Product.common.saving') : submitLabel}
          </button>
        </form>
        {error ? <ProblemState error={error} /> : null}
      </section>
    </div>
  );
}
