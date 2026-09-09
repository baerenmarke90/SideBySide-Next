import {
  type KeyboardEvent,
  type TouchEvent,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HEART_MOMENT_CREATE_ROUTE,
  MEMORY_CREATE_ROUTE,
  MILESTONE_CREATE_ROUTE,
  MORE_PRIVATE_ROUTE,
  appRoutePath,
  type AppRouteIcon,
} from '../client/routes';
import { PRIVATE_GIFT_IDEAS_PATH } from '../client/privateArea';
import { useTranslation } from '../i18n';
import { DestinationIcon } from './DestinationIcon';
import './QuickCreateMenu.css';

const PRIVATE_NOTE_CREATE_ROUTE = `${MORE_PRIVATE_ROUTE}/notes/new`;
const PRIVATE_GIFT_IDEA_CREATE_ROUTE = `${PRIVATE_GIFT_IDEAS_PATH}/new`;
const PLAN_ROUTE = appRoutePath('plan');

type QuickCreateTarget = {
  id: string;
  labelKey: string;
  sublineKey: string;
  to: string;
  icon: AppRouteIcon;
  tone: 'story' | 'planning' | 'private';
};

const SHARED_TARGETS: readonly QuickCreateTarget[] = [
  {
    id: 'memory',
    labelKey: 'navigation.quickCreateMemory',
    sublineKey: 'navigation.quickCreateMemorySubline',
    to: MEMORY_CREATE_ROUTE,
    icon: 'story',
    tone: 'story',
  },
  {
    id: 'heart-moment',
    labelKey: 'navigation.quickCreateHeartMoment',
    sublineKey: 'navigation.quickCreateHeartMomentSubline',
    to: HEART_MOMENT_CREATE_ROUTE,
    icon: 'today',
    tone: 'story',
  },
  {
    id: 'milestone',
    labelKey: 'navigation.quickCreateMilestone',
    sublineKey: 'navigation.quickCreateMilestoneSubline',
    to: MILESTONE_CREATE_ROUTE,
    icon: 'milestone',
    tone: 'story',
  },
  {
    id: 'wish',
    labelKey: 'navigation.quickCreateWish',
    sublineKey: 'navigation.quickCreateWishSubline',
    to: `${PLAN_ROUTE}#wish-title`,
    icon: 'wish',
    tone: 'planning',
  },
  {
    id: 'plan',
    labelKey: 'navigation.quickCreatePlan',
    sublineKey: 'navigation.quickCreatePlanSubline',
    to: `${PLAN_ROUTE}#plan-title`,
    icon: 'plan',
    tone: 'planning',
  },
];

const FOR_ME_TARGETS: readonly QuickCreateTarget[] = [
  {
    id: 'note',
    labelKey: 'navigation.quickCreatePrivateNote',
    sublineKey: 'navigation.quickCreatePrivateNoteSubline',
    to: PRIVATE_NOTE_CREATE_ROUTE,
    icon: 'private',
    tone: 'private',
  },
  {
    id: 'gift-idea',
    labelKey: 'navigation.quickCreateGiftIdea',
    sublineKey: 'navigation.quickCreateGiftIdeaSubline',
    to: PRIVATE_GIFT_IDEA_CREATE_ROUTE,
    icon: 'gift',
    tone: 'private',
  },
];

export interface QuickCreateMenuProps {
  variant?: 'desktop' | 'mobile';
}

