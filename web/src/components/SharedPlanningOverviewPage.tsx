import type { FormEvent } from 'react';
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import type { PlanDetail } from '../api/generated/models/PlanDetail';
import type { WishDetail } from '../api/generated/models/WishDetail';
import { normalizeClientError } from '../client/problemDetails';
import { planDetailPath, wishDetailPath } from '../client/routes';
import {
  loadAllPlaces,
  type SharedPlanningApis,
} from '../client/sharedPlanning';
import { invalidateDashboard } from '../client/dashboardQueries';
import { useTranslation } from '../i18n';
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

function statusLabel(
  t: ReturnType<typeof useTranslation>['t'],
  domain: 'wish' | 'plan',
  status: string,
): string {
  return t(`m5s3.${domain}.status.${status}`);
}

function PlanningCard({
  title,
  meta,
  to,
}: {
  title: string;
  meta?: string | null;
  to: string;
}) {
  return (
    <li className="planning-card-item">
      <Link className="planning-card planning-card-link" to={to}>
        <div className="planning-card-copy">
          <h3>{title}</h3>
          {meta ? <p className="planning-meta">{meta}</p> : null}
        </div>
      </Link>
    </li>
  );
}

export function SharedPlanningOverviewPage({
  apis,
  spaceId,
}: {
  apis: SharedPlanningApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const wishes = useInfiniteQuery({
    queryKey: ['m5-s3', 'wishes', spaceId],
    queryFn: ({ pageParam }) =>
      apiCall(() =>
        apis.wishes.listWishes({
          spaceId,
          cursor: pageParam,
          limit: PAGE_SIZE,
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: nextCursor<WishDetail>,
    retry: false,
  });

  const plans = useInfiniteQuery({
    queryKey: ['m5-s3', 'plans', spaceId],
    queryFn: ({ pageParam }) =>
      apiCall(() =>
        apis.plans.listPlans({ spaceId, cursor: pageParam, limit: PAGE_SIZE }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: nextCursor<PlanDetail>,
    retry: false,
  });

  const placesQuery = useQuery({
    queryKey: ['m5-s3', 'places', spaceId],
    queryFn: () => apiCall(() => loadAllPlaces(apis, spaceId)),
    staleTime: 30_000,
    retry: false,
  });

  const invalidate = (kind: string) =>
    queryClient.invalidateQueries({ queryKey: ['m5-s3', kind, spaceId] });

  const createWish = useMutation({
    mutationFn: (title: string) =>
      apiCall(() => apis.wishes.createWish({ spaceId, wishCreate: { title } })),
    onSuccess: () => invalidate('wishes'),
  });

  const createPlan = useMutation({
    mutationFn: (values: {
      title: string;
      description?: string;
      placeId?: string;
    }) => apiCall(() => apis.plans.createPlan({ spaceId, planCreate: values })),
    onSuccess: async () => {
      invalidate('plans');
      await invalidateDashboard(queryClient, spaceId);
    },
  });

  const wishItems = wishes.data?.pages.flatMap((page) => page.items) ?? [];
  const planItems = plans.data?.pages.flatMap((page) => page.items) ?? [];

  function submitWish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    createWish.mutate(String(data.get('title')).trim(), {
      onSuccess: () => form.reset(),
    });
  }

  function submitPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const description = String(data.get('description')).trim();
    const placeId = String(data.get('placeId')).trim();
    createPlan.mutate(
      {
        title: String(data.get('title')).trim(),
        description: description || undefined,
        placeId: placeId || undefined,
      },
      { onSuccess: () => form.reset() },
    );
  }

  const placeChoices = (placesQuery.data ?? []).map((place) => (
    <option key={place.id} value={place.id}>
      {place.name}
    </option>
  ));

  return (
    <div className="page planning-page">
      <PageHeader
        eyebrow={t('m5s3.overview.eyebrow')}
        title={t('m5s3.overview.title')}
        description={t('m5s3.overview.intro')}
      />

      <div className="future-map">
        <div className="future-map-path" aria-hidden="true" />

        <section className="future-map-stop future-map-stop-soon sbs-motion-reveal">
          <div className="future-map-marker">
            <span className="marker-dot" />
          </div>
          <div className="future-map-content">
            <h2 className="future-map-heading">{t('m5s3.overview.soon')}</h2>
            <p className="future-map-intro">{t('m5s3.overview.soonIntro')}</p>

            {plans.isLoading ? (
              <UiState kind="loading" title={t('states.loading.title')} />
            ) : null}
            {plans.error ? (
              <ProblemState
                error={plans.error}
                onRetry={() => void plans.refetch()}
              />
            ) : null}
            {!plans.isLoading && !plans.error && planItems.length === 0 ? (
              <p className="planning-empty">{t('m5s3.common.empty')}</p>
            ) : null}
            {planItems.length > 0 ? (
              <ul className="planning-list">
                {planItems.map((plan) => (
                  <PlanningCard
                    key={plan.id}
                    title={plan.title}
                    meta={statusLabel(t, 'plan', plan.status)}
                    to={planDetailPath(plan.id)}
                  />
                ))}
              </ul>
            ) : null}
            {plans.hasNextPage ? (
              <button
                type="button"
                className="tertiary compact-action"
                onClick={() => void plans.fetchNextPage()}
                disabled={plans.isFetchingNextPage}
              >
                {plans.isFetchingNextPage
                  ? t('m5s3.common.loadingMore')
                  : t('m5s3.common.loadMore')}
              </button>
            ) : null}
            <details className="planning-create">
              <summary id="plan-title">{t('m5s3.plan.create')}</summary>
              <form
                onSubmit={submitPlan}
                className="form-grid planning-create-form"
              >
                <label htmlFor="create-plan-title">
                  {t('m5s3.common.title')}
                </label>
                <input
                  id="create-plan-title"
                  name="title"
                  required
                  maxLength={200}
                />
                <label htmlFor="create-plan-description">
                  {t('m5s3.common.description')}
                </label>
                <textarea
                  id="create-plan-description"
                  name="description"
                  rows={3}
                />
                <label htmlFor="create-plan-place">
                  {t('m5s3.common.place')}
                </label>
                <select id="create-plan-place" name="placeId" defaultValue="">
                  <option value="">{t('m5s3.common.noPlace')}</option>
                  {placeChoices}
                </select>
                <button type="submit" disabled={createPlan.isPending}>
                  {createPlan.isPending
                    ? t('m5s3.common.saving')
                    : t('m5s3.common.save')}
                </button>
                {createPlan.error ? (
                  <ProblemState error={createPlan.error} />
                ) : null}
              </form>
            </details>
          </div>
        </section>

        <section
          className="future-map-stop future-map-stop-someday sbs-motion-reveal"
          style={{ animationDelay: '100ms' }}
        >
          <div className="future-map-marker">
            <span className="marker-dot" />
          </div>
          <div className="future-map-content">
            <h2 className="future-map-heading">{t('m5s3.overview.someday')}</h2>
            <p className="future-map-intro">
              {t('m5s3.overview.somedayIntro')}
            </p>

            {wishes.isLoading ? (
              <UiState kind="loading" title={t('states.loading.title')} />
            ) : null}
            {wishes.error ? (
              <ProblemState
                error={wishes.error}
                onRetry={() => void wishes.refetch()}
              />
            ) : null}
            {!wishes.isLoading && !wishes.error && wishItems.length === 0 ? (
              <p className="planning-empty">{t('m5s3.common.empty')}</p>
            ) : null}
            {wishItems.length > 0 ? (
              <ul className="planning-list">
                {wishItems.map((wish) => (
                  <PlanningCard
                    key={wish.id}
                    title={wish.title}
                    meta={statusLabel(t, 'wish', wish.status)}
                    to={wishDetailPath(wish.id)}
                  />
                ))}
              </ul>
            ) : null}
            {wishes.hasNextPage ? (
              <button
                type="button"
                className="tertiary compact-action"
                onClick={() => void wishes.fetchNextPage()}
                disabled={wishes.isFetchingNextPage}
              >
                {wishes.isFetchingNextPage
                  ? t('m5s3.common.loadingMore')
                  : t('m5s3.common.loadMore')}
              </button>
            ) : null}
            <details className="planning-create">
              <summary id="wish-title">{t('m5s3.wish.create')}</summary>
              <form
                onSubmit={submitWish}
                className="form-grid planning-create-form"
              >
                <label htmlFor="create-wish-title">
                  {t('m5s3.common.title')}
                </label>
                <input
                  id="create-wish-title"
                  name="title"
                  required
                  maxLength={200}
                />
                <button type="submit" disabled={createWish.isPending}>
                  {createWish.isPending
                    ? t('m5s3.common.saving')
                    : t('m5s3.common.save')}
                </button>
                {createWish.error ? (
                  <ProblemState error={createWish.error} />
                ) : null}
              </form>
            </details>
          </div>
        </section>
      </div>
    </div>
  );
}
