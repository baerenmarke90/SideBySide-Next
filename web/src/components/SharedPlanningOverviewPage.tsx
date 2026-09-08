import {
  type FormEvent,
  type KeyboardEvent,
  useEffect,
  useId,
  useRef,
  useState,
} from 'react';
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import type { PlaceDetail } from '../api/generated/models/PlaceDetail';
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

function PlacePicker({
  id,
  label,
  places,
  selectedPlaceId,
  onSelect,
  onAddNewPlace,
  noPlaceLabel,
  addNewPlaceLabel,
}: {
  id: string;
  label: string;
  places: PlaceDetail[];
  selectedPlaceId: string;
  onSelect: (placeId: string) => void;
  onAddNewPlace: () => void;
  noPlaceLabel: string;
  addNewPlaceLabel: string;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent): void {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [open]);

  function closeMenu(): void {
    setOpen(false);
    triggerRef.current?.focus();
  }

  function focusItem(index: number): void {
    const items =
      rootRef.current?.querySelectorAll<HTMLElement>('[role^="menuitem"]');
    if (!items?.length) return;
    items[(index + items.length) % items.length]?.focus();
  }

  function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>): void {
    if (
      event.key === 'ArrowDown' ||
      event.key === 'Enter' ||
      event.key === ' '
    ) {
      event.preventDefault();
      setOpen(true);
      window.requestAnimationFrame(() => focusItem(0));
    }
  }

  function handleMenuKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    const items = Array.from(
      rootRef.current?.querySelectorAll<HTMLElement>('[role^="menuitem"]') ??
        [],
    );
    if (!items.length) return;
    const currentIndex = items.indexOf(document.activeElement as HTMLElement);
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      focusItem(currentIndex + 1);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      focusItem(currentIndex <= 0 ? items.length - 1 : currentIndex - 1);
    } else if (event.key === 'Home') {
      event.preventDefault();
      focusItem(0);
    } else if (event.key === 'End') {
      event.preventDefault();
      focusItem(items.length - 1);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      closeMenu();
    } else if (event.key === 'Tab') {
      setOpen(false);
    }
  }

  const selectedLabel =
    places.find((place) => place.id === selectedPlaceId)?.name ?? noPlaceLabel;

  return (
    <div className="place-picker" ref={rootRef}>
      <button
        ref={triggerRef}
        type="button"
        id={id}
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        className="place-picker-trigger"
        onClick={() => setOpen((value) => !value)}
        onKeyDown={handleTriggerKeyDown}
      >
        <span>{selectedLabel}</span>
        <span className="place-picker-caret" aria-hidden="true" />
      </button>
      {open ? (
        <div
          id={menuId}
          role="menu"
          aria-label={label}
          className="place-picker-menu"
          onKeyDown={handleMenuKeyDown}
        >
          <button
            type="button"
            role="menuitemradio"
            aria-checked={selectedPlaceId === ''}
            className="place-picker-option"
            onClick={() => {
              onSelect('');
              closeMenu();
            }}
          >
            {noPlaceLabel}
          </button>
          {places.map((place) => (
            <button
              key={place.id}
              type="button"
              role="menuitemradio"
              aria-checked={selectedPlaceId === place.id}
              className="place-picker-option"
              onClick={() => {
                onSelect(place.id);
                closeMenu();
              }}
            >
              {place.name}
            </button>
          ))}
          <hr className="place-picker-separator" />
          <button
            type="button"
            role="menuitem"
            className="place-picker-option place-picker-add"
            onClick={() => {
              setOpen(false);
              onAddNewPlace();
            }}
          >
            {addNewPlaceLabel}
          </button>
        </div>
      ) : null}
    </div>
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
    queryKey: ['m5-s3', 'places', spaceId, 'options'],
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

  const [selectedPlanPlaceId, setSelectedPlanPlaceId] = useState('');
  const [isCreatingPlanPlace, setIsCreatingPlanPlace] = useState(false);
  const [newPlanPlaceName, setNewPlanPlaceName] = useState('');
  const [newPlanPlaceAddress, setNewPlanPlaceAddress] = useState('');
  const newPlanPlaceNameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isCreatingPlanPlace) newPlanPlaceNameRef.current?.focus();
  }, [isCreatingPlanPlace]);

  const createPlanPlace = useMutation({
    mutationFn: (values: { name: string; address?: string }) =>
      apiCall(() => apis.places.createPlace({ spaceId, placeCreate: values })),
    onSuccess: async (created) => {
      await queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'places', spaceId, 'options'],
      });
      setSelectedPlanPlaceId(created.id);
      setIsCreatingPlanPlace(false);
      setNewPlanPlaceName('');
      setNewPlanPlaceAddress('');
    },
  });

  function submitNewPlanPlace() {
    const name = newPlanPlaceName.trim();
    if (!name) return;
    const address = newPlanPlaceAddress.trim();
    createPlanPlace.mutate({ name, address: address || undefined });
  }

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
    createPlan.mutate(
      {
        title: String(data.get('title')).trim(),
        description: description || undefined,
        placeId: selectedPlanPlaceId || undefined,
      },
      {
        onSuccess: () => {
          form.reset();
          setSelectedPlanPlaceId('');
          setIsCreatingPlanPlace(false);
        },
      },
    );
  }

  return (
    <div className="page planning-page planning-sanctuary">
      <PageHeader
        eyebrow={t('m5s3.overview.eyebrow')}
        title={t('m5s3.overview.title')}
        description={t('m5s3.overview.intro')}
      />

      <div className="future-map">
        <div className="future-map-path" aria-hidden="true" />

        <section className="future-map-stop future-map-stop-soon sbs-motion-reveal">
          <div
            className="future-map-marker"
            style={{
              background: 'var(--color-brand)',
              boxShadow:
                '0 0 0 2px var(--color-surface), 0 5px 12px var(--color-brand-glow)',
            }}
          >
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
              <p className="planning-empty">{t('m5s3.overview.soonEmpty')}</p>
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
                <PlacePicker
                  id="create-plan-place"
                  label={t('m5s3.common.place')}
                  places={placesQuery.data ?? []}
                  selectedPlaceId={selectedPlanPlaceId}
                  onSelect={setSelectedPlanPlaceId}
                  onAddNewPlace={() => setIsCreatingPlanPlace(true)}
                  noPlaceLabel={t('m5s3.common.noPlace')}
                  addNewPlaceLabel={t('m5s3.plan.addNewPlace')}
                />
                {isCreatingPlanPlace ? (
                  <div className="inline-place-create">
                    <div className="field-group">
                      <label htmlFor="new-plan-place-name">
                        {t('m5s3.place.name')}
                      </label>
                      <input
                        id="new-plan-place-name"
                        ref={newPlanPlaceNameRef}
                        value={newPlanPlaceName}
                        onChange={(event) =>
                          setNewPlanPlaceName(event.target.value)
                        }
                        onKeyDown={(event) => {
                          if (event.key === 'Enter') event.preventDefault();
                        }}
                        maxLength={200}
                      />
                    </div>
                    <div className="field-group">
                      <label htmlFor="new-plan-place-address">
                        {t('m5s3.place.address')}
                      </label>
                      <input
                        id="new-plan-place-address"
                        value={newPlanPlaceAddress}
                        onChange={(event) =>
                          setNewPlanPlaceAddress(event.target.value)
                        }
                        onKeyDown={(event) => {
                          if (event.key === 'Enter') event.preventDefault();
                        }}
                      />
                    </div>
                    <div className="inline-place-create-actions">
                      <button
                        type="button"
                        className="button-link secondary-link"
                        onClick={() => {
                          setIsCreatingPlanPlace(false);
                          setNewPlanPlaceName('');
                          setNewPlanPlaceAddress('');
                        }}
                      >
                        {t('m5s3.plan.newPlaceCancel')}
                      </button>
                      <button
                        type="button"
                        disabled={
                          createPlanPlace.isPending || !newPlanPlaceName.trim()
                        }
                        onClick={submitNewPlanPlace}
                      >
                        {createPlanPlace.isPending
                          ? t('m5s3.plan.newPlaceSaving')
                          : t('m5s3.plan.newPlaceSave')}
                      </button>
                    </div>
                    {createPlanPlace.error ? (
                      <ProblemState error={createPlanPlace.error} />
                    ) : null}
                  </div>
                ) : null}
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
              <p className="planning-empty">
                {t('m5s3.overview.somedayEmpty')}
              </p>
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
