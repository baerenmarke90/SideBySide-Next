import { useEffect, useState, type ReactNode } from 'react';
import { Link, NavLink } from 'react-router-dom';
import {
  APP_ROUTE_GROUPS,
  APP_ROUTES,
  appRoutePath,
  appRoutesInGroup,
  DEFAULT_APP_ROUTE,
  type AppRouteDefinition,
  type AppRouteIcon,
} from '../client/routes';
import { useTranslation } from '../i18n';
import { Brand } from './Brand';
import { ThemeControl } from './ThemeControl';

function NavigationIcon({ icon }: { icon: AppRouteIcon }) {
  if (icon === 'add') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 5v14M5 12h14" />
      </svg>
    );
  }

  if (icon === 'planning') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 5h12v15H6V5Zm3-2h6v4H9V3Zm0 8 2 2 4-4m-6 8h6" />
      </svg>
    );
  }

  if (icon === 'dashboard') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 4h6v6H4V4Zm10 0h6v6h-6V4ZM4 14h6v6H4v-6Zm10 0h6v6h-6v-6Z" />
      </svg>
    );
  }

  if (icon === 'search') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="11" cy="11" r="6" />
        <path d="m16 16 4 4" />
      </svg>
    );
  }

  if (icon === 'activity') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 7h14M5 12h14M5 17h9" />
        <circle cx="18" cy="17" r="2" />
      </svg>
    );
  }

  if (icon === 'notifications') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 17h12l-1.5-2.5V10a4.5 4.5 0 0 0-9 0v4.5L6 17Zm4 3h4" />
      </svg>
    );
  }

  if (icon === 'people') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm8 1a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5ZM3.5 19a4.5 4.5 0 0 1 9 0M13 19a3.5 3.5 0 0 1 7 0" />
      </svg>
    );
  }

  if (icon === 'profile') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 8a7 7 0 0 1 14 0" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 18V9.5L12 4l7 5.5V18a2 2 0 0 1-2 2h-3v-6h-4v6H7a2 2 0 0 1-2-2Z" />
    </svg>
  );
}

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
        <NavigationIcon icon={route.icon} />
      </span>
      <span>{t(route.labelKey)}</span>
    </NavLink>
  );
}

/** Compact navigation: every destination in one flat, thumb-reachable row. */
function CompactNavigationLinks() {
  return (
    <>
      {APP_ROUTES.map((route) => (
        <NavigationLink key={route.id} route={route} />
      ))}
    </>
  );
}

/**
 * Desktop navigation: the same destinations grouped by intent so a wide
 * sidebar stays scannable instead of presenting nine equal-weight rows.
 */
function GroupedNavigationLinks() {
  const { t } = useTranslation();

  return (
    <>
      {APP_ROUTE_GROUPS.map((group) => {
        const routes = appRoutesInGroup(group.id);
        if (routes.length === 0) return null;

        return (
          <div key={group.id} className="shell-nav-group">
            <p className="shell-nav-group-label">{t(group.labelKey)}</p>
            {routes.map((route) => (
              <NavigationLink key={route.id} route={route} />
            ))}
          </div>
        );
      })}
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

export function AppShell({
  children,
  onLogout,
}: {
  children: ReactNode;
  onLogout: () => void;
}) {
  const { t } = useTranslation();
  const online = useOnlineStatus();

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
        <Brand to={DEFAULT_APP_ROUTE} ariaLabel={t('brand.storyAria')} />
        <div className="header-actions">
          <span className="shared-context">
            <span aria-hidden="true">♥</span> {t('header.sharedArea')}
          </span>
          <ThemeControl variant="inline" />
          <button type="button" className="tertiary" onClick={logout}>
            {t('header.logout')}
          </button>
        </div>
      </header>

      {!online ? (
        <div className="offline-banner" role="status">
          <span aria-hidden="true">↯</span>
          <span>{t('states.offline.banner')}</span>
        </div>
      ) : null}

      <div className="product-shell-body">
        <aside className="shell-sidebar">
          <div className="shell-sidebar-inner">
            <div className="shell-primary-action">
              <Link className="button-link" to={appRoutePath('memoryCreate')}>
                <span className="shell-nav-icon">
                  <NavigationIcon icon="add" />
                </span>
                <span>{t('navigation.newMemory')}</span>
              </Link>
            </div>
            <nav className="shell-nav" aria-label={t('navigation.primary')}>
              <GroupedNavigationLinks />
            </nav>
          </div>
        </aside>

        <main id="main-content" className="product-main" tabIndex={-1}>
          {children}
        </main>
      </div>

      <nav className="mobile-bottom-nav" aria-label={t('navigation.primary')}>
        <CompactNavigationLinks />
      </nav>
    </div>
  );
}
