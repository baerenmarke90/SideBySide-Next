import { useEffect, useState, type ReactNode } from 'react';
import { Link, NavLink } from 'react-router-dom';
import {
  PRODUCT_CACHE_FALLBACK_EVENT,
  PRODUCT_CACHE_NETWORK_EVENT,
  type ProductCacheEventDetail,
} from '../client/productReadCache';
import {
  APP_ROUTES,
  DEFAULT_APP_ROUTE,
  MEMORY_CREATE_ROUTE,
  SEARCH_ROUTE,
  type AppRouteDefinition,
} from '../client/routes';
import { resolvedLocale, useTranslation } from '../i18n';
import { Brand } from './Brand';
import { DestinationIcon } from './DestinationIcon';
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
}: {
  children: ReactNode;
  onLogout: () => void;
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
    if (import.meta.env.VITE_SBS_DEMO_MODE === 'true') {
      window.location.assign('/');
    }
  }

  return (
    <div className="product-shell">
      <a className="skip-link" href="#main-content">
        {t('navigation.skipToContent')}
      </a>

      <header className="app-header product-topbar">
        <Brand to={DEFAULT_APP_ROUTE} ariaLabel={t('brand.homeAria')} />
        <div className="header-actions">
          <NavLink
            to={SEARCH_ROUTE}
            className={({ isActive }) =>
              `shell-search-link${isActive ? ' shell-search-link-active' : ''}`
            }
          >
            <span className="shell-nav-icon" aria-hidden="true">
              <DestinationIcon icon="search" />
            </span>
            <span>{t('navigation.search')}</span>
          </NavLink>
          <span className="shared-context">
            <span aria-hidden="true">♥</span> {t('header.sharedArea')}
          </span>
          <ThemeControl variant="inline" />
          <button type="button" className="tertiary" onClick={logout}>
            {t('header.logout')}
          </button>
        </div>
      </header>

      {cachedAtLabel ? (
        <div className="offline-banner" role="status">
          <span aria-hidden="true">↯</span>
          <span>{t('cacheRuntime.cachedBanner', { timestamp: cachedAtLabel })}</span>
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
              <Link className="button-link" to={MEMORY_CREATE_ROUTE}>
                <span className="shell-nav-icon">
                  <DestinationIcon icon="add" />
                </span>
                <span>{t('navigation.newMemory')}</span>
              </Link>
            </div>
            <nav className="shell-nav" aria-label={t('navigation.primary')}>
              <PrimaryNavigationLinks />
            </nav>
          </div>
        </aside>

        <main id="main-content" className="product-main" tabIndex={-1}>
          {children}
        </main>
      </div>

      <nav className="mobile-bottom-nav" aria-label={t('navigation.primary')}>
        <PrimaryNavigationLinks />
      </nav>
    </div>
  );
}
