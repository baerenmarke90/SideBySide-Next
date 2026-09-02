import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HEART_MOMENT_CREATE_ROUTE,
  MEMORY_CREATE_ROUTE,
  MILESTONE_CREATE_ROUTE,
  MORE_PRIVATE_ROUTE,
  appRoutePath,
  type AppRouteIcon,
} from '../client/routes';
import { useTranslation } from '../i18n';
import { DestinationIcon } from './DestinationIcon';
import './QuickCreateMenu.css';

const PRIVATE_NOTE_CREATE_ROUTE = `${MORE_PRIVATE_ROUTE}/notes/new`;
const PLAN_ROUTE = appRoutePath('plan');

type QuickCreateTarget = {
  labelKey: string;
  to: string;
  icon: AppRouteIcon;
  tone: 'story' | 'planning';
};

const STORY_TARGETS: readonly QuickCreateTarget[] = [
  {
    labelKey: 'navigation.quickCreateMemory',
    to: MEMORY_CREATE_ROUTE,
    icon: 'story',
    tone: 'story',
  },
  {
    labelKey: 'navigation.quickCreateHeartMoment',
    to: HEART_MOMENT_CREATE_ROUTE,
    icon: 'activity',
    tone: 'story',
  },
  {
    labelKey: 'navigation.quickCreateMilestone',
    to: MILESTONE_CREATE_ROUTE,
    icon: 'today',
    tone: 'story',
  },
];

const PLANNING_TARGETS: readonly QuickCreateTarget[] = [
  {
    labelKey: 'navigation.quickCreatePlan',
    to: `${PLAN_ROUTE}#plan-title`,
    icon: 'plan',
    tone: 'planning',
  },
  {
    labelKey: 'navigation.quickCreateWish',
    to: `${PLAN_ROUTE}#wish-title`,
    icon: 'more',
    tone: 'planning',
  },
  {
    labelKey: 'navigation.quickCreatePlace',
    to: `${PLAN_ROUTE}#place-name`,
    icon: 'people',
    tone: 'planning',
  },
  {
    labelKey: 'navigation.quickCreateChapter',
    to: `${PLAN_ROUTE}#chapter-title`,
    icon: 'story',
    tone: 'planning',
  },
  {
    labelKey: 'navigation.quickCreateCollection',
    to: `${PLAN_ROUTE}#collection-title`,
    icon: 'more',
    tone: 'planning',
  },
];

export function QuickCreateMenu() {
  const { t } = useTranslation();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: MouseEvent): void {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }

    function onEscape(event: globalThis.KeyboardEvent): void {
      if (event.key !== 'Escape') return;
      setOpen(false);
      triggerRef.current?.focus();
    }

    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onEscape);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onEscape);
    };
  }, [open]);

  useEffect(() => {
    const targetId = location.hash.replace(/^#/, '');
    if (!targetId) return;

    const target = document.getElementById(targetId);
    if (!target) return;

    let parent = target.parentElement;
    while (parent) {
      if (parent instanceof HTMLDetailsElement) parent.open = true;
      parent = parent.parentElement;
    }
    target.scrollIntoView({ block: 'center' });
  }, [location.hash]);

  function focusMenuItem(index: number): void {
    const items =
      rootRef.current?.querySelectorAll<HTMLElement>('[role="menuitem"]');
    if (!items?.length) return;
    items[(index + items.length) % items.length]?.focus();
  }

  function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>): void {
    if (event.key !== 'ArrowDown') return;
    event.preventDefault();
    setOpen(true);
    window.requestAnimationFrame(() => focusMenuItem(0));
  }

  function handleMenuKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    const items = Array.from(
      rootRef.current?.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? [],
    );
    if (!items.length) return;

    const currentIndex = items.indexOf(document.activeElement as HTMLElement);
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      focusMenuItem(currentIndex + 1);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      focusMenuItem(currentIndex <= 0 ? items.length - 1 : currentIndex - 1);
    } else if (event.key === 'Home') {
      event.preventDefault();
      focusMenuItem(0);
    } else if (event.key === 'End') {
      event.preventDefault();
      focusMenuItem(items.length - 1);
    }
  }

  function renderTarget(target: QuickCreateTarget) {
    return (
      <Link
        key={target.labelKey}
        role="menuitem"
        className={`quick-create-menu-item quick-create-tile quick-create-tile-${target.tone}`}
        to={target.to}
        onClick={() => setOpen(false)}
      >
        <span className="quick-create-tile-icon" aria-hidden="true">
          <DestinationIcon icon={target.icon} />
        </span>
        <span>{t(target.labelKey)}</span>
      </Link>
    );
  }

  return (
    <div className="quick-create quick-create-polished" ref={rootRef}>
      <button
        ref={triggerRef}
        type="button"
        className="button-link quick-create-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls="quick-create-menu"
        onClick={() => setOpen((value) => !value)}
        onKeyDown={handleTriggerKeyDown}
      >
        <span className="shell-nav-icon" aria-hidden="true">
          <DestinationIcon icon="add" />
        </span>
        <span>{t('navigation.newContent')}</span>
        <span className="quick-create-chevron" aria-hidden="true">
          {open ? '−' : '⌄'}
        </span>
      </button>

      {open ? (
        <div
          id="quick-create-menu"
          className="quick-create-menu"
          role="menu"
          aria-label={t('navigation.newContent')}
          onKeyDown={handleMenuKeyDown}
        >
          <div className="quick-create-group-label">
            {t('navigation.quickCreateShared')}
          </div>
          <div className="quick-create-tile-grid">
            {STORY_TARGETS.map(renderTarget)}
          </div>

          <div className="quick-create-group-label quick-create-planning-label">
            {t('navigation.quickCreatePlanning')}
          </div>
          <div className="quick-create-tile-grid">
            {PLANNING_TARGETS.map(renderTarget)}
          </div>

          <hr className="quick-create-separator" />
          <div className="quick-create-group-label">
            {t('navigation.quickCreatePrivate')}
          </div>
          <Link
            role="menuitem"
            className="quick-create-menu-item quick-create-private-item"
            to={PRIVATE_NOTE_CREATE_ROUTE}
            onClick={() => setOpen(false)}
          >
            <span className="shell-nav-icon" aria-hidden="true">
              <DestinationIcon icon="private" />
            </span>
            <span>{t('navigation.quickCreatePrivateNote')}</span>
          </Link>
        </div>
      ) : null}
    </div>
  );
}
