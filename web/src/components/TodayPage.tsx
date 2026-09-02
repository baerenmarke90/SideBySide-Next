import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import type { DashboardItem } from '../api/generated/models/DashboardItem';
import { type M4ProductApis } from '../client/m4Product';
import { resolvedLocale, useTranslation } from '../i18n';
import { postSnackbar } from '../client/snackbar';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';
import { useState } from 'react';
import { MemoryPreview } from './MemoryPreview';
import { normalizeClientError } from '../client/problemDetails';
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

function dashboardItemPath(type: string, id: string): string | null {
  switch (type) {
    case 'Memory':
      return `/memory/${id}`;
    case 'Plan':
      return `/plan/${id}`;
    case 'Wish':
      return `/wish/${id}`;
    case 'Place':
      return `/place/${id}`;
    case 'Milestone':
      return `/milestone/${id}`;
    case 'HeartMoment':
      return `/heart/${id}`;
    default:
      return null;
  }
}

function VisualMemoryCard({ item }: { item: DashboardItem }) {
  const { t } = useTranslation();
  const path = dashboardItemPath(item.type, item.id);
  const date = formatDate(item.occurredOn) ?? formatDate(item.scheduledAt) ?? formatDate(item.createdAt);

  const inner = (
    <div className={`today-card today-card-${item.type.toLowerCase()} sbs-motion-lift`}>
      <div className="today-card-content">
        <span className="today-card-kind">{t(`m5s5.kind.${item.type}`)}</span>
        <h3 className="today-card-title">{item.titleOrText || t('m5s5.dashboard.itemFallback')}</h3>
        {date && <span className="today-card-date">{date}</span>}
      </div>
    </div>
  );

  if (path) {
    return <Link to={path} className="today-card-link">{inner}</Link>;
  }
  return inner;
}

function ThinkingOfYouHero() {
  const { t } = useTranslation();
  const [active, setActive] = useState(false);

  function handleClick() {
    if (active) return;
    setActive(true);
    postSnackbar('m5s5.dashboard.thinkingOfYouSent');
    setTimeout(() => setActive(false), 2500);
  }

  return (
    <button
      type="button"
      className={`today-hero-action ${active ? 'sbs-motion-success active' : 'sbs-motion-lift'}`}
      onClick={handleClick}
      aria-label={t('m5s5.dashboard.thinkingOfYouButton')}
    >
      <span className="today-hero-icon" aria-hidden="true">
        {active ? '✨' : '❤️'}
      </span>
      <span className="today-hero-text">
        {active ? t('m5s5.dashboard.thinkingOfYouSent') : t('m5s5.dashboard.thinkingOfYouButton')}
      </span>
    </button>
  );
}

export function TodayPage({
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
    <div className="page today-page">
      {dashboardQuery.isLoading && <UiState kind="loading" title={t('states.loading.title')} />}
      {dashboardQuery.error && <ProblemState error={dashboardQuery.error} onRetry={() => dashboardQuery.refetch()} />}
      
      {dashboardQuery.data && (
        <div className="today-content">
          <header className="today-hero sbs-motion-reveal">
            <h1 className="today-hero-greeting">
              {dashboardQuery.data.space.partner
                ? t('m5s5.dashboard.partner', { name: dashboardQuery.data.space.partner.displayName })
                : t('m5s5.dashboard.durationTitle')}
            </h1>
            <p className="today-hero-subtitle">
              {dashboardQuery.data.relationshipDuration
                ? t('m5s5.dashboard.durationDays', { count: dashboardQuery.data.relationshipDuration.daysTogether })
                : t('m5s5.dashboard.durationEmpty')}
            </p>
            <ThinkingOfYouHero />
          </header>

          <section className="today-section sbs-motion-reveal" style={{ animationDelay: '100ms' }}>
            <h2 className="today-section-title">{t('m5s5.dashboard.upcomingTitle')}</h2>
            <div className="today-stream">
              {dashboardQuery.data.upcoming.length > 0 ? (
                dashboardQuery.data.upcoming.map((item: DashboardItem) => <VisualMemoryCard key={item.id} item={item} />)
              ) : (
                <p className="today-empty">{t('m5s5.dashboard.upcomingEmpty')}</p>
              )}
            </div>
          </section>

          <section className="today-section sbs-motion-reveal" style={{ animationDelay: '200ms' }}>
            <h2 className="today-section-title">{t('m5s5.dashboard.recentTitle')}</h2>
            <div className="today-stream">
              {dashboardQuery.data.recentShared.length > 0 ? (
                dashboardQuery.data.recentShared.map((item: DashboardItem) => <VisualMemoryCard key={item.id} item={item} />)
              ) : (
                <p className="today-empty">{t('m5s5.dashboard.recentEmpty')}</p>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
