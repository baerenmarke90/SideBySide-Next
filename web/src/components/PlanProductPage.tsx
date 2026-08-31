import { type FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { PlanDetail } from '../api/generated/models/PlanDetail';
import { normalizeClientError } from '../client/problemDetails';
import {
  dateFromInput,
  dateOnlyInput,
  dateTimeFromInput,
  localDateTimeInput,
  planningIfMatch,
  type SharedPlanningApis,
} from '../client/sharedPlanning';
import { appRoutePath } from '../client/routes';
import { resolvedLocale, useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
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

function formatDateTime(value: Date | null): string | null {
  if (!value) return null;
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(value);
}

export function PlanProductPage({
  apis,
  spaceId,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const { planId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const key = ['m5-s3', 'plan', spaceId, planId] as const;

  const planQuery = useQuery({
    queryKey: key,
    queryFn: () => {
      if (!planId) throw new Error('Missing Plan route parameter.');
      return apiCall(() => apis.plans.getPlan({ spaceId, planId }));
    },
    enabled: Boolean(planId),
    retry: false,
  });
  const placesQuery = useQuery({
    queryKey: ['m5-s3', 'plan-places', spaceId],
    queryFn: () => apiCall(() => apis.places.listPlaces({ spaceId, limit: 50 })),
    staleTime: 30_000,
    retry: false,
  });

  const commitPlan = async (plan: PlanDetail) => {
    queryClient.setQueryData(key, plan);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['m5-s3', 'plans', spaceId] }),
      queryClient.invalidateQueries({ queryKey: key }),
    ]);
  };

  const updateMutation = useMutation({
    mutationFn: ({
      plan,
      title,
      description,
      placeId,
      experiencedOn,
    }: {
      plan: PlanDetail;
      title: string;
      description: string | null;
      placeId: string | null;
      experiencedOn?: Date;
    }) =>
      apiCall(() =>
        apis.plans.updatePlan({
          spaceId,
          planId: plan.id,
          ifMatch: planningIfMatch(plan),
          planUpdate: { title, description, placeId, experiencedOn },
        }),
      ),
    onSuccess: commitPlan,
  });

  const scheduleMutation = useMutation({
    mutationFn: ({ plan, start, end }: { plan: PlanDetail; start: Date; end?: Date }) =>
      apiCall(() =>
        apis.plans.schedulePlan({
          spaceId,
          planId: plan.id,
          ifMatch: planningIfMatch(plan),
          planSchedule: { plannedStart: start, plannedEnd: end },
        }),
      ),
    onSuccess: commitPlan,
  });
  const unscheduleMutation = useMutation({
    mutationFn: (plan: PlanDetail) =>
      apiCall(() =>
        apis.plans.unschedulePlan({
          spaceId,
          planId: plan.id,
          ifMatch: planningIfMatch(plan),
        }),
      ),
    onSuccess: commitPlan,
  });
  const completeMutation = useMutation({
    mutationFn: ({ plan, experiencedOn }: { plan: PlanDetail; experiencedOn: Date }) =>
      apiCall(() =>
        apis.plans.completePlan({
          spaceId,
          planId: plan.id,
          ifMatch: planningIfMatch(plan),
          planComplete: { experiencedOn },
        }),
      ),
    onSuccess: commitPlan,
  });
  const returnMutation = useMutation({
    mutationFn: (plan: PlanDetail) =>
      apiCall(() =>
        apis.plans.returnPlanToWish({
          spaceId,
          planId: plan.id,
          ifMatch: planningIfMatch(plan),
        }),
      ),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['m5-s3', 'plans', spaceId] }),
        queryClient.invalidateQueries({ queryKey: ['m5-s3', 'wishes', spaceId] }),
      ]);
      navigate(appRoutePath('planning'), { replace: true });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: (plan: PlanDetail) =>
      apiCall(() =>
        apis.plans.deletePlan({
          spaceId,
          planId: plan.id,
          ifMatch: planningIfMatch(plan),
        }),
      ),
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: key });
      await queryClient.invalidateQueries({ queryKey: ['m5-s3', 'plans', spaceId] });
      navigate(appRoutePath('planning'), { replace: true });
    },
  });

  if (!planId) return <UiState kind="error" title={t('states.unknown.title')} body={t('states.unknown.body')} />;
  if (planQuery.isLoading) return <UiState kind="loading" title={t('m5s3.plan.loading')} />;
  if (planQuery.error) return <ProblemState error={planQuery.error} onRetry={() => void planQuery.refetch()} />;
  const plan = planQuery.data;
  if (!plan) return null;

  function submitEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const description = String(data.get('description')).trim();
    const placeId = String(data.get('placeId')).trim();
    const experiencedOn = String(data.get('experiencedOn')).trim();
    updateMutation.mutate({
      plan,
      title: String(data.get('title')).trim(),
      description: description || null,
      placeId: placeId || null,
      experiencedOn: experiencedOn ? dateFromInput(experiencedOn) : undefined,
    });
  }

  function submitSchedule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const start = dateTimeFromInput(String(data.get('plannedStart')));
    const end = dateTimeFromInput(String(data.get('plannedEnd')));
    if (!start) return;
    scheduleMutation.mutate({ plan, start, end });
  }

  function submitComplete(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const experiencedOn = dateFromInput(String(data.get('experiencedOn')));
    if (!experiencedOn) return;
    completeMutation.mutate({ plan, experiencedOn });
  }

  const lifecycleError =
    scheduleMutation.error ||
    unscheduleMutation.error ||
    completeMutation.error ||
    returnMutation.error;

  return (
    <div className="page planning-page">
      <PageHeader
        before={<Link className="back-link" to={appRoutePath('planning')}>{t('m5s3.common.back')}</Link>}
        eyebrow={t('m5s3.plan.detailEyebrow')}
        title={plan.title}
        description={t(`m5s3.plan.status.${plan.status}`)}
      />

      <section className="planning-facts" aria-label={t('m5s3.plan.scheduleFacts')}>
        {plan.plannedStart ? <p><strong>{t('m5s3.plan.plannedStart')}:</strong> {formatDateTime(plan.plannedStart)}</p> : null}
        {plan.plannedEnd ? <p><strong>{t('m5s3.plan.plannedEnd')}:</strong> {formatDateTime(plan.plannedEnd)}</p> : null}
        {plan.experiencedOn ? <p><strong>{t('m5s3.plan.experiencedOn')}:</strong> {dateOnlyInput(plan.experiencedOn)}</p> : null}
      </section>

      <div className="planning-detail-grid">
        <section className="planning-subsection">
          <h2>{t('m5s3.common.edit')}</h2>
          {plan.capabilities.canEdit ? (
            <form className="form-grid" onSubmit={submitEdit}>
              <label htmlFor="plan-edit-title">{t('m5s3.common.title')}</label>
              <input id="plan-edit-title" name="title" required maxLength={200} defaultValue={plan.title} />
              <label htmlFor="plan-edit-description">{t('m5s3.common.description')}</label>
              <textarea id="plan-edit-description" name="description" rows={4} defaultValue={plan.description ?? ''} />
              <label htmlFor="plan-edit-place">{t('m5s3.common.place')}</label>
              <select id="plan-edit-place" name="placeId" defaultValue={plan.placeId ?? ''}>
                <option value="">{t('m5s3.common.noPlace')}</option>
                {placesQuery.data?.items.map((place) => <option key={place.id} value={place.id}>{place.name}</option>)}
              </select>
              {plan.status === 'COMPLETED' ? (
                <>
                  <label htmlFor="plan-edit-experienced">{t('m5s3.plan.experiencedOn')}</label>
                  <input id="plan-edit-experienced" name="experiencedOn" type="date" defaultValue={dateOnlyInput(plan.experiencedOn)} />
                </>
              ) : null}
              <button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? t('m5s3.common.saving') : t('m5s3.common.saveChanges')}
              </button>
              {updateMutation.error ? <ProblemState error={updateMutation.error} onRetry={() => void planQuery.refetch()} /> : null}
            </form>
          ) : <p className="planning-meta">{t('m5s3.common.readOnly')}</p>}
        </section>

        {plan.capabilities.canEdit && plan.status !== 'COMPLETED' ? (
          <section className="planning-subsection">
            <h2>{t('m5s3.plan.lifecycleHeading')}</h2>
            {plan.status === 'PLANNED' ? (
              <button type="button" className="secondary" onClick={() => unscheduleMutation.mutate(plan)} disabled={unscheduleMutation.isPending}>
                {t('m5s3.plan.unschedule')}
              </button>
            ) : (
              <form className="form-grid" onSubmit={submitSchedule}>
                <label htmlFor="plan-schedule-start">{t('m5s3.plan.plannedStart')}</label>
                <input id="plan-schedule-start" name="plannedStart" type="datetime-local" required defaultValue={localDateTimeInput(plan.plannedStart)} />
                <label htmlFor="plan-schedule-end">{t('m5s3.plan.plannedEnd')}</label>
                <input id="plan-schedule-end" name="plannedEnd" type="datetime-local" defaultValue={localDateTimeInput(plan.plannedEnd)} />
                <button type="submit" disabled={scheduleMutation.isPending}>{t('m5s3.plan.schedule')}</button>
              </form>
            )}

            <form className="form-grid planning-action-form" onSubmit={submitComplete}>
              <label htmlFor="plan-complete-date">{t('m5s3.plan.experiencedOn')}</label>
              <input id="plan-complete-date" name="experiencedOn" type="date" required defaultValue={localDateTimeInput(new Date()).slice(0, 10)} />
              <button type="submit" disabled={completeMutation.isPending}>{t('m5s3.plan.complete')}</button>
            </form>

            {plan.sourceWishId ? (
              <button type="button" className="tertiary" onClick={() => returnMutation.mutate(plan)} disabled={returnMutation.isPending}>
                {t('m5s3.plan.returnToWish')}
              </button>
            ) : null}
            {lifecycleError ? <ProblemState error={lifecycleError} onRetry={() => void planQuery.refetch()} /> : null}
          </section>
        ) : null}
      </div>

      {plan.capabilities.canDelete ? (
        <section className="planning-danger-zone" aria-labelledby="plan-delete-heading">
          <h2 id="plan-delete-heading">{t('m5s3.common.deleteHeading')}</h2>
          <p>{t('m5s3.plan.deleteConsequence')}</p>
          {!confirmDelete ? (
            <button type="button" className="danger" onClick={() => setConfirmDelete(true)}>{t('m5s3.common.delete')}</button>
          ) : (
            <div className="planning-confirm-row">
              <button type="button" className="danger" onClick={() => deleteMutation.mutate(plan)} disabled={deleteMutation.isPending}>
                {deleteMutation.isPending ? t('m5s3.common.deleting') : t('m5s3.common.confirmDelete')}
              </button>
              <button type="button" className="tertiary" onClick={() => setConfirmDelete(false)}>{t('common.cancel')}</button>
            </div>
          )}
          {deleteMutation.error ? <ProblemState error={deleteMutation.error} onRetry={() => void planQuery.refetch()} /> : null}
        </section>
      ) : null}
    </div>
  );
}
