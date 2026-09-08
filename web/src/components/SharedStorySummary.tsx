import type { DashboardSharedStorySummary } from '../api/generated/models/DashboardSharedStorySummary';
import { resolvedLocale, useTranslation } from '../i18n';
import './SharedStorySummary.css';

interface SharedStorySummaryProps {
  summary: DashboardSharedStorySummary;
}

export function sharedStorySummaryIsEligible(
  summary: DashboardSharedStorySummary,
): boolean {
  const values = [
    summary.memories,
    summary.heartMoments,
    summary.milestones,
  ].filter((value) => value > 0);
  return (
    values.length >= 2 && values.reduce((total, value) => total + value, 0) >= 5
  );
}

export function SharedStorySummary({ summary }: SharedStorySummaryProps) {
  const { t } = useTranslation();
  if (!sharedStorySummaryIsEligible(summary)) return null;

  const numberFormat = new Intl.NumberFormat(resolvedLocale());
  const metrics = [
    {
      key: 'memories',
      label: t('m5s5.dashboard.storySummaryMemories'),
      value: summary.memories,
    },
    {
      key: 'heartMoments',
      label: t('m5s5.dashboard.storySummaryHeartMoments'),
      value: summary.heartMoments,
    },
    {
      key: 'milestones',
      label: t('m5s5.dashboard.storySummaryMilestones'),
      value: summary.milestones,
    },
  ].filter((metric) => metric.value > 0);

  return (
    <section
      className="shared-story-summary"
      aria-labelledby="shared-story-summary-heading"
    >
      <h2 id="shared-story-summary-heading">
        {t('m5s5.dashboard.storySummaryTitle')}
      </h2>
      <dl className="shared-story-summary-values">
        {metrics.map((metric) => (
          <div className="shared-story-summary-metric" key={metric.key}>
            <dd>{numberFormat.format(metric.value)}</dd>
            <dt>{metric.label}</dt>
          </div>
        ))}
      </dl>
    </section>
  );
}
