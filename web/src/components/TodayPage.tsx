import { useRef } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import type { AccountView } from '../api/generated/models/AccountView';
import type { ActivityItem } from '../api/generated/models/ActivityItem';
import type { DashboardItem } from '../api/generated/models/DashboardItem';
import type { DashboardItemType } from '../api/generated/models/DashboardItemType';
import type { DashboardRelationshipDuration } from '../api/generated/models/DashboardRelationshipDuration';
import { DurationDisplayMode } from '../api/generated/models/DurationDisplayMode';
import type { ProfilesApi } from '../api/generated/apis/ProfilesApi';
import {
  type M4ProductApis,
  dashboardItemPath,
  engagementTargetPath,
} from '../client/m4Product';
import { dashboardQueryKey } from '../client/dashboardQueries';
import { formatRecency, formatUpcomingRelative } from '../client/formatRecency';
import { normalizeClientError } from '../client/problemDetails';
import { ACTIVITY_ROUTE } from '../client/routes';
import { postSnackbar } from '../client/snackbar';
import { useProfileAvatarUrl } from '../client/useProfileAvatarUrl';
import { resolvedLocale, useTranslation } from '../i18n';
import { CouplePresence } from './CouplePresence';
import { MemoryPreview } from './MemoryPreview';
import { PersonIdentity } from './PersonIdentity';
import { ProblemState } from './ProblemState';
import { ThinkingOfYouButton } from './ThinkingOfYouButton';
import { UiState } from './UiState';
import './TodayPage.css';
import './TodayPageB2.css';

export function formatRelationshipDuration(
  duration: DashboardRelationshipDuration,
  t: (key: string, options?: Record<string, unknown>) => string,
): string {
  if (duration.displayMode !== DurationDisplayMode.YEARS_MONTHS) {
    if (duration.daysTogether === 1) {
      return t('m5s5.dashboard.durationDaysOne', {
        defaultValue: '1 Tag zusammen',
      });
    }
    return t('m5s5.dashboard.durationDays', {
      count: duration.daysTogether,
    });
  }

  const start = new Date(duration.startedOn);
  const end = new Date(start.getTime() + duration.daysTogether * 86_400_000);

  let years = end.getUTCFullYear() - start.getUTCFullYear();
  let months = end.getUTCMonth() - start.getUTCMonth();
  const days = end.getUTCDate() - start.getUTCDate();

  if (days < 0) months -= 1;
  if (months < 0) {
    years -= 1;
    months += 12;
  }
  years = Math.max(0, years);
  months = Math.max(0, months);

  const yearsLabel =
    years === 1
      ? t('m5s5.dashboard.yearOne', { defaultValue: 'Jahr' })
      : t('m5s5.dashboard.yearMany', { defaultValue: 'Jahre' });
  const monthsLabel =
    months === 1
      ? t('m5s5.dashboard.monthOne', { defaultValue: 'Monat' })
      : t('m5s5.dashboard.monthMany', { defaultValue: 'Monate' });

  if (years > 0 && months > 0) {
    return t('m5s5.dashboard.durationYearsMonths', {
      years,
      yearsLabel,
      months,
      monthsLabel,
      defaultValue: `${years} ${yearsLabel}, ${months} ${monthsLabel} zusammen`,
    });
  }
  if (years > 0) {
    return t('m5s5.dashboard.durationYearsOnly', {
      years,
      yearsLabel,
      defaultValue: `${years} ${yearsLabel} zusammen`,
    });
  }
  if (months > 0) {
    return t('m5s5.dashboard.durationMonthsOnly', {
      months,
      monthsLabel,
      defaultValue: `${months} ${monthsLabel} zusammen`,
    });
  }
  if (duration.daysTogether === 1) {
    return t('m5s5.dashboard.durationDaysOne', {
      defaultValue: '1 Tag zusammen',
    });
  }
  return t('m5s5.dashboard.durationDays', { count: duration.daysTogether });
}

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

