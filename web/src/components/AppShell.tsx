import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { NotificationsApi } from '../api/generated/apis/NotificationsApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { Configuration } from '../api/generated/runtime';
import { notificationUnreadCountQueryKey } from '../client/notificationQueries';
import {
  PRODUCT_CACHE_FALLBACK_EVENT,
  PRODUCT_CACHE_NETWORK_EVENT,
  type ProductCacheEventDetail,
} from '../client/productReadCache';
import { PUBLIC_START_ROUTE } from '../client/publicStart';
import {
  APP_ROUTES,
  DEFAULT_APP_ROUTE,
  MORE_NOTIFICATIONS_ROUTE,
  SEARCH_ROUTE,
  type AppRouteDefinition,
} from '../client/routes';
import { resolvedLocale, useTranslation } from '../i18n';
import { Brand } from './Brand';
import { DestinationIcon } from './DestinationIcon';
import { HeaderProfileMenu } from './HeaderProfileMenu';
import { QuickCreateMenu } from './QuickCreateMenu';
import { Snackbar } from './Snackbar';
import { ThemeControl } from './ThemeControl';

function NavigationLink({ route }: { route: AppRouteDefinition }) {
  const { t } = useTranslation();

  return (
    <NavLink
      to={route.path}
      end={route.end}
      className={({ isActive }) =>
        `shell-nav-link${isActive ? ' shell-nav-link-active' : ''}`
      }
    >
      <span className="shell-nav-icon">
        <DestinationIcon icon={route.icon} />
      </span>
      <span>{t(route.labelKey)}</span>
    </NavLink>
  );
}

function PrimaryNavigationLinks() {
  return (
    <>
      {APP_ROUTES.map((route) => (
        <NavigationLink key={route.id} route={route} />
      ))}
    </>
  );
}

function useOnlineStatus(): boolean {
  const [online, setOnline] = useState(() =>
    typeof navigator === 'undefined' ? true : navigator.onLine,
  );

  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    return () => {
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
    };
  }, []);

  return online;
}

function useCachedReadTimestamp(): string | null {
  const [cachedAt, setCachedAt] = useState<string | null>(null);

  useEffect(() => {
    const onFallback = (event: Event) => {
      const detail = (event as CustomEvent<ProductCacheEventDetail>).detail;
      if (detail?.refreshedAt) setCachedAt(detail.refreshedAt);
    };
    const onNetwork = () => setCachedAt(null);
    window.addEventListener(PRODUCT_CACHE_FALLBACK_EVENT, onFallback);
    window.addEventListener(PRODUCT_CACHE_NETWORK_EVENT, onNetwork);
    return () => {
      window.removeEventListener(PRODUCT_CACHE_FALLBACK_EVENT, onFallback);
      window.removeEventListener(PRODUCT_CACHE_NETWORK_EVENT, onNetwork);
    };
  }, []);

  return cachedAt;
}

