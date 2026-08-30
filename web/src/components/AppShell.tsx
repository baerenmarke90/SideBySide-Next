import { useEffect, useState, type ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import {
  APP_ROUTES,
  DEFAULT_APP_ROUTE,
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

  if (icon === 'people') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm8 1a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5ZM3.5 19a4.5 4.5 0 0 1 9 0M13 19a3.5 3.5 0 0 1 7 0" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 18V9.5L12 4l7 5.5V18a2 2 0 0 1-2 2h-3v-6h-4v6H7a2 2 0 0 1-2-2Z" />
    </svg>
  );
}

function NavigationLinks() {
  const { t } = useTranslation();

  return (
    <>
      {APP_ROUTES.map((route) => (
        <NavLink
          key={route.id}
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

export function AppShell({
  children,
  onLogout,
}: {
  children: ReactNode;
  onLogout: () => void;
}) {
  const { t } = useTranslation();
  const online = useOnlineStatus();

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
          <button type="button" className="tertiary" onClick={onLogout}>
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
          <nav className="shell-nav" aria-label={t('navigation.primary')}>
            <NavigationLinks />
          </nav>
        </aside>

        <main id="main-content" className="product-main" tabIndex={-1}>
          {children}
        </main>
      </div>

      <nav className="mobile-bottom-nav" aria-label={t('navigation.primary')}>
        <NavigationLinks />
      </nav>
    </div>
  );
}