export type TodayCardVariant =
  | 'upcoming'
  | 'recent'
  | 'retrospective'
  | 'keepsake';

export type TodayPresentationRole =
  | 'hero'
  | 'primary_context'
  | 'relationship_signal'
  | 'shared_content'
  | 'editorial_highlight';

export function TodayModuleSection({
  id,
  className,
  title,
  kicker,
  subline,
  headerAction,
  children,
  animationDelay,
}: {
  id?: string;
  className?: string;
  title: string;
  kicker?: string;
  subline?: string;
  headerAction?: React.ReactNode;
  children: React.ReactNode;
  animationDelay?: string;
}) {
  return (
    <section
      id={id}
      className={`today-section ${className ?? ''} sbs-motion-reveal`}
      style={animationDelay ? { animationDelay } : undefined}
    >
      <div className="today-section-header">
        <div>
          {kicker ? (
            <span className="today-section-kicker">{kicker}</span>
          ) : null}
          <h2 className="today-section-title">{title}</h2>
          {subline ? <p className="today-section-subline">{subline}</p> : null}
        </div>
        {headerAction ? (
          <div className="today-section-action">{headerAction}</div>
        ) : null}
      </div>
      <div className="today-section-body">{children}</div>
    </section>
  );
}

function RecentItemTypeIcon({ type }: { type: DashboardItemType }) {
  if (type === 'HEART_MOMENT' || type === 'ANNIVERSARY') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="recent-type-icon">
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
      </svg>
    );
  }

  if (
    type === 'PLAN' ||
    type === 'IMPORTANT_DATE' ||
    type === 'BIRTHDAY'
  ) {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="recent-type-icon">
        <rect x="3" y="4" width="18" height="18" rx="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>
    );
  }

  if (type === 'PLACE') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="recent-type-icon">
        <path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8zm0 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="recent-type-icon">
      <rect x="3" y="3" width="18" height="18" rx="4" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <path d="m21 15-5-5L5 21" />
    </svg>
  );
}

function TodayContextualCard({ item }: { item: DashboardItem }) {
  const { t } = useTranslation();
  const path = dashboardItemPath(item.type, item.id);
  const rawDate = item.occurredOn ?? item.scheduledAt ?? item.createdAt;
  const date = rawDate ? formatUpcomingRelative(rawDate, t) : null;

  const kicker =
    item.type === 'PLAN'
      ? t('m5s5.today.contextSlot.upcomingPlanKicker')
      : item.type === 'IMPORTANT_DATE' ||
          item.type === 'BIRTHDAY' ||
          item.type === 'ANNIVERSARY'
        ? t('m5s5.today.contextSlot.importantDateKicker')
        : t('m5s5.today.contextSlot.kicker');

  const content = (
    <div className="today-context-card sbs-motion-lift">
      <div className="today-context-header">
        <span className="today-context-kicker">{kicker}</span>
        <span className={`today-card-kind today-kind-${item.type.toLowerCase()}`}>
          <span className="today-type-icon" aria-hidden="true">
            <RecentItemTypeIcon type={item.type} />
          </span>
          <span>{t(`m5s5.kind.${item.type}`)}</span>
        </span>
      </div>
      <h2 className="today-context-title">
        {item.titleOrText || t('m5s5.dashboard.itemFallback')}
      </h2>
      <div className="today-context-footer">
        {date ? <span className="today-context-date">{date}</span> : null}
        {path ? (
          <span className="today-context-action">
            {t('m5s5.today.contextSlot.viewDetails')} →
          </span>
        ) : null}
      </div>
    </div>
  );

  if (path) {
    return (
      <Link to={path} className="today-context-link">
        {content}
      </Link>
    );
  }
  return content;
}

