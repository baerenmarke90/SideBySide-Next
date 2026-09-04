import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';

export interface UseDismissiblePopoverOptions {
  onClose?: () => void;
  closeOnRouteChange?: boolean;
}

export function useDismissiblePopover(
  options: UseDismissiblePopoverOptions = {},
) {
  const { onClose, closeOnRouteChange = true } = options;
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef<HTMLElement | null>(null);
  const panelRef = useRef<HTMLElement | null>(null);
  const location = useLocation();

  const close = useCallback(
    (restoreFocus = false) => {
      setIsOpen((prev) => {
        if (prev) {
          onClose?.();
          return false;
        }
        return prev;
      });
      if (restoreFocus) {
        triggerRef.current?.focus();
      }
    },
    [onClose],
  );

  const open = useCallback(() => {
    setIsOpen(true);
  }, []);

  const toggle = useCallback(() => {
    setIsOpen((prev) => {
      const next = !prev;
      if (!next) {
        onClose?.();
      }
      return next;
    });
  }, [onClose]);

  // Route change auto-dismiss
  useEffect(() => {
    if (closeOnRouteChange) {
      setIsOpen(false);
    }
  }, [location.pathname, location.search, location.hash, closeOnRouteChange]);

  // Outside pointerdown and Escape key listeners
  useEffect(() => {
    if (!isOpen) return;

    function onPointerDown(event: PointerEvent | MouseEvent) {
      const target = event.target as Node | null;
      if (!target) return;
      if (
        panelRef.current?.contains(target) ||
        triggerRef.current?.contains(target)
      ) {
        return;
      }
      close();
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        close(true);
      }
    }

    document.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('keydown', onKeyDown);

    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [isOpen, close]);

  return {
    isOpen,
    setIsOpen,
    open,
    close,
    toggle,
    triggerRef,
    panelRef,
  };
}
