import { type FormEvent, useState } from 'react';
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import type { ActivityItem } from '../api/generated/models/ActivityItem';
import type { DashboardItem } from '../api/generated/models/DashboardItem';
import type { NotificationItem } from '../api/generated/models/NotificationItem';
import type { SearchKind } from '../api/generated/models/SearchKind';
import type { SearchResult } from '../api/generated/models/SearchResult';
import {
  dashboardItemPath,
  engagementTargetPath,
  opaqueNextCursor,
  searchResultPath,
  type M4ProductApis,
} from '../client/m4Product';
import { normalizeClientError } from '../client/problemDetails';
import { resolvedLocale, useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import './M4ProductPages.css';

const PAGE_SIZE = 20;

const SEARCH_KINDS: readonly SearchKind[] = [
  'MEMORY',
  'HEART_MOMENT',
  'MILESTONE',
  'WISH',
  'PLAN',
  'PLACE',
  'CHAPTER',
  'COLLECTION',
  'COLLECTION_ITEM',
  'PRIVATE_NOTE',
  'GIFT_IDEA',
  'PRIVATE_COLLECTION',
  'PRIVATE_COLLECTION_ITEM',
];

async function apiCall<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request();
  } catch (error) {
    throw await normalizeClientError(error);
  }
}

function formatDate(value: Date | null): string | null {
  if (!value) return null;
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
  }).format(value);
}

function formatDateTime(value: Date): string {
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(value);
}

function DashboardItemCard({ item }: { item: DashboardItem }) {
  const { t } = useTranslation();
  const path = dashboardItemPath(item.type, item.id);
  const date =
    formatDate(item.occurredOn) ??
    (item.scheduledAt ? formatDateTime(item.scheduledAt) : null) ??
    (item.createdAt ? formatDateTime(item.createdAt) : null);

  return (
    <li className="m4-item">
      <div className="m4-item-heading">
        <h3>{item.titleOrText || t('m5s5.dashboard.itemFallback')}</h3>
        <span className="m4-item-kind">{t(`m5s5.kind.${item.type}`)}</span>
      </div>
      {date ? <p className="m4-item-meta">{date}</p> : null}
      <div className="m4-item-actions">
        {path ? (
          <Link className="button-link secondary-link" to={path}>
            {t('m5s5.common.open')}
          </Link>
        ) : (
          <span className="m4-muted">{t('m5s5.common.noDirectLink')}</span>
        )}
      </div>
    </li>
  );
}

function DashboardSection({
  title,
  items,
  empty,
}: {
  title: string;
  items: DashboardItem[];
  empty: string;
}) {
  return (
    <section className="layout-panel">
      <div className="layout-section-head">
        <div>
          <h2>{title}</h2>
        </div>
      </div>
      {items.length > 0 ? (
        <ul className="m4-list m4-list-rows">
          {items.map((item) => (
            <DashboardItemCard key={`${item.type}:${item.id}`} item={item} />
          ))}
        </ul>
      ) : (
        <p className="m4-muted">{empty}</p>
      )}
    </section>
  );
}

