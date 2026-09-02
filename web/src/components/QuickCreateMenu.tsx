import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { Link } from 'react-router-dom';
import {
  HEART_MOMENT_CREATE_ROUTE,
  MEMORY_CREATE_ROUTE,
  MILESTONE_CREATE_ROUTE,
  MORE_PRIVATE_ROUTE,
  appRoutePath,
} from '../client/routes';
import { useTranslation } from '../i18n';
import { DestinationIcon } from './DestinationIcon';

const PRIVATE_NOTE_CREATE_ROUTE = `${MORE_PRIVATE_ROUTE}/notes/new`;

type QuickCreateGlyphName =
  | 'memory'
  | 'heart'
  | 'milestone'
  | 'plan'
  | 'wish'
  | 'place'
  | 'chapter'
  | 'collection';

function QuickCreateGlyph({ icon }: { icon: QuickCreateGlyphName }) {
  switch (icon) {
    case 'memory':
      return (
        <svg viewBox="0 0 24 24">
          <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
          <circle cx="9" cy="9" r="1.5" />
          <path d="m5.5 17 4.3-4.3 3 3 2.2-2.2 3.5 3.5" />
        </svg>
      );
    case 'heart':
      return (
        <svg viewBox="0 0 24 24">
          <path d="M20.5 8.7c0 5-8.5 10-8.5 10s-8.5-5-8.5-10a4.7 4.7 0 0 1 8.5-2.8 4.7 4.7 0 0 1 8.5 2.8Z" />
        </svg>
      );
    case 'milestone':
      return (
        <svg viewBox="0 0 24 24">
          <path d="M6 21V4" />
          <path d="M6 5h10l-2.5 3L16 11H6" />
        </svg>
      );
    case 'plan':
      return (
        <svg viewBox="0 0 24 24">
          <rect x="3.5" y="5.5" width="17" height="15" rx="2.5" />
          <path d="M8 3.5v4M16 3.5v4M3.5 10h17" />
        </svg>
      );
    case 'wish':
      return (
        <svg viewBox="0 0 24 24">
          <path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z" />
        </svg>
      );
    case 'place':
      return (
        <svg viewBox="0 0 24 24">
          <path d="M19 10c0 5-7 10.5-7 10.5S5 15 5 10a7 7 0 1 1 14 0Z" />
          <circle cx="12" cy="10" r="2.25" />
        </svg>
      );
    case 'chapter':
      return (
        <svg viewBox="0 0 24 24">
          <path d="M4 5.5A3.5 3.5 0 0 1 7.5 2H12v17H7.5A3.5 3.5 0 0 0 4 22V5.5ZM20 5.5A3.5 3.5 0 0 0 16.5 2H12v17h4.5A3.5 3.5 0 0 1 20 22V5.5Z" />
        </svg>
      );
    case 'collection':
      return (
        <svg viewBox="0 0 24 24">
          <path d="M9 6h11M9 12h11M9 18h11" />
          <circle cx="4.5" cy="6" r="1" />
          <circle cx="4.5" cy="12" r="1" />
          <circle cx="4.5" cy="18" r="1" />
        </svg>
      );
  }
}

export function QuickCreateMenu() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const planningPath = appRoutePath('plan');

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
    if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
      event.preventDefault();
      focusMenuItem(currentIndex + 1);
    } else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
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

  const sharedItems: Array<{
    key: string;
    label: string;
    to: string;
    icon: QuickCreateGlyphName;
    tone: string;
  }> = [
    {
      key: 'memory',
      label: t('story.addMemory'),
      to: MEMORY_CREATE_ROUTE,
      icon: 'memory',
      tone: 'lavender',
    },
    {
      key: 'heart',
      label: t('storyActions.addHeartMoment'),
      to: HEART_MOMENT_CREATE_ROUTE,
      icon: 'heart',
      tone: 'blush',
    },
    {
      key: 'milestone',
      label: t('storyActions.addMilestone'),
      to: MILESTONE_CREATE_ROUTE,
      icon: 'milestone',
      tone: 'lavender',
    },
    {
      key: 'plan',
      label: t('m5s3.plan.create'),
      to: planningPath,
      icon: 'plan',
      tone: 'mint',
    },
    {
      key: 'wish',
      label: t('m5s3.wish.create'),
      to: planningPath,
      icon: 'wish',
      tone: 'gold',
    },
    {
      key: 'place',
      label: t('m5s3.place.create'),
      to: planningPath,
      icon: 'place',
      tone: 'sand',
    },
    {
      key: 'chapter',
      label: t('m5s3.chapter.create'),
      to: planningPath,
      icon: 'chapter',
      tone: 'lavender',
    },
    {
      key: 'collection',
      label: t('m5s3.collection.detailEyebrow'),
      to: planningPath,
      icon: 'collection',
      tone: 'mint',
    },
  ];

  return (
    <div className="quick-create" ref={rootRef}>
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
        <span className="quick-create-trigger-chevron" aria-hidden="true">
          {open ? '⌃' : '⌄'}
        </span>
      </button>

      {open ? (
        <div
          id="quick-create-menu"
          className="quick-create-menu quick-create-menu-expanded"
          role="menu"
          aria-label={t('navigation.newContent')}
          onKeyDown={handleMenuKeyDown}
        >
          <div className="quick-create-group-label">
            {t('navigation.quickCreateShared')}
          </div>
          <div className="quick-create-grid">
            {sharedItems.map((item) => (
              <Link
                key={item.key}
                role="menuitem"
                className="quick-create-menu-item quick-create-tile"
                to={item.to}
                onClick={() => setOpen(false)}
              >
                <span
                  className={`quick-create-tile-icon quick-create-tone-${item.tone}`}
                  aria-hidden="true"
                >
                  <QuickCreateGlyph icon={item.icon} />
                </span>
                <span className="quick-create-tile-label">{item.label}</span>
              </Link>
            ))}
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
