import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react';
import {
  attachmentDraftReducer,
  hasPendingAttachments,
  readyAttachmentIds,
  type AttachmentDraft,
} from './attachmentDraftState';
import {
  deleteUnboundAttachment,
  uploadMemoryDraftAttachment,
  type DraftUploadPhase,
} from './memoryAttachmentDraft';
import type { ReferenceApis } from './referenceFlow';

interface AttachmentDraftOptions {
  apis: ReferenceApis;
  apiBaseUrl: string;
  accessToken: string;
  spaceId: string;
}

function errorMessage(error: unknown): string {
  return error instanceof Error && error.message
    ? error.message
    : String(error);
}

export function useAttachmentDrafts({
  apis,
  apiBaseUrl,
  accessToken,
  spaceId,
}: AttachmentDraftOptions) {
  const [items, dispatch] = useReducer(attachmentDraftReducer, []);
  const itemsRef = useRef<AttachmentDraft[]>([]);
  itemsRef.current = items;
  const nextAttempt = useRef(0);
  const previewUrls = useRef(new Map<string, string>());
  const controllers = useRef(new Map<string, AbortController>());
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      for (const controller of controllers.current.values()) controller.abort();
      controllers.current.clear();
      for (const draft of itemsRef.current) {
        if (draft.attachmentId) {
          void deleteUnboundAttachment(apis, spaceId, draft.attachmentId);
        }
      }
      itemsRef.current = [];
      for (const previewUrl of previewUrls.current.values()) {
        URL.revokeObjectURL(previewUrl);
      }
      previewUrls.current.clear();
    };
  }, [apis, spaceId]);

  const startUpload = useCallback(
    (id: string, file: File) => {
      controllers.current.get(id)?.abort();
      const controller = new AbortController();
      controllers.current.set(id, controller);
      const attempt = ++nextAttempt.current;
      dispatch({ type: 'start', id, attempt });

      const updatePhase = (status: DraftUploadPhase) => {
        if (!mounted.current || controller.signal.aborted) return;
        dispatch({ type: 'phase', id, attempt, status });
      };

      void uploadMemoryDraftAttachment(
        apis,
        apiBaseUrl,
        accessToken,
        spaceId,
        file,
        updatePhase,
        fetch,
        controller.signal,
      )
        .then(({ attachmentId }) => {
          if (!mounted.current || controller.signal.aborted) return;
          controllers.current.delete(id);
          dispatch({ type: 'ready', id, attempt, attachmentId });
        })
        .catch((error: unknown) => {
          controllers.current.delete(id);
          if (!mounted.current || controller.signal.aborted) return;
          dispatch({ type: 'failed', id, attempt, error: errorMessage(error) });
        });
    },
    [accessToken, apiBaseUrl, apis, spaceId],
  );

  const addFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      for (const file of Array.from(files)) {
        const id = globalThis.crypto.randomUUID();
        const previewUrl = URL.createObjectURL(file);
        previewUrls.current.set(id, previewUrl);
        dispatch({
          type: 'add',
          draft: {
            id,
            file,
            previewUrl,
            status: 'uploading',
            attempt: 0,
          },
        });
        startUpload(id, file);
      }
    },
    [startUpload],
  );

  const remove = useCallback(
    (id: string) => {
      controllers.current.get(id)?.abort();
      controllers.current.delete(id);
      const draft = itemsRef.current.find((candidate) => candidate.id === id);
      itemsRef.current = itemsRef.current.filter(
        (candidate) => candidate.id !== id,
      );
      if (draft?.attachmentId) {
        void deleteUnboundAttachment(apis, spaceId, draft.attachmentId);
      }
      const previewUrl = previewUrls.current.get(id);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrls.current.delete(id);
      dispatch({ type: 'remove', id });
    },
    [apis, spaceId],
  );

  const retry = useCallback(
    (draft: AttachmentDraft) => startUpload(draft.id, draft.file),
    [startUpload],
  );

  const clear = useCallback(() => {
    for (const controller of controllers.current.values()) controller.abort();
    controllers.current.clear();
    itemsRef.current = [];
    for (const previewUrl of previewUrls.current.values()) {
      URL.revokeObjectURL(previewUrl);
    }
    previewUrls.current.clear();
    dispatch({ type: 'clear' });
  }, []);

  const readyIds = useMemo(() => readyAttachmentIds(items), [items]);
  const hasPending = useMemo(() => hasPendingAttachments(items), [items]);

  return { items, addFiles, remove, retry, clear, readyIds, hasPending };
}