export function DashboardProductPage({
  apis,
  spaceId,
}: {
  apis: M4ProductApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const dashboardQuery = useQuery({
    queryKey: ['m5-s5', 'dashboard', spaceId],
    queryFn: () => apiCall(() => apis.dashboard.getDashboard({ spaceId })),
    retry: false,
  });

  return (
    <div className="page m4-product-page">
      <PageHeader
        eyebrow={t('m5s5.dashboard.eyebrow')}
        title={t('m5s5.dashboard.title')}
        description={t('m5s5.dashboard.intro')}
        action={
          <button
            type="button"
            className="secondary compact-action"
            onClick={() => void dashboardQuery.refetch()}
            disabled={dashboardQuery.isFetching}
          >
            {dashboardQuery.isFetching
              ? t('m5s5.common.refreshing')
              : t('m5s5.common.refresh')}
          </button>
        }
      />

      {dashboardQuery.isLoading ? (
        <UiState kind="loading" title={t('states.loading.title')} />
      ) : null}
      {dashboardQuery.error ? (
        <ProblemState
          error={dashboardQuery.error}
          onRetry={() => void dashboardQuery.refetch()}
        />
      ) : null}

      {dashboardQuery.data ? (
        <>
          <section
            className="m4-summary-card"
            aria-labelledby="m4-summary-heading"
          >
            <div className="m4-summary-copy">
              <h2 id="m4-summary-heading">
                {dashboardQuery.data.space.partner
                  ? t('m5s5.dashboard.partner', {
                      name: dashboardQuery.data.space.partner.displayName,
                    })
                  : t('m5s5.dashboard.durationTitle')}
              </h2>
              <p className="m4-muted">
                {dashboardQuery.data.relationshipDuration
                  ? t('m5s5.dashboard.durationSince', {
                      date: formatDate(
                        dashboardQuery.data.relationshipDuration.startedOn,
                      ),
                    })
                  : t('m5s5.dashboard.durationEmpty')}
              </p>
            </div>
            {dashboardQuery.data.relationshipDuration ? (
              <p className="m4-summary-value">
                {t('m5s5.dashboard.durationDays', {
                  count: dashboardQuery.data.relationshipDuration.daysTogether,
                })}
              </p>
            ) : null}
          </section>

          <div className="layout-split">
            <div className="layout-main">
              <DashboardSection
                title={t('m5s5.dashboard.recentTitle')}
                items={dashboardQuery.data.recentShared}
                empty={t('m5s5.dashboard.recentEmpty')}
              />
            </div>
            <aside
              className="layout-rail"
              aria-label={t('m5s5.dashboard.railAria')}
            >
              <DashboardSection
                title={t('m5s5.dashboard.upcomingTitle')}
                items={dashboardQuery.data.upcoming}
                empty={t('m5s5.dashboard.upcomingEmpty')}
              />
              <DashboardSection
                title={t('m5s5.dashboard.retrospectiveTitle')}
                items={
                  dashboardQuery.data.retrospective
                    ? [dashboardQuery.data.retrospective]
                    : []
                }
                empty={t('m5s5.dashboard.retrospectiveEmpty')}
              />
            </aside>
          </div>
        </>
      ) : null}
    </div>
  );
}

function SearchResultCard({ item }: { item: SearchResult }) {
  const { t } = useTranslation();
  const path = searchResultPath(item.type, item.id);
  const date = formatDate(item.occurredOn);

  return (
    <li className="m4-item">
      <div className="m4-item-heading">
        <h3>{item.title || t('m5s5.search.resultFallback')}</h3>
        <span className="m4-item-kind">
          {t(`m5s5.kind.${item.type}`)} · {t(`m5s5.scope.${item.scope}`)}
        </span>
      </div>
      {item.excerpt ? <p className="m4-item-excerpt">{item.excerpt}</p> : null}
      {date ? <p className="m4-item-meta">{date}</p> : null}
      <div className="m4-item-actions">
        {path ? (
          <Link className="button-link secondary-link" to={path}>
            {t('m5s5.common.open')}
          </Link>
        ) : (
          <span className="m4-muted">{t('m5s5.common.noDirectLink')}</span>
        )}
      </div>
    </li>
  );
}

export function SearchProductPage({
  apis,
  spaceId,
}: {
  apis: M4ProductApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const [draftQuery, setDraftQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [kind, setKind] = useState<SearchKind | ''>('');

  const searchQuery = useInfiniteQuery({
    queryKey: ['m5-s5', 'search', spaceId, submittedQuery, kind],
    queryFn: ({ pageParam }) =>
      apiCall(() =>
        apis.search.searchSpaceContent({
          spaceId,
          q: submittedQuery,
          type: kind ? [kind] : undefined,
          cursor: pageParam,
          limit: PAGE_SIZE,
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: opaqueNextCursor,
    enabled: submittedQuery.length > 0,
    retry: false,
  });

  const items = searchQuery.data?.pages.flatMap((page) => page.items) ?? [];

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmittedQuery(draftQuery.trim());
  }

  return (
    <div className="page m4-product-page">
      <PageHeader
        eyebrow={t('m5s5.search.eyebrow')}
        title={t('m5s5.search.title')}
        description={t('m5s5.search.intro')}
      />

      <form className="layout-panel m4-toolbar" onSubmit={submit}>
        <div className="m4-toolbar-row">
          <div className="field-group m4-search-field">
            <label htmlFor="m4-search-query">{t('m5s5.search.label')}</label>
            <input
              id="m4-search-query"
              type="search"
              value={draftQuery}
              onChange={(event) => setDraftQuery(event.currentTarget.value)}
              placeholder={t('m5s5.search.placeholder')}
              autoComplete="off"
            />
          </div>
          <div className="field-group">
            <label htmlFor="m4-search-kind">{t('m5s5.search.typeLabel')}</label>
            <select
              id="m4-search-kind"
              value={kind}
              onChange={(event) =>
                setKind(event.currentTarget.value as SearchKind | '')
              }
            >
              <option value="">{t('m5s5.search.allTypes')}</option>
              {SEARCH_KINDS.map((candidate) => (
                <option key={candidate} value={candidate}>
                  {t(`m5s5.kind.${candidate}`)}
                </option>
              ))}
            </select>
          </div>
          <div className="m4-toolbar-submit">
            <button
              type="submit"
              disabled={!draftQuery.trim() || searchQuery.isFetching}
            >
              {searchQuery.isFetching && !searchQuery.isFetchingNextPage
                ? t('m5s5.search.searching')
                : t('m5s5.search.submit')}
            </button>
          </div>
        </div>
      </form>

      {!submittedQuery ? (
        <UiState
          kind="empty"
          title={t('m5s5.search.startTitle')}
          body={t('m5s5.search.startBody')}
        />
      ) : null}
      {searchQuery.isLoading ? (
        <UiState kind="loading" title={t('m5s5.search.searching')} />
      ) : null}
      {searchQuery.error ? (
        <ProblemState
          error={searchQuery.error}
          onRetry={() => void searchQuery.refetch()}
        />
      ) : null}
      {submittedQuery && searchQuery.data && items.length === 0 ? (
        <UiState
          kind="empty"
          title={t('m5s5.search.emptyTitle')}
          body={t('m5s5.search.emptyBody')}
        />
      ) : null}
      {items.length > 0 ? (
        <section className="m4-results" aria-live="polite">
          <h2 className="m4-results-heading">
            {t('m5s5.search.resultsHeading')}
          </h2>
          <ul className="m4-list layout-columns layout-columns-dense">
            {items.map((item) => (
              <SearchResultCard key={`${item.type}:${item.id}`} item={item} />
            ))}
          </ul>
          {searchQuery.hasNextPage ? (
            <button
              type="button"
              className="secondary"
              onClick={() => void searchQuery.fetchNextPage()}
              disabled={searchQuery.isFetchingNextPage}
            >
              {searchQuery.isFetchingNextPage
                ? t('m5s5.search.loadingMore')
                : t('m5s5.search.loadMore')}
            </button>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function ActivityCard({ item }: { item: ActivityItem }) {
  const { t } = useTranslation();
  const path = engagementTargetPath(item.targetType, item.targetId);

  return (
    <li className="m4-item">
      <div className="m4-item-heading">
        <h3>{t(`m5s5.activityKind.${item.kind}`)}</h3>
        <time className="m4-item-meta" dateTime={item.occurredAt.toISOString()}>
          {formatDateTime(item.occurredAt)}
        </time>
      </div>
      <div className="m4-item-actions">
        {path ? (
          <Link className="button-link secondary-link" to={path}>
            {t('m5s5.common.open')}
          </Link>
        ) : (
          <span className="m4-muted">{t('m5s5.common.noDirectLink')}</span>
        )}
      </div>
    </li>
  );
}

export function ActivityProductPage({
  apis,
  spaceId,
}: {
  apis: M4ProductApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const activityQuery = useInfiniteQuery({
    queryKey: ['m5-s5', 'activity', spaceId],
    queryFn: ({ pageParam }) =>
      apiCall(() =>
        apis.activity.getActivity({
          spaceId,
          cursor: pageParam,
          limit: PAGE_SIZE,
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: opaqueNextCursor,
    retry: false,
  });
  const items = activityQuery.data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <div className="page m4-product-page">
      <PageHeader
        eyebrow={t('m5s5.activity.eyebrow')}
        title={t('m5s5.activity.title')}
        description={t('m5s5.activity.intro')}
        action={
          <button
            type="button"
            className="secondary compact-action"
            onClick={() => void activityQuery.refetch()}
            disabled={activityQuery.isFetching}
          >
            {activityQuery.isFetching && !activityQuery.isFetchingNextPage
              ? t('m5s5.common.refreshing')
              : t('m5s5.common.refresh')}
          </button>
        }
      />
      {activityQuery.isLoading ? (
        <UiState kind="loading" title={t('states.loading.title')} />
      ) : null}
      {activityQuery.error ? (
        <ProblemState
          error={activityQuery.error}
          onRetry={() => void activityQuery.refetch()}
        />
      ) : null}
      {activityQuery.data && items.length === 0 ? (
        <UiState
          kind="empty"
          title={t('m5s5.activity.emptyTitle')}
          body={t('m5s5.activity.emptyBody')}
        />
      ) : null}
      {items.length > 0 ? (
        <section className="layout-panel" aria-live="polite">
          <ul className="m4-list m4-list-rows">
            {items.map((item) => (
              <ActivityCard key={item.id} item={item} />
            ))}
          </ul>
          {activityQuery.hasNextPage ? (
            <button
              type="button"
              className="secondary"
              onClick={() => void activityQuery.fetchNextPage()}
              disabled={activityQuery.isFetchingNextPage}
            >
              {activityQuery.isFetchingNextPage
                ? t('m5s5.activity.loadingMore')
                : t('m5s5.activity.loadMore')}
            </button>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function notificationTitle(item: NotificationItem, t: (key: string) => string) {
  if (item.kind === 'COMMENT_CREATED') {
    return t('m5s5.notificationKind.COMMENT_CREATED');
  }
  return t('m5s5.notificationKind.generic');
}

export function NotificationsProductPage({
  apis,
  spaceId,
}: {
  apis: M4ProductApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const listKey = ['m5-s5', 'notifications', spaceId] as const;
  const unreadKey = ['m5-s5', 'notification-unread-count', spaceId] as const;

  const notificationsQuery = useInfiniteQuery({
    queryKey: listKey,
    queryFn: ({ pageParam }) =>
      apiCall(() =>
        apis.notifications.getNotifications({
          spaceId,
          cursor: pageParam,
          limit: PAGE_SIZE,
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: opaqueNextCursor,
    retry: false,
  });
  const unreadQuery = useQuery({
    queryKey: unreadKey,
    queryFn: () =>
      apiCall(() => apis.notifications.getNotificationUnreadCount({ spaceId })),
    retry: false,
  });

  async function refreshNotifications() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: listKey }),
      queryClient.invalidateQueries({ queryKey: unreadKey }),
    ]);
  }

  const markOne = useMutation({
    mutationFn: (notificationId: string) =>
      apiCall(() =>
        apis.notifications.markNotificationRead({ notificationId, spaceId }),
      ),
    onSuccess: refreshNotifications,
  });
  const markAll = useMutation({
    mutationFn: () =>
      apiCall(() => apis.notifications.markAllNotificationsRead({ spaceId })),
    onSuccess: refreshNotifications,
  });

  const items =
    notificationsQuery.data?.pages.flatMap((page) => page.items) ?? [];
  const unreadCount = unreadQuery.data?.unreadCount ?? 0;

  return (
    <div className="page m4-product-page">
      <PageHeader
        eyebrow={t('m5s5.notifications.eyebrow')}
        title={t('m5s5.notifications.title')}
        description={t('m5s5.notifications.intro')}
        action={
          <button
            type="button"
            className="secondary compact-action"
            onClick={() => {
              void notificationsQuery.refetch();
              void unreadQuery.refetch();
            }}
            disabled={notificationsQuery.isFetching || unreadQuery.isFetching}
          >
            {notificationsQuery.isFetching || unreadQuery.isFetching
              ? t('m5s5.common.refreshing')
              : t('m5s5.common.refresh')}
          </button>
        }
      />

      <section
        className="layout-panel layout-panel-quiet"
        aria-labelledby="m4-notification-summary"
      >
        <div className="m4-notification-summary">
          <h2
            id="m4-notification-summary"
            className="m4-unread-badge"
            aria-live="polite"
          >
            {t('m5s5.notifications.unreadCount', { count: unreadCount })}
          </h2>
          <button
            type="button"
            className="secondary"
            onClick={() => markAll.mutate()}
            disabled={markAll.isPending || unreadCount === 0}
          >
            {markAll.isPending
              ? t('m5s5.notifications.markingAllRead')
              : t('m5s5.notifications.markAllRead')}
          </button>
        </div>
      </section>

      {notificationsQuery.isLoading || unreadQuery.isLoading ? (
        <UiState kind="loading" title={t('states.loading.title')} />
      ) : null}
      {notificationsQuery.error ? (
        <ProblemState
          error={notificationsQuery.error}
          onRetry={() => void notificationsQuery.refetch()}
        />
      ) : null}
      {unreadQuery.error ? (
        <ProblemState
          error={unreadQuery.error}
          onRetry={() => void unreadQuery.refetch()}
        />
      ) : null}
      {markOne.error ? <ProblemState error={markOne.error} /> : null}
      {markAll.error ? <ProblemState error={markAll.error} /> : null}

      {notificationsQuery.data && items.length === 0 ? (
        <UiState
          kind="empty"
          title={t('m5s5.notifications.emptyTitle')}
          body={t('m5s5.notifications.emptyBody')}
        />
      ) : null}

      {items.length > 0 ? (
        <section className="layout-panel" aria-live="polite">
          <ul className="m4-list m4-list-rows">
            {items.map((item) => {
              const path = engagementTargetPath(item.targetType, item.targetId);
              const markingThis =
                markOne.isPending && markOne.variables === item.id;
              return (
                <li
                  className={`m4-item${item.readAt ? '' : ' m4-item-unread'}`}
                  key={item.id}
                >
                  <div className="m4-item-heading">
                    <h3>{notificationTitle(item, t)}</h3>
                    <span className="m4-item-kind">
                      {item.readAt
                        ? t('m5s5.notifications.read')
                        : t('m5s5.notifications.unread')}
                    </span>
                  </div>
                  <time
                    className="m4-item-meta"
                    dateTime={item.createdAt.toISOString()}
                  >
                    {formatDateTime(item.createdAt)}
                  </time>
                  <div className="m4-item-actions">
                    {path ? (
                      <Link className="button-link secondary-link" to={path}>
                        {t('m5s5.common.open')}
                      </Link>
                    ) : null}
                    {!item.readAt ? (
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => markOne.mutate(item.id)}
                        disabled={markOne.isPending}
                      >
                        {markingThis
                          ? t('m5s5.notifications.markingRead')
                          : t('m5s5.notifications.markRead')}
                      </button>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
          {notificationsQuery.hasNextPage ? (
            <button
              type="button"
              className="secondary"
              onClick={() => void notificationsQuery.fetchNextPage()}
              disabled={notificationsQuery.isFetchingNextPage}
            >
              {notificationsQuery.isFetchingNextPage
                ? t('m5s5.notifications.loadingMore')
                : t('m5s5.notifications.loadMore')}
            </button>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