function TodayRelationshipSignalCard({
  partnerName,
  activityItem,
  partnerAvatarUrl,
}: {
  partnerName: string;
  activityItem: ActivityItem;
  partnerAvatarUrl?: string | null;
}) {
  const { t } = useTranslation();
  const path = engagementTargetPath(
    activityItem.targetType,
    activityItem.targetId,
  );
  const date = formatDate(activityItem.createdAt);
  const message =
    activityItem.targetType === 'MEMORY'
      ? t('m5s5.today.relationshipSignal.partnerCommentedMemory', {
          name: partnerName,
        })
      : t('m5s5.today.relationshipSignal.partnerCommentedGeneric', {
          name: partnerName,
        });

  return (
    <div className="today-signal-card sbs-motion-lift">
      <div className="today-signal-header">
        <span className="today-signal-kicker">
          {t('m5s5.today.relationshipSignal.kicker')}
        </span>
        <div className="today-signal-avatar" aria-hidden="true">
          <PersonIdentity
            displayName={partnerName}
            imageUrl={partnerAvatarUrl}
            size="small"
            showName={false}
            imageAlt={partnerName}
            fallbackAlt={partnerName}
          />
        </div>
      </div>
      <p className="today-signal-message">{message}</p>
      <div className="today-signal-footer">
        {date ? <span className="today-signal-date">{date}</span> : null}
        {path ? (
          <Link
            to={path}
            className="today-signal-action"
            aria-label={t('m5s5.today.relationshipSignal.ariaLabel', {
              name: partnerName,
            })}
          >
            {t('m5s5.today.relationshipSignal.viewAction')} →
          </Link>
        ) : null}
      </div>
    </div>
  );
}