export function QuickCreateMenu({ variant = 'desktop' }: QuickCreateMenuProps) {
  const { t } = useTranslation();
  const location = useLocation();
  const menuId = useId();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const sheetRef = useRef<HTMLDivElement>(null);
  const firstFocusableRef = useRef<HTMLButtonElement>(null);
  const touchStartY = useRef<number | null>(null);

  const closeMenu = useCallback((): void => {
    setOpen(false);
    setTimeout(() => {
      triggerRef.current?.focus();
    }, 0);
  }, []);

  // Scroll locking for mobile bottom sheet
  useEffect(() => {
    if (!open || variant !== 'mobile') return;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [open, variant]);

  // Initial focus for mobile sheet
  useEffect(() => {
    if (open && variant === 'mobile') {
      const timer = setTimeout(() => {
        firstFocusableRef.current?.focus();
      }, 30);
      return () => clearTimeout(timer);
    }
  }, [open, variant]);

  // Escape key and outside click handling
  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: MouseEvent): void {
      if (variant === 'desktop') {
        if (!rootRef.current?.contains(event.target as Node)) {
          setOpen(false);
        }
      }
    }

    function onKeyDown(event: globalThis.KeyboardEvent): void {
      if (event.key === 'Escape') {
        closeMenu();
        return;
      }

      if (variant === 'mobile' && event.key === 'Tab' && sheetRef.current) {
        const focusable = sheetRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])',
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey) {
          if (
            document.activeElement === first ||
            !sheetRef.current.contains(document.activeElement)
          ) {
            event.preventDefault();
            last.focus();
          }
        } else {
          if (
            document.activeElement === last ||
            !sheetRef.current.contains(document.activeElement)
          ) {
            event.preventDefault();
            first.focus();
          }
        }
      }
    }

    document.addEventListener('mousedown', onPointerDown);
    window.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [open, variant, closeMenu]);

  // Anchor hash scrolling
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

  function handleTouchStart(e: TouchEvent<HTMLDivElement>) {
    touchStartY.current = e.touches[0].clientY;
  }

  function handleTouchEnd(e: TouchEvent<HTMLDivElement>) {
    if (touchStartY.current === null) return;
    const deltaY = e.changedTouches[0].clientY - touchStartY.current;
    if (deltaY > 60) {
      closeMenu();
    }
    touchStartY.current = null;
  }

  function renderDesktopTarget(target: QuickCreateTarget) {
    const sublineId = `${menuId}-subline-${target.id}`;
    return (
      <Link
        key={target.labelKey}
        role="menuitem"
        className={`quick-create-menu-item quick-create-tile quick-create-tile-${target.tone}`}
        to={target.to}
        onClick={() => setOpen(false)}
        aria-label={t(target.labelKey)}
        aria-describedby={sublineId}
      >
        <span className="quick-create-tile-icon" aria-hidden="true">
          <DestinationIcon icon={target.icon} />
        </span>
        <span className="quick-create-tile-content">
          <span className="quick-create-tile-title">{t(target.labelKey)}</span>
          <span id={sublineId} className="quick-create-tile-subline">
            {t(target.sublineKey)}
          </span>
        </span>
      </Link>
    );
  }

  function renderMobileTarget(target: QuickCreateTarget) {
    const sublineId = `${menuId}-mob-subline-${target.id}`;
    return (
      <Link
        key={target.labelKey}
        className={`quick-create-mobile-item quick-create-mobile-item-${target.tone}`}
        to={target.to}
        onClick={closeMenu}
        aria-label={t(target.labelKey)}
        aria-describedby={sublineId}
      >
        <span className="quick-create-tile-icon" aria-hidden="true">
          <DestinationIcon icon={target.icon} />
        </span>
        <span className="quick-create-mobile-item-content">
          <span className="quick-create-mobile-item-title">
            {t(target.labelKey)}
          </span>
          <span id={sublineId} className="quick-create-mobile-item-subline">
            {t(target.sublineKey)}
          </span>
        </span>
      </Link>
    );
  }

  const isMobile = variant === 'mobile';

  return (
    <div
      className={`quick-create quick-create-polished ${isMobile ? 'quick-create-mobile-variant' : 'quick-create-desktop-variant'}`}
      ref={rootRef}
    >
      <button
        ref={triggerRef}
        type="button"
        className={`button-link quick-create-trigger ${isMobile ? 'quick-create-fab' : ''}`}
        aria-haspopup={isMobile ? 'dialog' : 'menu'}
        aria-expanded={open}
        aria-controls={menuId}
        aria-label={t('navigation.newContent')}
        title={t('navigation.newContent')}
        style={
          isMobile && open
            ? { visibility: 'hidden', pointerEvents: 'none' }
            : undefined
        }
        aria-hidden={isMobile && open ? true : undefined}
        tabIndex={isMobile && open ? -1 : 0}
        onClick={() => setOpen((value) => !value)}
        onKeyDown={handleTriggerKeyDown}
      >
        <span className="shell-nav-icon" aria-hidden="true">
          <DestinationIcon icon="add" />
        </span>
        {!isMobile ? <span>{t('navigation.newContent')}</span> : null}
      </button>

      {/* Desktop Popover Menu */}
      {!isMobile && open ? (
        <div
          id={menuId}
          className="quick-create-menu"
          role="menu"
          aria-label={t('navigation.quickCreateTitle')}
          onKeyDown={handleMenuKeyDown}
        >
          <div className="quick-create-header-title">
            {t('navigation.quickCreateTitle')}
          </div>
          <div className="quick-create-tile-grid">
            {SHARED_TARGETS.map(renderDesktopTarget)}
          </div>

          <hr className="quick-create-separator" />
          <div className="quick-create-group-label quick-create-for-me-label">
            {t('navigation.quickCreateForMe')}
          </div>
          <div className="quick-create-tile-grid">
            {FOR_ME_TARGETS.map(renderDesktopTarget)}
          </div>
        </div>
      ) : null}

      {/* Mobile Responsive Action Sheet */}
      {isMobile && open ? (
        <div className="quick-create-mobile-portal">
          <div
            className="quick-create-mobile-backdrop"
            onClick={closeMenu}
            aria-hidden="true"
          />
          <div
            ref={sheetRef}
            id={menuId}
            className="quick-create-mobile-sheet sbs-motion-reveal"
            role="dialog"
            aria-modal="true"
            aria-label={t('navigation.quickCreateTitle')}
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
          >
            <div className="quick-create-sheet-header">
              <h2 className="quick-create-sheet-title">
                {t('navigation.quickCreateTitle')}
              </h2>
              <button
                ref={firstFocusableRef}
                type="button"
                className="quick-create-sheet-close"
                onClick={closeMenu}
                aria-label={t('navigation.closeMenu')}
              >
                ✕
              </button>
            </div>

            <div className="quick-create-sheet-scrollable">
              <div className="quick-create-mobile-list">
                {SHARED_TARGETS.map(renderMobileTarget)}
              </div>

              <hr className="quick-create-separator" />
              <div className="quick-create-group-label quick-create-for-me-label">
                {t('navigation.quickCreateForMe')}
              </div>
              <div className="quick-create-mobile-list">
                {FOR_ME_TARGETS.map(renderMobileTarget)}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
