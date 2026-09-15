import { useCallback, useEffect, useRef } from 'react';

export const EDITOR_HISTORY_STATE_KEY = '__sideBySideEditorEntry';
let editorHistorySequence = 0;
let pendingEntryRemoval: Promise<void> | null = null;

function waitForPendingEntryRemoval(): Promise<void> {
  return pendingEntryRemoval ?? Promise.resolve();
}

function removeCurrentEntry(marker: string): Promise<void> {
  if (window.history.state?.[EDITOR_HISTORY_STATE_KEY] !== marker) {
    return Promise.resolve();
  }
  if (pendingEntryRemoval) return pendingEntryRemoval;

  const removal = new Promise<void>((resolve) => {
    window.addEventListener('popstate', () => resolve(), { once: true });
    window.history.back();
  });
  const trackedRemoval = removal.finally(() => {
    if (pendingEntryRemoval === trackedRemoval) pendingEntryRemoval = null;
  });
  pendingEntryRemoval = trackedRemoval;
  return trackedRemoval;
}

function historyStateWithMarker(marker: string): Record<string, unknown> {
  const currentState = window.history.state;
  const state =
    currentState && typeof currentState === 'object' ? currentState : {};
  return { ...state, [EDITOR_HISTORY_STATE_KEY]: marker };
}

export function useEditorHistoryEntry({
  isActive = true,
  isDirty,
  isCloseBlocked = false,
  onDiscardRequested,
  onClose,
}: {
  isActive?: boolean;
  isDirty: boolean;
  isCloseBlocked?: boolean;
  onDiscardRequested: () => void;
  onClose: () => void;
}): () => void {
  const markerRef = useRef('');
  if (!markerRef.current) {
    editorHistorySequence += 1;
    markerRef.current = `editor-${editorHistorySequence}`;
  }

  const ownsEntryRef = useRef(false);
  const closingRef = useRef(false);
  const isDirtyRef = useRef(isDirty);
  const isCloseBlockedRef = useRef(isCloseBlocked);
  const onDiscardRequestedRef = useRef(onDiscardRequested);
  const onCloseRef = useRef(onClose);

  isDirtyRef.current = isDirty;
  isCloseBlockedRef.current = isCloseBlocked;
  onDiscardRequestedRef.current = onDiscardRequested;
  onCloseRef.current = onClose;

  useEffect(() => {
    if (isActive) closingRef.current = false;
  }, [isActive]);

  const isCurrentEntry = useCallback(
    () =>
      window.history.state?.[EDITOR_HISTORY_STATE_KEY] === markerRef.current,
    [],
  );

  const pushEntry = useCallback(() => {
    window.history.pushState(
      historyStateWithMarker(markerRef.current),
      '',
      window.location.href,
    );
    ownsEntryRef.current = true;
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined' || !isActive) return;

    let mounted = true;
    const handlePopState = () => {
      if (!ownsEntryRef.current) return;
      ownsEntryRef.current = false;

      if (isCloseBlockedRef.current) {
        pushEntry();
        return;
      }

      if (isDirtyRef.current) {
        pushEntry();
        onDiscardRequestedRef.current();
        return;
      }

      onCloseRef.current();
    };

    window.addEventListener('popstate', handlePopState);
    void waitForPendingEntryRemoval().then(() => {
      if (mounted && !ownsEntryRef.current) pushEntry();
    });

    return () => {
      mounted = false;
      window.removeEventListener('popstate', handlePopState);
      if (ownsEntryRef.current && isCurrentEntry()) {
        ownsEntryRef.current = false;
        void removeCurrentEntry(markerRef.current);
      }
    };
  }, [isActive, isCurrentEntry, pushEntry]);

  return useCallback(() => {
    if (closingRef.current) return;
    closingRef.current = true;
    if (
      typeof window !== 'undefined' &&
      ownsEntryRef.current &&
      isCurrentEntry()
    ) {
      ownsEntryRef.current = false;
      void removeCurrentEntry(markerRef.current).then(() =>
        onCloseRef.current(),
      );
      return;
    }
    onCloseRef.current();
  }, [isCurrentEntry]);
}
