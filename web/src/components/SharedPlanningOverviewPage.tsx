import { type FormEvent, type ReactNode, useState } from 'react';
import {
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import type { WishDetail } from '../api/generated/models/WishDetail';
import type { PlanDetail } from '../api/generated/models/PlanDetail';
import type { PlaceDetail } from '../api/generated/models/PlaceDetail';
import type { ChapterDetail } from '../api/generated/models/ChapterDetail';
import type { CollectionDetail } from '../api/generated/models/CollectionDetail';
import { normalizeClientError } from '../client/problemDetails';
import type { SharedPlanningApis } from '../client/sharedPlanning';
import {
  chapterDetailPath,
  collectionDetailPath,
  planDetailPath,
  placeDetailPath,
  wishDetailPath,
} from '../client/routes';
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
  const { t } = useTranslation();
  return (
    <li className="planning-card">
      <div className="planning-card-copy">
        <h3>{title}</h3>
        {meta ? <p className="planning-meta">{meta}</p> : null}
      </div>
      <Link className="button-link secondary-link" to={to}>
        {t('m5s3.common.open')}
      </Link>
    </li>
  );
}

function PlanningSection({
  id,
  title,
  intro,
  children,
  create,
  loading,
  error,
  empty,
  onRetry,
  hasMore,
  loadingMore,
  onLoadMore,
}: {
  id: string;
  title: string;
  intro: string;
  children: ReactNode;
  create: ReactNode;
  loading: boolean;
  error: Error | null;
  empty: boolean;
  onRetry: () => void;
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
}) {
  const { t } = useTranslation();
  return (
    <section className="layout-panel" aria-labelledby={`${id}-heading`}>
      <div className="layout-section-head">
        <div>
          <h2 id={`${id}-heading`}>{title}</h2>
          <p>{intro}</p>
        </div>
        {create}
      </div>
      {loading ? (
        <UiState kind="loading" title={t('m5s3.common.loading')} />
      ) : null}
      {error ? <ProblemState error={error} onRetry={onRetry} /> : null}
      {!loading && !error && empty ? (
        <p className="planning-empty">{t('m5s3.common.empty')}</p>
      ) : null}
      {children}
      {hasMore ? (
        <button
          type="button"
          className="secondary compact-action"
          onClick={onLoadMore}
          disabled={loadingMore}
        >
          {loadingMore
            ? t('m5s3.common.loadingMore')
            : t('m5s3.common.loadMore')}
        </button>
      ) : null}
    </section>
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
  const [placeCoordinateError, setPlaceCoordinateError] = useState(false);

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
  const places = useInfiniteQuery({
    queryKey: ['m5-s3', 'places', spaceId],
    queryFn: ({ pageParam }) =>
      apiCall(() =>
        apis.places.listPlaces({
          spaceId,
          cursor: pageParam,
          limit: PAGE_SIZE,
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: nextCursor<PlaceDetail>,
    retry: false,
  });
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
  const collections = useInfiniteQuery({
    queryKey: ['m5-s3', 'collections', spaceId],
    queryFn: ({ pageParam }) =>
      apiCall(() =>
        apis.collections.listCollections({
          spaceId,
          cursor: pageParam,
          limit: PAGE_SIZE,
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: nextCursor<CollectionDetail>,
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
    onSuccess: () => invalidate('plans'),
  });
  const createPlace = useMutation({
    mutationFn: (values: {
      name: string;
      description?: string;
      address?: string;
      latitude?: number;
      longitude?: number;
    }) =>
      apiCall(() => apis.places.createPlace({ spaceId, placeCreate: values })),
    onSuccess: () => invalidate('places'),
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
    onSuccess: () => invalidate('chapters'),
  });
  const createCollection = useMutation({
    mutationFn: (title: string) =>
      apiCall(() =>
        apis.collections.createCollection({
          spaceId,
          collectionCreate: { title },
        }),
      ),
    onSuccess: () => invalidate('collections'),
  });

  const wishItems = wishes.data?.pages.flatMap((page) => page.items) ?? [];
  const planItems = plans.data?.pages.flatMap((page) => page.items) ?? [];
  const placeItems = places.data?.pages.flatMap((page) => page.items) ?? [];
  const chapterItems = chapters.data?.pages.flatMap((page) => page.items) ?? [];
  const collectionItems =
    collections.data?.pages.flatMap((page) => page.items) ?? [];

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

  function submitPlace(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const latitudeRaw = String(data.get('latitude')).trim();
    const longitudeRaw = String(data.get('longitude')).trim();
    if (Boolean(latitudeRaw) !== Boolean(longitudeRaw)) {
      setPlaceCoordinateError(true);
      return;
    }
    setPlaceCoordinateError(false);
    const description = String(data.get('description')).trim();
    const address = String(data.get('address')).trim();
    createPlace.mutate(
      {
        name: String(data.get('name')).trim(),
        description: description || undefined,
        address: address || undefined,
        latitude: latitudeRaw ? Number(latitudeRaw) : undefined,
        longitude: longitudeRaw ? Number(longitudeRaw) : undefined,
      },
      {
        onSuccess: () => {
          form.reset();
          setPlaceCoordinateError(false);
        },
      },
    );
  }

  function submitChapter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const startOn = String(data.get('startOn')).trim();
    const endOn = String(data.get('endOn')).trim();
    const description = String(data.get('description')).trim();
    const placeId = String(data.get('placeId')).trim();
    createChapter.mutate(
      {
        title: String(data.get('title')).trim(),
        description: description || undefined,
        startOn: startOn ? new Date(`${startOn}T00:00:00Z`) : undefined,
        endOn: endOn ? new Date(`${endOn}T00:00:00Z`) : undefined,
        placeId: placeId || undefined,
      },
      { onSuccess: () => form.reset() },
    );
  }

  function submitCollection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    createCollection.mutate(String(data.get('title')).trim(), {
      onSuccess: () => form.reset(),
    });
  }

  const placeChoices = placeItems.map((place) => (
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

      <div className="layout-columns planning-grid">
        <PlanningSection
          id="wishes"
          title={t('m5s3.wish.heading')}
          intro={t('m5s3.wish.intro')}
          loading={wishes.isLoading}
          error={wishes.error}
          empty={wishItems.length === 0}
          onRetry={() => void wishes.refetch()}
          hasMore={Boolean(wishes.hasNextPage)}
          loadingMore={wishes.isFetchingNextPage}
          onLoadMore={() => void wishes.fetchNextPage()}
          create={
            <details className="planning-create">
              <summary>{t('m5s3.wish.create')}</summary>
              <form
                onSubmit={submitWish}
                className="form-grid planning-create-form"
              >
                <label htmlFor="wish-title">{t('m5s3.common.title')}</label>
                <input id="wish-title" name="title" required maxLength={200} />
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
          }
        >
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
        </PlanningSection>

        <PlanningSection
          id="plans"
          title={t('m5s3.plan.heading')}
          intro={t('m5s3.plan.intro')}
          loading={plans.isLoading}
          error={plans.error}
          empty={planItems.length === 0}
          onRetry={() => void plans.refetch()}
          hasMore={Boolean(plans.hasNextPage)}
          loadingMore={plans.isFetchingNextPage}
          onLoadMore={() => void plans.fetchNextPage()}
          create={
            <details className="planning-create">
              <summary>{t('m5s3.plan.create')}</summary>
              <form
                onSubmit={submitPlan}
                className="form-grid planning-create-form"
              >
                <label htmlFor="plan-title">{t('m5s3.common.title')}</label>
                <input id="plan-title" name="title" required maxLength={200} />
                <label htmlFor="plan-description">
                  {t('m5s3.common.description')}
                </label>
                <textarea id="plan-description" name="description" rows={3} />
                <label htmlFor="plan-place">{t('m5s3.common.place')}</label>
                <select id="plan-place" name="placeId" defaultValue="">
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
          }
        >
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
        </PlanningSection>

        <PlanningSection
          id="places"
          title={t('m5s3.place.heading')}
          intro={t('m5s3.place.intro')}
          loading={places.isLoading}
          error={places.error}
          empty={placeItems.length === 0}
          onRetry={() => void places.refetch()}
          hasMore={Boolean(places.hasNextPage)}
          loadingMore={places.isFetchingNextPage}
          onLoadMore={() => void places.fetchNextPage()}
          create={
            <details className="planning-create">
              <summary>{t('m5s3.place.create')}</summary>
              <form
                onSubmit={submitPlace}
                className="form-grid planning-create-form"
              >
                <label htmlFor="place-name">{t('m5s3.place.name')}</label>
                <input id="place-name" name="name" required maxLength={200} />
                <label htmlFor="place-description">
                  {t('m5s3.common.description')}
                </label>
                <textarea id="place-description" name="description" rows={3} />
                <label htmlFor="place-address">{t('m5s3.place.address')}</label>
                <input id="place-address" name="address" />
                <div className="planning-coordinate-grid">
                  <div className="field-group">
                    <label htmlFor="place-latitude">
                      {t('m5s3.place.latitude')}
                    </label>
                    <input
                      id="place-latitude"
                      name="latitude"
                      type="number"
                      step="any"
                      min="-90"
                      max="90"
                      aria-invalid={placeCoordinateError}
                      aria-describedby={
                        placeCoordinateError
                          ? 'place-coordinate-help place-coordinate-error'
                          : 'place-coordinate-help'
                      }
                    />
                  </div>
                  <div className="field-group">
                    <label htmlFor="place-longitude">
                      {t('m5s3.place.longitude')}
                    </label>
                    <input
                      id="place-longitude"
                      name="longitude"
                      type="number"
                      step="any"
                      min="-180"
                      max="180"
                      aria-invalid={placeCoordinateError}
                      aria-describedby={
                        placeCoordinateError
                          ? 'place-coordinate-help place-coordinate-error'
                          : 'place-coordinate-help'
                      }
                    />
                  </div>
                </div>
                <p id="place-coordinate-help" className="field-help">
                  {t('m5s3.place.coordinateHelp')}
                </p>
                {placeCoordinateError ? (
                  <p
                    id="place-coordinate-error"
                    className="field-error"
                    role="alert"
                  >
                    {t('m5s3.place.coordinatePairError')}
                  </p>
                ) : null}
                <button type="submit" disabled={createPlace.isPending}>
                  {createPlace.isPending
                    ? t('m5s3.common.saving')
                    : t('m5s3.common.save')}
                </button>
                {createPlace.error ? (
                  <ProblemState error={createPlace.error} />
                ) : null}
              </form>
            </details>
          }
        >
          {placeItems.length > 0 ? (
            <ul className="planning-list">
              {placeItems.map((place) => (
                <PlanningCard
                  key={place.id}
                  title={place.name}
                  meta={place.address}
                  to={placeDetailPath(place.id)}
                />
              ))}
            </ul>
          ) : null}
        </PlanningSection>

        <PlanningSection
          id="chapters"
          title={t('m5s3.chapter.heading')}
          intro={t('m5s3.chapter.intro')}
          loading={chapters.isLoading}
          error={chapters.error}
          empty={chapterItems.length === 0}
          onRetry={() => void chapters.refetch()}
          hasMore={Boolean(chapters.hasNextPage)}
          loadingMore={chapters.isFetchingNextPage}
          onLoadMore={() => void chapters.fetchNextPage()}
          create={
            <details className="planning-create">
              <summary>{t('m5s3.chapter.create')}</summary>
              <form
                onSubmit={submitChapter}
                className="form-grid planning-create-form"
              >
                <label htmlFor="chapter-title">{t('m5s3.common.title')}</label>
                <input
                  id="chapter-title"
                  name="title"
                  required
                  maxLength={200}
                />
                <label htmlFor="chapter-description">
                  {t('m5s3.common.description')}
                </label>
                <textarea
                  id="chapter-description"
                  name="description"
                  rows={3}
                />
                <div className="planning-coordinate-grid">
                  <div className="field-group">
                    <label htmlFor="chapter-start">
                      {t('m5s3.chapter.startOn')}
                    </label>
                    <input id="chapter-start" name="startOn" type="date" />
                  </div>
                  <div className="field-group">
                    <label htmlFor="chapter-end">
                      {t('m5s3.chapter.endOn')}
                    </label>
                    <input id="chapter-end" name="endOn" type="date" />
                  </div>
                </div>
                <label htmlFor="chapter-place">{t('m5s3.common.place')}</label>
                <select id="chapter-place" name="placeId" defaultValue="">
                  <option value="">{t('m5s3.common.noPlace')}</option>
                  {placeChoices}
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
          }
        >
          {chapterItems.length > 0 ? (
            <ul className="planning-list">
              {chapterItems.map((chapter) => {
                const start = formatDate(chapter.startOn);
                const end = formatDate(chapter.endOn);
                const meta =
                  start && end ? `${start} – ${end}` : (start ?? end);
                return (
                  <PlanningCard
                    key={chapter.id}
                    title={chapter.title}
                    meta={meta}
                    to={chapterDetailPath(chapter.id)}
                  />
                );
              })}
            </ul>
          ) : null}
        </PlanningSection>

        <PlanningSection
          id="collections"
          title={t('m5s3.collection.heading')}
          intro={t('m5s3.collection.intro')}
          loading={collections.isLoading}
          error={collections.error}
          empty={collectionItems.length === 0}
          onRetry={() => void collections.refetch()}
          hasMore={Boolean(collections.hasNextPage)}
          loadingMore={collections.isFetchingNextPage}
          onLoadMore={() => void collections.fetchNextPage()}
          create={
            <details className="planning-create">
              <summary>{t('m5s3.collection.create')}</summary>
              <form
                onSubmit={submitCollection}
                className="form-grid planning-create-form"
              >
                <label htmlFor="collection-title">
                  {t('m5s3.common.title')}
                </label>
                <input
                  id="collection-title"
                  name="title"
                  required
                  maxLength={200}
                />
                <button type="submit" disabled={createCollection.isPending}>
                  {createCollection.isPending
                    ? t('m5s3.common.saving')
                    : t('m5s3.common.save')}
                </button>
                {createCollection.error ? (
                  <ProblemState error={createCollection.error} />
                ) : null}
              </form>
            </details>
          }
        >
          {collectionItems.length > 0 ? (
            <ul className="planning-list">
              {collectionItems.map((collection) => (
                <PlanningCard
                  key={collection.id}
                  title={collection.title}
                  meta={t('m5s3.collection.itemCount', {
                    count: collection.items.length,
                  })}
                  to={collectionDetailPath(collection.id)}
                />
              ))}
            </ul>
          ) : null}
        </PlanningSection>
      </div>
    </div>
  );
}
