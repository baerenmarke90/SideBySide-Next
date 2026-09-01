import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { Link } from 'react-router-dom';
import {
  HEART_MOMENT_CREATE_ROUTE,
  MEMORY_CREATE_ROUTE,
  MILESTONE_CREATE_ROUTE,
  MORE_PRIVATE_ROUTE,
} from '../client/routes';
import { useTranslation } from '../i18n';
import { DestinationIcon } from './DestinationIcon';

const PRIVATE_NOTE_CREATE_ROUTE = `${MORE_PRIVATE_ROUTE}/notes/new`;

export function QuickCreateMenu() {
  const { t } = useTranslation();
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

  function focusMenuItem(index: number): void {
    const items = rootRef.current?.querySelectorAll<HTMLElement>('[role="menuitem"]');
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

    const currentIndex = items.findIndex((item) => item === document.activeElement);
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
          <Link
            role="menuitem"
            className="quick-create-menu-item"
            to={MEMORY_CREATE_ROUTE}
            onClick={() => setOpen(false)}
          >
            {t('story.addMemory')}
          </Link>
          <Link
            role="menuitem"
            className="quick-create-menu-item"
            to={HEART_MOMENT_CREATE_ROUTE}
            onClick={() => setOpen(false)}
          >
            {t('storyActions.addHeartMoment')}
          </Link>
          <Link
            role="menuitem"
            className="quick-create-menu-item"
            to={MILESTONE_CREATE_ROUTE}
            onClick={() => setOpen(false)}
          >
            {t('storyActions.addMilestone')}
          </Link>

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
