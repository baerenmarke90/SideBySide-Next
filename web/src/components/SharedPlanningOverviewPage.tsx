import {
  type FormEvent,
  type KeyboardEvent,
  type ReactNode,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from 'react';
import { createPortal } from 'react-dom';
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { Link, useLocation } from 'react-router-dom';
import type { PlaceDetail } from '../api/generated/models/PlaceDetail';
import type { PlanDetail } from '../api/generated/models/PlanDetail';
import type { PlanSchedule } from '../api/generated/models/PlanSchedule';
import type { WishDetail } from '../api/generated/models/WishDetail';
import { WishStatus } from '../api/generated/models/WishStatus';
import { invalidateDashboard } from '../client/dashboardQueries';
import {
  loadPlanningOverviewPlans,
  selectUpcomingPlans,
} from '../client/planningOverview';
import {
  planPillLabel,
  planPillTone,
  wishPillTone,
} from '../client/planningPresentation';
import { normalizeClientError } from '../client/problemDetails';
import { planDetailPath, wishDetailPath } from '../client/routes';
import {
  loadAllPlaces,
  planScheduleFromInputs,
  type SharedPlanningApis,
} from '../client/sharedPlanning';
import { useDismissiblePopover } from '../client/useDismissiblePopover';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { PlanScheduleFields } from './PlanScheduleFields';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import './SharedPlanningPages.css';
import './PlanningReference.css';

const PAGE_SIZE = 20;

type PlanenSegment = 'wishes' | 'plans';

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

function segmentForHash(hash: string): PlanenSegment | null {
  if (hash === '#plan-title') return 'plans';
  if (hash === '#wish-title') return 'wishes';
  return null;
}

function PlanenCard({
  title,
  attribution,
  pillLabel,
  pillTone,
  to,
}: {
  title: string;
  attribution: string;
  pillLabel: string;
  pillTone: string;
  to: string;
}) {
  return (
    <li className="planen-card-item">
      <Link className="planen-card" to={to}>
        <h2 className="planen-card-title">{title}</h2>
        <span className="planen-card-attribution">{attribution}</span>
        <span className="planen-card-pills">
          <span className={`planen-pill planen-pill-${pillTone}`}>
            {pillLabel}
          </span>
        </span>
      </Link>
    </li>
  );
}

function PlanenSegmentedControl({
  active,
  onChange,
  wishesTabId,
  plansTabId,
  wishesPanelId,
  plansPanelId,
}: {
  active: PlanenSegment;
  onChange: (segment: PlanenSegment) => void;
  wishesTabId: string;
  plansTabId: string;
  wishesPanelId: string;
  plansPanelId: string;
}) {
  const { t } = useTranslation();
  const wishesRef = useRef<HTMLButtonElement>(null);
  const plansRef = useRef<HTMLButtonElement>(null);

  function switchTo(segment: PlanenSegment, focus: boolean): void {
    onChange(segment);
    if (!focus) return;
    (segment === 'plans' ? plansRef : wishesRef).current?.focus();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    switchTo(active === 'plans' ? 'wishes' : 'plans', true);
  }

  return (
    <div
      className="planen-segmented"
      role="tablist"
      aria-label={t('m5s3.overview.segmentedLabel')}
      onKeyDown={handleKeyDown}
    >
      <button
        ref={plansRef}
        type="button"
        role="tab"
        id={plansTabId}
        aria-selected={active === 'plans'}
        aria-controls={plansPanelId}
        tabIndex={active === 'plans' ? 0 : -1}
        className={`planen-segment ${active === 'plans' ? 'is-active' : ''}`}
        onClick={() => switchTo('plans', false)}
      >
        {t('m5s3.overview.segmentPlans')}
      </button>
      <button
        ref={wishesRef}
        type="button"
        role="tab"
        id={wishesTabId}
        aria-selected={active === 'wishes'}
        aria-controls={wishesPanelId}
        tabIndex={active === 'wishes' ? 0 : -1}
        className={`planen-segment ${active === 'wishes' ? 'is-active' : ''}`}
        onClick={() => switchTo('wishes', false)}
      >
        {t('m5s3.overview.segmentWishes')}
      </button>
    </div>
  );
}

function PlanenPanel({
  id,
  labelledBy,
  hidden,
  children,
}: {
  id: string;
  labelledBy: string;
  hidden: boolean;
  children: ReactNode;
}) {
  return (
    <div
      id={id}
      role="tabpanel"
      aria-labelledby={labelledBy}
      hidden={hidden}
      className="planen-panel sbs-motion-reveal"
    >
      {children}
    </div>
  );
}

interface PlacePickerCoords {
  left: number;
  width: number;
  maxHeight: number;
  placement: 'below' | 'above';
  top?: number;
  bottom?: number;
}

const PLACE_PICKER_VIEWPORT_MARGIN = 8;
const PLACE_PICKER_PREFERRED_MAX_HEIGHT = 256;

function computePlacePickerCoords(rect: DOMRect): PlacePickerCoords {
  const spaceBelow =
    window.innerHeight - rect.bottom - PLACE_PICKER_VIEWPORT_MARGIN * 2;
  const spaceAbove = rect.top - PLACE_PICKER_VIEWPORT_MARGIN * 2;
  const placement: PlacePickerCoords['placement'] =
    spaceBelow < 120 && spaceAbove > spaceBelow ? 'above' : 'below';

  return {
    left: rect.left,
    width: rect.width,
    maxHeight: Math.max(
      120,
      Math.min(
        PLACE_PICKER_PREFERRED_MAX_HEIGHT,
        placement === 'below' ? spaceBelow : spaceAbove,
      ),
    ),
    placement,
    top:
      placement === 'below'
        ? rect.bottom + PLACE_PICKER_VIEWPORT_MARGIN
        : undefined,
    bottom:
      placement === 'above'
        ? window.innerHeight - rect.top + PLACE_PICKER_VIEWPORT_MARGIN
        : undefined,
  };
}

/**
 * Render the place menu outside animated/overflow stacking contexts so the
 * compact product surface stays usable near the viewport edge.
 */
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
  const { isOpen, close, toggle, triggerRef, panelRef } =
    useDismissiblePopover();
  const [coords, setCoords] = useState<PlacePickerCoords | null>(null);
  const menuId = useId();

  useLayoutEffect(() => {
    if (!isOpen) return;

    function updateCoords(): void {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      setCoords(computePlacePickerCoords(rect));
    }

    updateCoords();
    window.addEventListener('scroll', updateCoords, true);
    window.addEventListener('resize', updateCoords);
    return () => {
      window.removeEventListener('scroll', updateCoords, true);
      window.removeEventListener('resize', updateCoords);
    };
  }, [isOpen, triggerRef]);

  function focusItem(index: number): void {
    const items =
      panelRef.current?.querySelectorAll<HTMLElement>('[role^="menuitem"]');
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
      if (!isOpen) toggle();
      window.requestAnimationFrame(() => focusItem(0));
    }
  }

  function handleMenuKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    const items = Array.from(
      panelRef.current?.querySelectorAll<HTMLElement>('[role^="menuitem"]') ??
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
    } else if (event.key === 'Tab') {
      close();
    }
  }

  const selectedLabel =
    places.find((place) => place.id === selectedPlaceId)?.name ?? noPlaceLabel;

  return (
    <div className="place-picker">
      <button
        ref={triggerRef as React.RefObject<HTMLButtonElement>}
        type="button"
        id={id}
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-controls={menuId}
        className="place-picker-trigger"
        onClick={() => toggle()}
        onKeyDown={handleTriggerKeyDown}
      >
        <span>{selectedLabel}</span>
        <span className="place-picker-caret" aria-hidden="true" />
      </button>
      {isOpen && coords && typeof document !== 'undefined'
        ? createPortal(
            <div
              ref={panelRef as React.RefObject<HTMLDivElement>}
              id={menuId}
              role="menu"
              aria-label={label}
              className="place-picker-menu"
              style={{
                position: 'fixed',
                top: coords.top,
                bottom: coords.bottom,
                left: coords.left,
                width: coords.width,
                maxHeight: coords.maxHeight,
              }}
              onKeyDown={handleMenuKeyDown}
            >
              <button
                type="button"
                role="menuitemradio"
                aria-checked={selectedPlaceId === ''}
                className="place-picker-option"
                onClick={() => {
                  onSelect('');
                  close(true);
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
                    close(true);
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
                  close();
                  onAddNewPlace();
                }}
              >
                {addNewPlaceLabel}
              </button>
            </div>,
            document.body,
          )
        : null}
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
  const location = useLocation();
  const wishesTabId = useId();
  const plansTabId = useId();
  const wishesPanelId = useId();
  const plansPanelId = useId();

  const [activeSegment, setActiveSegment] = useState<PlanenSegment>(
    () => segmentForHash(location.hash) ?? 'plans',
  );

  useLayoutEffect(() => {
    const segment = segmentForHash(location.hash);
    if (segment) setActiveSegment(segment);
  }, [location.hash]);

  const wishes = useInfiniteQuery({
    queryKey: ['m5-s3', 'wishes', spaceId],
    queryFn: ({ pageParam }) =>
      apiCall(() =>
        apis.wishes.listWishes({
          spaceId,
          cursor: pageParam,
          limit: PAGE_SIZE,
          status: WishStatus.OPEN,
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: nextCursor<WishDetail>,
    retry: false,
  });

  const plans = useInfiniteQuery({
    queryKey: ['m5-s3', 'plans', spaceId],
    queryFn: () =>
      apiCall(async () => ({
        items: await loadPlanningOverviewPlans(apis, spaceId),
        nextCursor: null,
      })),
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
      schedule?: PlanSchedule;
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

  const wishItems = (
    wishes.data?.pages.flatMap((page) => page.items) ?? []
  ).filter((wish) => wish.status === WishStatus.OPEN);
  const planItems = plans.data?.pages.flatMap((page) => page.items) ?? [];
  const upcomingPlans = selectUpcomingPlans(planItems);
  const upcomingPlanIds = new Set(upcomingPlans.map((plan) => plan.id));
  const orderedPlanItems = [
    ...upcomingPlans,
    ...planItems.filter(
      (plan) => !upcomingPlanIds.has(plan.id) && plan.status !== 'COMPLETED',
    ),
  ];

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
    const schedule = planScheduleFromInputs(
      String(data.get('plannedDate') ?? ''),
      String(data.get('plannedTime') ?? ''),
    );
    createPlan.mutate(
      {
        title: String(data.get('title')).trim(),
        description: description || undefined,
        placeId: selectedPlanPlaceId || undefined,
        schedule,
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

  const wishesLoading = wishes.isLoading;
  const plansLoading = plans.isLoading;

  return (
    <div className="page planning-page planning-sanctuary planen-overview">
      <PageHeader title={t('m5s3.overview.title')} />

      <PlanenSegmentedControl
        active={activeSegment}
        onChange={setActiveSegment}
        wishesTabId={wishesTabId}
        plansTabId={plansTabId}
        wishesPanelId={wishesPanelId}
        plansPanelId={plansPanelId}
      />

      <PlanenPanel
        id={plansPanelId}
        labelledBy={plansTabId}
        hidden={activeSegment !== 'plans'}
      >
        {plansLoading ? (
          <UiState kind="loading" title={t('states.loading.title')} />
        ) : null}
        {plans.error ? (
          <ProblemState
            error={plans.error}
            onRetry={() => void plans.refetch()}
          />
        ) : null}
        {!plansLoading && !plans.error && orderedPlanItems.length === 0 ? (
          <p className="planen-empty">{t('m5s3.overview.plansEmpty')}</p>
        ) : null}
        {orderedPlanItems.length > 0 ? (
          <ul className="planen-card-list">
            {orderedPlanItems.map((plan) => (
              <PlanenCard
                key={plan.id}
                title={plan.title}
                attribution={t('m5s3.overview.createdBy', {
                  name: plan.creator.displayName,
                })}
                pillLabel={planPillLabel(t, plan)}
                pillTone={planPillTone(plan)}
                to={planDetailPath(plan.id)}
              />
            ))}
          </ul>
        ) : null}
        <details className="planning-create">
          <summary id="plan-title">{t('m5s3.plan.create')}</summary>
          <form
            onSubmit={submitPlan}
            className="form-grid planning-create-form"
          >
            <label htmlFor="create-plan-title">{t('m5s3.common.title')}</label>
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
            <label htmlFor="create-plan-place">{t('m5s3.common.place')}</label>
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
            <PlanScheduleFields idPrefix="create-plan-schedule" />
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
      </PlanenPanel>

      <PlanenPanel
        id={wishesPanelId}
        labelledBy={wishesTabId}
        hidden={activeSegment !== 'wishes'}
      >
        {wishesLoading ? (
          <UiState kind="loading" title={t('states.loading.title')} />
        ) : null}
        {wishes.error ? (
          <ProblemState
            error={wishes.error}
            onRetry={() => void wishes.refetch()}
          />
        ) : null}
        {!wishesLoading && !wishes.error && wishItems.length === 0 ? (
          <p className="planen-empty">{t('m5s3.overview.wishesEmpty')}</p>
        ) : null}
        {wishItems.length > 0 ? (
          <ul className="planen-card-list">
            {wishItems.map((wish) => (
              <PlanenCard
                key={wish.id}
                title={wish.title}
                attribution={t('m5s3.overview.createdBy', {
                  name: wish.creator.displayName,
                })}
                pillLabel={t(`m5s3.wish.status.${wish.status}`)}
                pillTone={wishPillTone(wish.status)}
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
            <label htmlFor="create-wish-title">{t('m5s3.common.title')}</label>
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
      </PlanenPanel>
    </div>
  );
}
