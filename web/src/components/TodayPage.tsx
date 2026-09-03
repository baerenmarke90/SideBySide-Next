import { useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import type { ActivityItem } from '../api/generated/models/ActivityItem';
import type { DashboardItem } from '../api/generated/models/DashboardItem';
import {
  type M4ProductApis,
  dashboardItemPath,
  engagementTargetPath,
} from '../client/m4Product';
import { normalizeClientError } from '../client/problemDetails';
import { postSnackbar } from '../client/snackbar';
import { resolvedLocale, useTranslation } from '../i18n';
import { MemoryPreview } from './MemoryPreview';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import './TodayPage.css';

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

export type TodayCardVariant = 'upcoming' | 'recent' | 'retrospective';

/**
 * Presentation roles for modules composed on the Today orchestration surface.
 * Rather than equal-sized dashboard widgets, each role fulfills an intentional
 * relationship purpose.
 */
export type TodayPresentationRole =
  | 'hero' // Stable couple presence & emotional anchor
  | 'primary_context' // 0-1 current relevant action/item (e.g. today's plan or due reminder)
  | 'relationship_signal' // 0-1 partner interaction signal (e.g. partner commented on memory)
  | 'shared_content' // Recent shared relationship moments
  | 'editorial_highlight'; // Retrospective discovery (e.g. "Weißt du noch?")

export function TodayModuleSection({
  id,
  className,
  title,
  kicker,
  headerAction,
  children,
  animationDelay,
}: {
  id?: string;
  className?: string;
  title: string;
  kicker?: string;
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
        </div>
        {headerAction ? (
          <div className="today-section-action">{headerAction}</div>
        ) : null}
      </div>
      <div className="today-section-body">{children}</div>
    </section>
  );
}

function TodayContextualCard({ item }: { item: DashboardItem }) {
  const { t } = useTranslation();
  const path = dashboardItemPath(item.type, item.id);
  const date =
    formatDate(item.occurredOn) ??
    formatDate(item.scheduledAt) ??
    formatDate(item.createdAt);

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
        <span className="today-card-kind">
          {item.type === 'HEART_MOMENT'
            ? '♥ '
            : item.type === 'MILESTONE'
              ? '★ '
              : ''}
          {t(`m5s5.kind.${item.type}`)}
        </span>
      </div>
      <h3 className="today-context-title">
        {item.titleOrText || t('m5s5.dashboard.itemFallback')}
      </h3>
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
}: {
  partnerName: string;
  activityItem: ActivityItem;
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
        <span className="today-signal-badge" aria-hidden="true">
          💬
        </span>
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
  const date =
    formatDate(item.occurredOn) ??
    formatDate(item.scheduledAt) ??
    formatDate(item.createdAt);

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
          <span className="today-card-kind">
            {item.type === 'HEART_MOMENT'
              ? '♥ '
              : item.type === 'MILESTONE'
                ? '★ '
                : ''}
            {t(`m5s5.kind.${item.type}`)}
          </span>
          {variant === 'retrospective' ? (
            <span className="today-card-retrospective-badge">
              ✨ {t('m5s5.dashboard.retrospectiveTitle')}
            </span>
          ) : null}
        </div>
        <h3 className="today-card-title">
          {item.titleOrText || t('m5s5.dashboard.itemFallback')}
        </h3>
        {date && <span className="today-card-date">{date}</span>}
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
}: {
  apis: M4ProductApis;
  spaceId: string;
}) {
  const { t } = useTranslation();
  const [active, setActive] = useState(false);
  const clientRequestIdRef = useRef<string>('');

  const mutation = useMutation({
    mutationFn: () =>
      apiCall(() =>
        apis.notifications.sendThinkingOfYou({
          spaceId,
          thinkingOfYouCreate: { clientRequestId: clientRequestIdRef.current },
        }),
      ),
    onSuccess: () => {
      setActive(true);
      postSnackbar('m5s5.dashboard.thinkingOfYouSent');
      setTimeout(() => setActive(false), 2500);
    },
    onError: () => {
      postSnackbar('m5s5.common.error');
    },
  });

  function handleClick() {
    if (active || mutation.isPending) return;
    clientRequestIdRef.current = crypto.randomUUID();
    mutation.mutate();
  }

  return (
    <button
      type="button"
      className={`today-hero-action ${active ? 'sbs-motion-success active' : 'sbs-motion-lift'} ${mutation.isPending ? 'pending' : ''}`}
      onClick={handleClick}
      aria-label={t('m5s5.dashboard.thinkingOfYouButton')}
      aria-busy={mutation.isPending}
      disabled={mutation.isPending}
    >
      <span className="today-hero-icon" aria-hidden="true">
        {active ? '✨' : '❤️'}
      </span>
      <span className="today-hero-text">
        {active
          ? t('m5s5.dashboard.thinkingOfYouSent')
          : t('m5s5.dashboard.thinkingOfYouButton')}
      </span>
    </button>
  );
}

