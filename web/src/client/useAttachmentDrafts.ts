import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useReducer,
  useRef,
} from 'react';
import {
  attachmentDraftReducer,
  hasPendingAttachments,
  readyAttachmentIds,
  type AttachmentDraft,
  type AttachmentDraftAction,
} from './attachmentDraftState';
import {
  uploadMemoryDraftAttachment,
  type DraftUploadPhase,
} from './memoryAttachmentDraft';
import type { ReferenceApis } from './referenceFlow';

export interface AttachmentDraftOptions {
  apis: ReferenceApis;
  apiBaseUrl: string;
  accessToken: string;
  spaceId: string;
  accountId: string;
  fetchApi?: typeof fetch;
  uploadAttachmentFn?: typeof uploadMemoryDraftAttachment;
}

export function formatAttachmentDraftContextKey(
  accountId: string,
  spaceId: string,
): string {
  return `${accountId}:${spaceId}`;
}

function errorMessage(error: unknown): string {
  return error instanceof Error && error.message
    ? error.message
    : String(error);
}

interface AttachmentDraftStore {
  contextKey: string;
  generation: number;
  items: AttachmentDraft[];
}

type AttachmentDraftStoreAction =
  | { type: 'reset_context'; contextKey: string; generation: number }
  | {
      type: 'draft_action';
      contextKey: string;
      generation: number;
      action: AttachmentDraftAction;
    };

function attachmentDraftStoreReducer(
  state: AttachmentDraftStore,
  action: AttachmentDraftStoreAction,
): AttachmentDraftStore {
  if (action.type === 'reset_context') {
    return {
      contextKey: action.contextKey,
      generation: action.generation,
      items: [],
    };
  }
  if (
    action.contextKey !== state.contextKey ||
    action.generation !== state.generation
  ) {
    return state;
  }
  return {
    ...state,
    items: attachmentDraftReducer(state.items, action.action),
  };
}

function abortAndRevoke(
  uploads: Map<string, AbortController>,
  previewUrls: Map<string, string>,
): void {
  for (const controller of uploads.values()) {
    try {
      controller.abort();
    } catch {
      // ignore
    }
  }
  uploads.clear();
  for (const previewUrl of previewUrls.values()) {
    try {
      URL.revokeObjectURL(previewUrl);
    } catch {
      // ignore
    }
  }
  previewUrls.clear();
}

