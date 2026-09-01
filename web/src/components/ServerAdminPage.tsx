import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import type { ServerAdminOverview } from '../api/generated/models/ServerAdminOverview';
import { PUBLIC_START_ROUTE } from '../client/publicStart';
import { DEFAULT_APP_ROUTE } from '../client/routes';
import { createServerAdminApis } from '../client/serverAdmin';
import { resolvedLocale, useTranslation } from '../i18n';
import { Brand } from './Brand';
import { ThemeControl } from './ThemeControl';
import { UiState } from './UiState';
import './ServerAdminPage.css';

export function ServerAdminAccessGate({
  loading,
  error,
  onRetry,
}: {
  loading: boolean;
  error: Error | null;
  onRetry: () => void;
}) {
  const { t } = useTranslation();

  return (
    <div className="server-admin-shell server-admin-gate-shell">
      <ThemeControl />
      <header className="server-admin-topbar">
        <Brand to={DEFAULT_APP_ROUTE} ariaLabel={t('brand.homeAria')} />
      </header>
      <main className="server-admin-main">
        <UiState
          kind={loading ? 'loading' : error ? 'error' : 'permission'}
          title={
            loading
              ? t('serverAdmin.access.loading')
              : error
                ? t('serverAdmin.access.errorTitle')
                : t('serverAdmin.access.deniedTitle')
          }
          body={
            error
              ? t('serverAdmin.access.errorBody')
              : loading
                ? undefined
                : t('serverAdmin.access.deniedBody')
          }
          action={
            <div className="server-admin-gate-actions">
              {error ? (
                <button type="button" onClick={onRetry}>
                  {t('serverAdmin.access.retry')}
                </button>
              ) : null}
              <Link
                className="button-link secondary-link"
                to={DEFAULT_APP_ROUTE}
              >
                {t('serverAdmin.backToApp')}
              </Link>
            </div>
          }
        />
      </main>
    </div>
  );
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat(resolvedLocale()).format(value);
}