export function AppShell({
  children,
  onLogout,
  apiBaseUrl,
  accessToken,
  account,
  spaceId,
  serverAdmin = false,
}: {
  children: ReactNode;
  onLogout: () => void;
  apiBaseUrl: string;
  accessToken: string;
  account: AccountView;
  spaceId: string;
  serverAdmin?: boolean;
}) {
  const { t } = useTranslation();
  const online = useOnlineStatus();
  const cachedAt = useCachedReadTimestamp();
  const cachedAtLabel = cachedAt
    ? new Intl.DateTimeFormat(resolvedLocale(), {
        dateStyle: 'medium',
        timeStyle: 'short',
      }).format(new Date(cachedAt))
    : null;

  function logout(): void {
    onLogout();
    window.location.assign(PUBLIC_START_ROUTE);
  }

  const location = useLocation();
  const isPrivateArea = location.pathname.startsWith('/more/private');

  useEffect(
    () => () => {
      document.body.classList.remove('theme-vault');
    },
    [],
  );

  const notificationsApi = useMemo(
    () =>
      new NotificationsApi(
        new Configuration({
          basePath: apiBaseUrl,
          accessToken,
        }),
      ),
    [apiBaseUrl, accessToken],
  );

  const unreadQuery = useQuery({
    queryKey: notificationUnreadCountQueryKey(spaceId),
    queryFn: () => notificationsApi.getNotificationUnreadCount({ spaceId }),
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    enabled: Boolean(spaceId && accessToken),
  });
  const unreadCount = unreadQuery.data?.unreadCount ?? 0;

  const bellAriaLabel =
    unreadCount > 0
      ? t('navigation.notificationsWithUnread', { count: unreadCount })
      : t('navigation.notifications');

  return (
    <div className="product-shell">
      <ThemeControl />
      <a className="skip-link" href="#main-content">
        {t('navigation.skipToContent')}
      </a>

      <header className="app-header product-topbar">
        <Brand to={DEFAULT_APP_ROUTE} ariaLabel={t('brand.homeAria')} />
        <div className="header-actions">
          <span
            className={`shared-context ${isPrivateArea ? 'private-context' : ''}`}
          >
            {isPrivateArea ? (
              <>
                <span aria-hidden="true">🔒</span>{' '}
                {t('privateArea.privacyLabel')}
              </>
            ) : (
              <>
                <span aria-hidden="true">♥</span> {t('header.sharedArea')}
              </>
            )}
          </span>
          <NavLink
            to={SEARCH_ROUTE}
            className={({ isActive }) =>
              `shell-utility-link${isActive ? ' shell-utility-link-active' : ''}`
            }
            aria-label={t('navigation.search')}
            title={t('navigation.search')}
          >
            <span className="shell-nav-icon" aria-hidden="true">
              <DestinationIcon icon="search" />
            </span>
          </NavLink>
          <NavLink
            to={MORE_NOTIFICATIONS_ROUTE}
            className={({ isActive }) =>
              `shell-utility-link${isActive ? ' shell-utility-link-active' : ''}`
            }
            aria-label={bellAriaLabel}
            title={bellAriaLabel}
          >
            <span className="shell-nav-icon" aria-hidden="true">
              <DestinationIcon icon="notifications" />
              {unreadCount > 0 ? (
                <span className="notification-dot" aria-hidden="true" />
              ) : null}
            </span>
          </NavLink>
          <HeaderProfileMenu
            apiBaseUrl={apiBaseUrl}
            accessToken={accessToken}
            account={account}
            spaceId={spaceId}
            serverAdmin={serverAdmin}
            onLogout={logout}
          />
        </div>
      </header>

      {cachedAtLabel ? (
        <div className="offline-banner" role="status">
          <span aria-hidden="true">↯</span>
          <span>
            {t('cacheRuntime.cachedBanner', { timestamp: cachedAtLabel })}
          </span>
        </div>
      ) : !online ? (
        <div className="offline-banner" role="status">
          <span aria-hidden="true">↯</span>
          <span>{t('states.offline.banner')}</span>
        </div>
      ) : null}

      <div className="product-shell-body">
        <aside className="shell-sidebar">
          <div className="shell-sidebar-inner">
            <div className="shell-primary-action">
              <QuickCreateMenu variant="desktop" />
            </div>
            <nav className="shell-nav" aria-label={t('navigation.primary')}>
              <PrimaryNavigationLinks />
            </nav>
          </div>
        </aside>

        <main
          key={location.pathname}
          id="main-content"
          className="product-main sbs-motion-reveal"
          tabIndex={-1}
        >
          {children}
        </main>
      </div>

      <div className="mobile-quick-create">
        <QuickCreateMenu variant="mobile" />
      </div>

      <nav className="mobile-bottom-nav" aria-label={t('navigation.primary')}>
        <PrimaryNavigationLinks />
      </nav>

      <Snackbar />
    </div>
  );
}