export function useAttachmentDrafts({
  apis,
  apiBaseUrl,
  accessToken,
  spaceId,
  accountId,
  fetchApi = fetch,
  uploadAttachmentFn = uploadMemoryDraftAttachment,
}: AttachmentDraftOptions) {
  const contextKey = formatAttachmentDraftContextKey(accountId, spaceId);
  const committedContextKey = useRef(contextKey);
  const currentGeneration = useRef(1);
  const nextAttempt = useRef(0);
  const previewUrls = useRef(new Map<string, string>());
  const uploads = useRef(new Map<string, AbortController>());
  const mounted = useRef(true);

  const [store, dispatch] = useReducer(attachmentDraftStoreReducer, {
    contextKey,
    generation: currentGeneration.current,
    items: [],
  });

  useLayoutEffect(() => {
    if (committedContextKey.current !== contextKey) {
      committedContextKey.current = contextKey;
      currentGeneration.current += 1;
      abortAndRevoke(uploads.current, previewUrls.current);
      dispatch({
        type: 'reset_context',
        contextKey,
        generation: currentGeneration.current,
      });
    }
  }, [contextKey]);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      abortAndRevoke(uploads.current, previewUrls.current);
    };
  }, []);

  const isCurrentContext =
    store.contextKey === contextKey &&
    store.generation === currentGeneration.current &&
    committedContextKey.current === contextKey;
  const items = isCurrentContext ? store.items : [];

  const startUpload = useCallback(
    (id: string, file: File) => {
      uploads.current.get(id)?.abort();
      const controller = new AbortController();
      uploads.current.set(id, controller);
      const attempt = ++nextAttempt.current;
      const uploadGeneration = currentGeneration.current;
      const uploadContextKey = committedContextKey.current;

      dispatch({
        type: 'draft_action',
        contextKey: uploadContextKey,
        generation: uploadGeneration,
        action: { type: 'start', id, attempt },
      });

      const isCurrentAttempt = () =>
        mounted.current &&
        uploadGeneration === currentGeneration.current &&
        uploadContextKey === committedContextKey.current &&
        !controller.signal.aborted;

      const updatePhase = (status: DraftUploadPhase) => {
        if (!isCurrentAttempt()) return;
        dispatch({
          type: 'draft_action',
          contextKey: uploadContextKey,
          generation: uploadGeneration,
          action: { type: 'phase', id, attempt, status },
        });
      };
      const updateProgress = (progress: number) => {
        if (!isCurrentAttempt()) return;
        dispatch({
          type: 'draft_action',
          contextKey: uploadContextKey,
          generation: uploadGeneration,
          action: { type: 'progress', id, attempt, progress },
        });
      };

      void uploadAttachmentFn(
        apis,
        apiBaseUrl,
        accessToken,
        spaceId,
        file,
        updatePhase,
        fetchApi,
        { signal: controller.signal, onProgress: updateProgress },
      )
        .then(({ attachmentId }) => {
          uploads.current.delete(id);
          if (!isCurrentAttempt()) return;
          dispatch({
            type: 'draft_action',
            contextKey: uploadContextKey,
            generation: uploadGeneration,
            action: { type: 'ready', id, attempt, attachmentId },
          });
        })
        .catch((error: unknown) => {
          uploads.current.delete(id);
          if (!isCurrentAttempt()) return;
          dispatch({
            type: 'draft_action',
            contextKey: uploadContextKey,
            generation: uploadGeneration,
            action: {
              type: 'failed',
              id,
              attempt,
              error: errorMessage(error),
            },
          });
        });
    },
    [accessToken, apiBaseUrl, apis, fetchApi, spaceId, uploadAttachmentFn],
  );

  const addFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      const currentContext = committedContextKey.current;
      const currentGen = currentGeneration.current;
      for (const file of Array.from(files)) {
        const id = globalThis.crypto.randomUUID();
        const previewUrl = URL.createObjectURL(file);
        previewUrls.current.set(id, previewUrl);
        dispatch({
          type: 'draft_action',
          contextKey: currentContext,
          generation: currentGen,
          action: {
            type: 'add',
            draft: {
              id,
              file,
              previewUrl,
              status: 'uploading',
              attempt: 0,
              progress: 0,
            },
          },
        });
        startUpload(id, file);
      }
    },
    [startUpload],
  );

  const cancel = useCallback((id: string) => {
    uploads.current.get(id)?.abort();
    uploads.current.delete(id);
  }, []);

  const remove = useCallback(
    (id: string) => {
      cancel(id);
      const previewUrl = previewUrls.current.get(id);
      if (previewUrl) {
        try {
          URL.revokeObjectURL(previewUrl);
        } catch {
          // ignore
        }
      }
      previewUrls.current.delete(id);
      dispatch({
        type: 'draft_action',
        contextKey: committedContextKey.current,
        generation: currentGeneration.current,
        action: { type: 'remove', id },
      });
    },
    [cancel],
  );

  const retry = useCallback(
    (draft: AttachmentDraft) => startUpload(draft.id, draft.file),
    [startUpload],
  );

  const clear = useCallback(() => {
    currentGeneration.current += 1;
    abortAndRevoke(uploads.current, previewUrls.current);
    dispatch({
      type: 'reset_context',
      contextKey: committedContextKey.current,
      generation: currentGeneration.current,
    });
  }, []);

  const readyIds = useMemo(() => readyAttachmentIds(items), [items]);
  const hasPending = useMemo(() => hasPendingAttachments(items), [items]);

  return {
    items,
    addFiles,
    cancel,
    remove,
    retry,
    clear,
    readyIds,
    hasPending,
    contextKey,
    generation: currentGeneration.current,
  };
}