export function TodayPage({
  apis,
  spaceId,
  loadMemoryImage,
}: {
  apis: M4ProductApis;
  spaceId: string;
  loadMemoryImage?: (memoryId: string, attachmentId: string) => Promise<string>;
}) {
  const { t } = useTranslation();
  const dashboardQuery = useQuery({
    queryKey: ['m5-s5', 'dashboard', spaceId],
    queryFn: () => apiCall(() => apis.dashboard.getDashboard({ spaceId })),
    retry: false,
  });

  const activityQuery = useQuery({
    queryKey: ['m4', 'activity', spaceId],
    queryFn: () =>
      apiCall(() => apis.activity.getActivity({ spaceId, limit: 10 })),
    enabled: Boolean(apis?.activity && spaceId),
    retry: false,
  });

  const partner = dashboardQuery.data?.space.partner;
  const partnerName =
    partner?.displayName ?? t('m5s5.today.relationshipSignal.partnerFallback');

  // 1. Primary Contextual Slot (0 or 1 item):
  // Deterministically selects the earliest upcoming item. If empty, the slot disappears.
  const upcoming = dashboardQuery.data?.upcoming ?? [];
  const primaryContextItem = upcoming.length > 0 ? upcoming[0] : null;
  const secondaryUpcoming = upcoming.length > 1 ? upcoming.slice(1) : [];

  // 2. Relationship Signal Slot (0 or 1 item):
  // Curated partner interaction (e.g. partner commented on a shared memory).
  // Only attributes genuine partner comments: actorId must match partner.id.
  // Disappears completely if no partner interaction occurred or there is no partner.
  const relationshipSignalItem =
    partner?.id != null
      ? activityQuery.data?.items?.find(
          (item) =>
            item.kind === 'COMMENT_CREATED' &&
            item.actorId != null &&
            item.actorId === partner.id,
        )
      : undefined;

  const hasContextModules = Boolean(
    primaryContextItem || relationshipSignalItem,
  );
  const hasBothContextModules = Boolean(
    primaryContextItem && relationshipSignalItem,
  );
  const recentShared = dashboardQuery.data?.recentShared ?? [];
  const retrospective = dashboardQuery.data?.retrospective;

  return (
    <div className="page today-page">
      {dashboardQuery.isLoading && (
        <UiState kind="loading" title={t('states.loading.title')} />
      )}
      {dashboardQuery.error && (
        <ProblemState
          error={dashboardQuery.error}
          onRetry={() => dashboardQuery.refetch()}
        />
      )}

      {dashboardQuery.data &&
        (dashboardQuery.data.upcoming.length === 0 &&
        dashboardQuery.data.recentShared.length === 0 &&
        !dashboardQuery.data.retrospective &&
        !relationshipSignalItem ? (
          <div className="new-space-experience sbs-motion-reveal">
            <div className="new-space-mark" aria-hidden="true">
              ❤️
            </div>
            <h1 className="new-space-title">
              {partner
                ? t('m5s5.dashboard.newSpacePartner', {
                    name: partner.displayName,
                  })
                : t('m5s5.dashboard.newSpaceEmpty')}
            </h1>
            <p className="new-space-body">
              {t('m5s5.dashboard.newSpaceIntro')}
            </p>
            <div className="new-space-actions">
              <Link
                className="button-link primary new-space-cta"
                to="/story/memories/new"
              >
                {t('m5s5.dashboard.newSpaceAction')}
              </Link>
            </div>
          </div>
        ) : (
          <div className="today-content">
            {/* ROLE: Hero / Couple Presence */}
            <header className="today-hero sbs-motion-reveal">
              <div className="today-hero-badge" aria-hidden="true">
                <span className="today-hero-badge-dot" />
                <span>{t('m5s5.dashboard.durationTitle')}</span>
              </div>
              <h1 className="today-hero-greeting">
                {partner
                  ? t('m5s5.dashboard.partner', {
                      name: partner.displayName,
                    })
                  : t('m5s5.dashboard.durationTitle')}
              </h1>
              <div className="today-hero-meta-row">
                {dashboardQuery.data.relationshipDuration ? (
                  <p className="today-hero-subtitle">
                    <span className="today-hero-pill-icon" aria-hidden="true">
                      ★
                    </span>
                    <span>
                      {t('m5s5.dashboard.durationDays', {
                        count:
                          dashboardQuery.data.relationshipDuration.daysTogether,
                      })}
                    </span>
                  </p>
                ) : null}
              </div>
              <div className="today-hero-action-container">
                <ThinkingOfYouHero apis={apis} spaceId={spaceId} />
              </div>
            </header>

            {/* ROLE: Context Area (0-1 Primary Contextual Module + 0-1 Relationship Signal) */}
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
                  />
                ) : null}
              </div>
            ) : null}

            {/* ROLE: Secondary Upcoming (rendered only when > 1 upcoming items exist to avoid duplicating the primary contextual item) */}
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

            {/* ROLE: Shared Story Content Area */}
            {recentShared.length > 0 ? (
              <TodayModuleSection
                className="today-section-recent"
                title={t('m5s5.dashboard.recentTitle')}
                kicker={t('m5s5.today.roles.sharedContent')}
                animationDelay="200ms"
              >
                <div className="today-stream today-stream-recent">
                  {recentShared.map((item: DashboardItem) => (
                    <VisualMemoryCard
                      key={item.id}
                      item={item}
                      variant="recent"
                      loadMemoryImage={loadMemoryImage}
                    />
                  ))}
                </div>
              </TodayModuleSection>
            ) : null}

            {/* ROLE: Editorial Retrospective Highlight */}
            {retrospective ? (
              <TodayModuleSection
                className="today-section-retrospective"
                title={t('m5s5.dashboard.retrospectiveTitle')}
                kicker={t('m5s5.today.roles.editorial')}
                animationDelay="300ms"
              >
                <div className="today-retrospective-container">
                  <VisualMemoryCard
                    item={retrospective}
                    variant="retrospective"
                    loadMemoryImage={loadMemoryImage}
                  />
                </div>
              </TodayModuleSection>
            ) : null}
          </div>
        ))}
    </div>
  );
}