function formatDate(value: Date | null): string | null {
  if (!value) return null;
  return new Intl.DateTimeFormat(resolvedLocale(), {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(value);
}

function formatBytes(value: number): string {
  if (value < 1024) return `${formatNumber(value)} B`;
  const units = ['KB', 'MB', 'GB', 'TB'];
  let amount = value / 1024;
  let unit = units[0];
  for (let index = 1; index < units.length && amount >= 1024; index += 1) {
    amount /= 1024;
    unit = units[index];
  }
  return `${new Intl.NumberFormat(resolvedLocale(), { maximumFractionDigits: 1 }).format(amount)} ${unit}`;
}

function healthLabel(status: string, t: (key: string) => string): string {
  switch (status) {
    case 'ok':
      return t('serverAdmin.health.ok');
    case 'unavailable':
      return t('serverAdmin.health.unavailable');
    case 'no_heartbeat_signal':
      return t('serverAdmin.health.noHeartbeat');
    case 'not_probed':
      return t('serverAdmin.health.notProbed');
    default:
      return t('serverAdmin.health.unknown');
  }
}

function StatusRow({ label, status }: { label: string; status: string }) {
  const { t } = useTranslation();
  const statusClass = status === 'ok' ? 'is-ok' : 'is-neutral';
  return (
    <div className="server-admin-status-row">
      <span>{label}</span>
      <span className={`server-admin-status ${statusClass}`}>
        {healthLabel(status, t)}
      </span>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="server-admin-metric">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function OverviewContent({ overview }: { overview: ServerAdminOverview }) {
  const { t } = useTranslation();
  const lastSuccessfulJob = formatDate(overview.lastSuccessfulJobAt);

  return (
    <>
      <section
        className="server-admin-panel"
        aria-labelledby="server-health-title"
      >
        <h2 id="server-health-title">{t('serverAdmin.health.title')}</h2>
        <div className="server-admin-status-list">
          <StatusRow
            label={t('serverAdmin.health.application')}
            status={overview.applicationStatus}
          />
          <StatusRow
            label={t('serverAdmin.health.database')}
            status={overview.databaseStatus}
          />
          <StatusRow
            label={t('serverAdmin.health.worker')}
            status={overview.workerStatus}
          />
          <StatusRow
            label={t('serverAdmin.health.media')}
            status={overview.mediaStatus}
          />
        </div>
      </section>

      <section
        className="server-admin-panel"
        aria-labelledby="server-usage-title"
      >
        <h2 id="server-usage-title">{t('serverAdmin.usage.title')}</h2>
        <dl className="server-admin-metrics">
          <Metric
            label={t('serverAdmin.usage.accounts')}
            value={formatNumber(overview.accountCount)}
          />
          <Metric
            label={t('serverAdmin.usage.spaces')}
            value={formatNumber(overview.activeSpaceCount)}
          />
          <Metric
            label={t('serverAdmin.usage.accounts24h')}
            value={formatNumber(overview.accountsLast24h)}
          />
          <Metric
            label={t('serverAdmin.usage.accounts7d')}
            value={formatNumber(overview.accountsLast7d)}
          />
          <Metric
            label={t('serverAdmin.usage.mediaObjects')}
            value={formatNumber(overview.mediaObjectCount)}
          />
          <Metric
            label={t('serverAdmin.usage.mediaBytes')}
            value={formatBytes(overview.mediaStoredBytes)}
          />
        </dl>
      </section>

      <section
        className="server-admin-panel"
        aria-labelledby="server-jobs-title"
      >
        <h2 id="server-jobs-title">{t('serverAdmin.jobs.title')}</h2>
        <dl className="server-admin-metrics server-admin-job-metrics">
          <Metric
            label={t('serverAdmin.jobs.pending')}
            value={formatNumber(overview.jobsPending)}
          />
          <Metric
            label={t('serverAdmin.jobs.running')}
            value={formatNumber(overview.jobsRunning)}
          />
          <Metric
            label={t('serverAdmin.jobs.failed')}
            value={formatNumber(overview.jobsFailed)}
          />
          <Metric
            label={t('serverAdmin.jobs.lastSuccess')}
            value={lastSuccessfulJob ?? t('serverAdmin.jobs.noSuccess')}
          />
        </dl>
        <h3>{t('serverAdmin.jobs.failuresTitle')}</h3>
        {overview.recentFailedJobs.length === 0 ? (
          <p className="server-admin-muted">
            {t('serverAdmin.jobs.noFailures')}
          </p>
        ) : (
          <div className="server-admin-table-scroll">
            <table className="server-admin-table">
              <thead>
                <tr>
                  <th scope="col">{t('serverAdmin.jobs.kind')}</th>
                  <th scope="col">{t('serverAdmin.jobs.attempts')}</th>
                  <th scope="col">{t('serverAdmin.jobs.finishedAt')}</th>
                </tr>
              </thead>
              <tbody>
                {overview.recentFailedJobs.map((job) => (
                  <tr key={job.id}>
                    <td>{job.kind}</td>
                    <td>
                      {formatNumber(job.attempts)} /{' '}
                      {formatNumber(job.maxAttempts)}
                    </td>
                    <td>{formatDate(job.finishedAt) ?? '–'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section
        className="server-admin-panel"
        aria-labelledby="server-configuration-title"
      >
        <h2 id="server-configuration-title">
          {t('serverAdmin.configuration.title')}
        </h2>
        <dl className="server-admin-config-list">
          <Metric
            label={t('serverAdmin.configuration.deployment')}
            value={overview.deployment}
          />
          <Metric
            label={t('serverAdmin.configuration.environment')}
            value={overview.environment}
          />
          <Metric
            label={t('serverAdmin.configuration.revision')}
            value={overview.buildRevision}
          />
          <Metric
            label={t('serverAdmin.configuration.startedAt')}
            value={formatDate(overview.processStartedAt) ?? '–'}
          />
          <Metric
            label={t('serverAdmin.configuration.publicBaseUrl')}
            value={overview.publicBaseUrl}
          />
          <Metric
            label={t('serverAdmin.configuration.mediaStore')}
            value={overview.mediaStore}
          />
          <Metric
            label={t('serverAdmin.configuration.mailTransport')}
            value={overview.mailTransport}
          />
          <Metric
            label={t('serverAdmin.configuration.oidcConnections')}
            value={formatNumber(overview.oidcConnectionCount)}
          />
          <Metric
            label={t('serverAdmin.configuration.databaseProvider')}
            value={overview.databaseProvider}
          />
          <Metric
            label={t('serverAdmin.configuration.demoMode')}
            value={t(
              overview.demoMode
                ? 'serverAdmin.configuration.enabled'
                : 'serverAdmin.configuration.disabled',
            )}
          />
        </dl>
      </section>
    </>
  );
}

export function ServerAdminPage({
  apiBaseUrl,
  accessToken,
  onLogout,
}: {
  apiBaseUrl: string;
  accessToken: string;
  onLogout: () => void;
}) {
  const { t } = useTranslation();
  const apis = useMemo(
    () => createServerAdminApis(apiBaseUrl, accessToken),
    [accessToken, apiBaseUrl],
  );
  const overviewQuery = useQuery({
    queryKey: ['server-admin', 'overview'],
    queryFn: () =>
      apis.serverAdmin.getServerAdminOverviewApiV1ServerAdminOverviewGet(),
    retry: false,
  });

  function logout() {
    onLogout();
    window.location.assign(PUBLIC_START_ROUTE);
  }

  return (
    <div className="server-admin-shell">
      <ThemeControl />
      <a className="skip-link" href="#server-admin-main">
        {t('navigation.skipToContent')}
      </a>
      <header className="server-admin-topbar">
        <Brand to={DEFAULT_APP_ROUTE} ariaLabel={t('brand.homeAria')} />
        <nav
          className="server-admin-topbar-actions"
          aria-label={t('serverAdmin.title')}
        >
          <Link className="secondary-link" to={DEFAULT_APP_ROUTE}>
            {t('serverAdmin.backToApp')}
          </Link>
          <button type="button" className="text-button" onClick={logout}>
            {t('serverAdmin.logout')}
          </button>
        </nav>
      </header>

      <main id="server-admin-main" className="server-admin-main" tabIndex={-1}>
        <div className="server-admin-heading-row">
          <div>
            <p className="eyebrow">{t('serverAdmin.eyebrow')}</p>
            <h1>{t('serverAdmin.title')}</h1>
            <p className="server-admin-intro">{t('serverAdmin.intro')}</p>
          </div>
          <button
            type="button"
            onClick={() => void overviewQuery.refetch()}
            disabled={overviewQuery.isFetching}
          >
            {t('serverAdmin.refresh')}
          </button>
        </div>

        {overviewQuery.isPending ? (
          <UiState
            kind="loading"
            title={t('serverAdmin.states.loadingTitle')}
            body={t('serverAdmin.states.loadingBody')}
          />
        ) : overviewQuery.error ? (
          <UiState
            kind="error"
            title={t('serverAdmin.states.errorTitle')}
            body={t('serverAdmin.states.errorBody')}
            action={
              <button
                type="button"
                onClick={() => void overviewQuery.refetch()}
              >
                {t('serverAdmin.refresh')}
              </button>
            }
          />
        ) : overviewQuery.data ? (
          <div className="server-admin-grid">
            <OverviewContent overview={overviewQuery.data} />
          </div>
        ) : null}

        <p className="server-admin-privacy-note">
          {t('serverAdmin.privacyNote')}
        </p>
      </main>
    </div>
  );
}