function RecentSharedItemCard({ item }: { item: DashboardItem }) {
  const { t } = useTranslation();
  const path = dashboardItemPath(item.type, item.id);
  const rawDate = item.occurredOn ?? item.scheduledAt ?? item.createdAt;
  const recency = rawDate ? formatRecency(rawDate, t) : null;
  const typeLabel = t(`m5s5.kind.${item.type}`);
  const title = item.titleOrText || t('m5s5.dashboard.itemFallback');

  const cardInner = (
    <div className="recent-shared-card sbs-motion-lift">
      <div className="recent-shared-icon" aria-hidden="true">
        <RecentItemTypeIcon type={item.type} />
      </div>
      <div className="recent-shared-copy">
        <h3 className="recent-shared-title">{title}</h3>
        <div className="recent-shared-meta">
          <span className="recent-shared-kind">{typeLabel}</span>
          {recency ? (
            <>
              <span className="recent-shared-meta-sep" aria-hidden="true">
                ·
              </span>
              <time className="recent-shared-date" dateTime={rawDate?.toISOString()}>
                {recency}
              </time>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );

  if (path) {
    return (
      <Link to={path} className="recent-shared-card-link">
        {cardInner}
      </Link>
    );
  }
  return <div className="recent-shared-card-wrapper">{cardInner}</div>;
}

function VisualMemoryCard({
  item,
  variant,
  loadMemoryImage,
}: {
  item: DashboardItem;
  variant: TodayCardVariant;
  loadMemoryImage?: (memoryId: string, attachmentId: string) => Promise<string>;
}) {
  const { t } = useTranslation();
  const path = dashboardItemPath(item.type, item.id);
  const rawDate = item.occurredOn ?? item.scheduledAt ?? item.createdAt;
  const date = rawDate
    ? variant === 'upcoming'
      ? formatUpcomingRelative(rawDate, t)
      : formatDate(rawDate)
    : null;
  const previewAttachmentId = item.previewAttachmentId;
  const hasMedia = Boolean(previewAttachmentId && loadMemoryImage);
  const shellClass = `today-card-shell today-card-shell-${variant}${hasMedia ? ' today-card-shell-media' : ''}${path ? ' today-card-link' : ''}`;

  const inner = (
    <div
      className={`today-card today-card-${item.type.toLowerCase()} today-card-${variant} ${hasMedia ? 'today-card-has-media' : 'today-card-typography-first'} sbs-motion-lift`}
    >
      {hasMedia && previewAttachmentId && loadMemoryImage ? (
        <div className="today-card-media">
          <MemoryPreview
            memoryId={item.id}
            attachmentId={previewAttachmentId}
            loadImage={loadMemoryImage}
          />
        </div>
      ) : null}
      <div className="today-card-content">
        <div className="today-card-badges">
          <span className={`today-card-kind today-kind-${item.type.toLowerCase()}`}>
            <span className="today-type-icon" aria-hidden="true">
              <RecentItemTypeIcon type={item.type} />
            </span>
            <span>{t(`m5s5.kind.${item.type}`)}</span>
          </span>
          {variant === 'retrospective' ? (
            <span className="today-card-retrospective-badge">
              <svg
                viewBox="0 0 24 24"
                aria-hidden="true"
                className="retrospective-badge-icon"
                width="14"
                height="14"
                fill="currentColor"
              >
                <path d="M12 2l2.4 7.4h7.6l-6.1 4.5 2.3 7.1-6.2-4.5-6.2 4.5 2.3-7.1-6.1-4.5h7.6z" />
              </svg>
              <span>{t('m5s5.dashboard.retrospectiveTitle')}</span>
            </span>
          ) : null}
        </div>
        <h3 className="today-card-title">
          {item.titleOrText || t('m5s5.dashboard.itemFallback')}
        </h3>
        {date ? <span className="today-card-date">{date}</span> : null}
      </div>
    </div>
  );

  if (path) {
    return (
      <Link to={path} className={shellClass}>
        {inner}
      </Link>
    );
  }
  return <div className={shellClass}>{inner}</div>;
}

function ThinkingOfYouHero({
  apis,
  spaceId,
  partnerName,
}: {
  apis: M4ProductApis;
  spaceId: string;
  partnerName?: string;
}) {
  const clientRequestIdRef = useRef<string>('');
  const mutation = useMutation({
    mutationFn: () =>
      apiCall(() =>
        apis.notifications.sendThinkingOfYou({
          spaceId,
          thinkingOfYouCreate: { clientRequestId: clientRequestIdRef.current },
        }),
      ),
    onSuccess: () => postSnackbar('m5s5.dashboard.thinkingOfYouSent'),
    onError: () => postSnackbar('m5s5.common.error'),
  });

  const handleSend = async () => {
    clientRequestIdRef.current = crypto.randomUUID();
    await mutation.mutateAsync();
  };

  return (
    <ThinkingOfYouButton
      className="today-hero-action"
      partnerName={partnerName}
      disabled={mutation.isPending}
      onSend={handleSend}
    />
  );
}

export function TodayPage({
  apis,
  spaceId,
  loadMemoryImage,
  profilesApi,
  account,
}: {
  apis: M4ProductApis;
  spaceId: string;
  loadMemoryImage?: (memoryId: string, attachmentId: string) => Promise<string>;
  profilesApi?: ProfilesApi;
  account?: AccountView | null;
}) {
  const { t } = useTranslation();
  const dashboardQuery = useQuery({
    queryKey: dashboardQueryKey(spaceId),
    queryFn: () => apiCall(() => apis.dashboard.getDashboard({ spaceId })),
    retry: false,
  });
  const activityQuery = useQuery({
    queryKey: ['m4', 'activity', spaceId],
    queryFn: () => apiCall(() => apis.activity.getActivity({ spaceId, limit: 10 })),
    enabled: Boolean(apis?.activity && spaceId),
    retry: false,
  });

  const partner = dashboardQuery.data?.space.partner;
  const partnerName =
    partner?.displayName ?? t('m5s5.today.relationshipSignal.partnerFallback');

  const userProfileQuery = useQuery({
    queryKey: ['profile-identity', spaceId, account?.id],
    queryFn: () =>
      profilesApi && account
        ? profilesApi.getPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGet({
            accountId: account.id,
            spaceId,
          })
        : null,
    enabled: Boolean(profilesApi && account && spaceId),
    retry: false,
  });
  const partnerProfileQuery = useQuery({
    queryKey: ['profile-identity', spaceId, partner?.id],
    queryFn: () =>
      profilesApi && partner?.id
        ? profilesApi.getPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGet({
            accountId: partner.id,
            spaceId,
          })
        : null,
    enabled: Boolean(profilesApi && partner?.id && spaceId),
    retry: false,
  });

  const userAvatar = useProfileAvatarUrl(
    profilesApi,
    spaceId,
    account?.id ?? '',
    userProfileQuery.data?.profileAttachmentId,
  );
  const partnerAvatar = useProfileAvatarUrl(
    profilesApi,
    spaceId,
    partner?.id ?? '',
    partnerProfileQuery.data?.profileAttachmentId,
  );

  const upcoming = dashboardQuery.data?.upcoming ?? [];
  const primaryContextItem = upcoming.length > 0 ? upcoming[0] : null;
  const secondaryUpcoming = upcoming.length > 1 ? upcoming.slice(1) : [];

  const relationshipSignalItem =
    partner?.id != null
      ? activityQuery.data?.items?.find(
          (item) =>
            item.kind === 'COMMENT_CREATED' &&
            item.actorId != null &&
            item.actorId === partner.id,
        )
      : undefined;

  const hasContextModules = Boolean(primaryContextItem || relationshipSignalItem);
  const hasBothContextModules = Boolean(primaryContextItem && relationshipSignalItem);
  const recentShared = dashboardQuery.data?.recentShared ?? [];
  const retrospective = dashboardQuery.data?.retrospective;
  const visualRecentSharedItem =
    !retrospective && loadMemoryImage
      ? recentShared.find(
          (item) => item.type === 'MEMORY' && Boolean(item.previewAttachmentId),
        )
      : undefined;
  const recentSharedForTrace = visualRecentSharedItem
    ? recentShared.filter((item) => item.id !== visualRecentSharedItem.id)
    : recentShared;
  const isSparse = Boolean(
    dashboardQuery.data &&
      upcoming.length === 0 &&
      recentShared.length === 0 &&
      !retrospective &&
      !relationshipSignalItem,
  );

  return (
    <div className="page today-page">
      {dashboardQuery.isLoading ? (
        <UiState kind="loading" title={t('states.loading.title')} />
      ) : null}
      {dashboardQuery.error ? (
        <ProblemState
          error={dashboardQuery.error}
          onRetry={() => dashboardQuery.refetch()}
        />
      ) : null}

      {dashboardQuery.data ? (
        <div className="today-content">
          <CouplePresence
            className="today-hero sbs-motion-reveal"
            headingLevel="h1"
            spaceTitle={
              partner
                ? t('m5s5.dashboard.partner', { name: partner.displayName })
                : t('m5s5.dashboard.durationTitle')
            }
            primaryPerson={{
              displayName:
                account?.displayName ||
                t('m5s5.activity.you', { defaultValue: 'Du' }),
              imageUrl: userAvatar.avatarUrl,
            }}
            secondaryPerson={
              partner
                ? {
                    displayName: partner.displayName,
                    imageUrl: partnerAvatar.avatarUrl,
                  }
                : null
            }
            status={partner ? 'connected' : 'waiting'}
            relationshipDuration={
              dashboardQuery.data.relationshipDuration
                ? formatRelationshipDuration(
                    dashboardQuery.data.relationshipDuration,
                    t,
                  )
                : undefined
            }
            durationLinkTo={
              dashboardQuery.data.relationshipDuration
                ? '/more/profile#relationship-profile-title'
                : undefined
            }
            durationTitle={t('m5s5.dashboard.openRelationshipSettings')}
            actions={
              <div className="today-hero-action-container">
                <ThinkingOfYouHero
                  apis={apis}
                  spaceId={spaceId}
                  partnerName={partner?.displayName}
                />
              </div>
            }
          />

          {isSparse ? (
            <section className="new-space-experience sbs-motion-reveal">
              <div className="new-space-mark" aria-hidden="true">
                <span>e.</span>
              </div>
              <h1 className="new-space-title">
                {partner
                  ? t('m5s5.dashboard.newSpacePartner', {
                      name: partner.displayName,
                    })
                  : t('m5s5.dashboard.newSpaceEmpty')}
              </h1>
              <p className="new-space-body">{t('m5s5.dashboard.newSpaceIntro')}</p>
              <div className="new-space-actions">
                <Link className="button-link primary new-space-cta" to="/story/memories/new">
                  {t('m5s5.dashboard.newSpaceAction')}
                </Link>
              </div>
            </section>
          ) : (
            <>
              {retrospective ? (
                <TodayModuleSection
                  className="today-section-retrospective today-section-keepsake"
                  title={t('m5s5.dashboard.retrospectiveTitle')}
                  kicker={t('m5s5.today.roles.editorial')}
                  animationDelay="100ms"
                >
                  <div className="today-retrospective-container">
                    <VisualMemoryCard
                      item={retrospective}
                      variant="retrospective"
                      loadMemoryImage={loadMemoryImage}
                    />
                  </div>
                </TodayModuleSection>
              ) : visualRecentSharedItem ? (
                <TodayModuleSection
                  className="today-section-retrospective today-section-keepsake today-section-keepsake-recent"
                  title={t('m5s5.today.keepsake.recentTitle')}
                  kicker={t('m5s5.today.keepsake.kicker')}
                  animationDelay="100ms"
                >
                  <div className="today-retrospective-container">
                    <VisualMemoryCard
                      item={visualRecentSharedItem}
                      variant="keepsake"
                      loadMemoryImage={loadMemoryImage}
                    />
                  </div>
                </TodayModuleSection>
              ) : null}

              {hasContextModules ? (
                <div
                  className={`today-context-area ${
                    hasBothContextModules
                      ? 'today-context-dual'
                      : 'today-context-single'
                  } sbs-motion-reveal`}
                >
                  {primaryContextItem ? (
                    <TodayContextualCard item={primaryContextItem} />
                  ) : null}
                  {relationshipSignalItem ? (
                    <TodayRelationshipSignalCard
                      partnerName={partnerName}
                      activityItem={relationshipSignalItem}
                      partnerAvatarUrl={partnerAvatar.avatarUrl}
                    />
                  ) : null}
                </div>
              ) : null}

              {secondaryUpcoming.length > 0 ? (
                <TodayModuleSection
                  className="today-section-upcoming"
                  title={t('m5s5.dashboard.upcomingMoreTitle')}
                  animationDelay="150ms"
                >
                  <div className="today-stream today-stream-upcoming">
                    {secondaryUpcoming.map((item: DashboardItem) => (
                      <VisualMemoryCard
                        key={item.id}
                        item={item}
                        variant="upcoming"
                        loadMemoryImage={loadMemoryImage}
                      />
                    ))}
                  </div>
                </TodayModuleSection>
              ) : null}

              {recentSharedForTrace.length > 0 ? (
                <TodayModuleSection
                  className="today-section-recent"
                  title={t('m5s5.dashboard.recentTitle')}
                  kicker={t('m5s5.dashboard.recentKicker')}
                  subline={t('m5s5.dashboard.recentSubline')}
                  animationDelay="200ms"
                >
                  <div className="today-stream today-stream-recent">
                    {recentSharedForTrace.slice(0, 4).map((item: DashboardItem) => (
                      <RecentSharedItemCard key={item.id} item={item} />
                    ))}
                  </div>
                  <div className="today-recent-footer">
                    <Link to={ACTIVITY_ROUTE} className="today-recent-activity-link">
                      {t('m5s5.dashboard.allActivityAction')}
                    </Link>
                  </div>
                </TodayModuleSection>
              ) : null}
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}
