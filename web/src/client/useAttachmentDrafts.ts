import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react';
import {
  attachmentDraftReducer,
  hasPendingAttachments,
  readyAttachmentIds,
  type AttachmentDraft,
} from './attachmentDraftState';
import {
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
  const nextAttempt = useRef(0);
  const previewUrls = useRef(new Map<string, string>());
  const uploads = useRef(new Map<string, AbortController>());
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      for (const controller of uploads.current.values()) controller.abort();
      uploads.current.clear();
      for (const previewUrl of previewUrls.current.values()) {
        URL.revokeObjectURL(previewUrl);
      }
      previewUrls.current.clear();
    };
  }, []);

  const startUpload = useCallback(
    (id: string, file: File) => {
      uploads.current.get(id)?.abort();
      const controller = new AbortController();
      uploads.current.set(id, controller);
      const attempt = ++nextAttempt.current;
      dispatch({ type: 'start', id, attempt });

      const updatePhase = (status: DraftUploadPhase) => {
        if (!mounted.current || controller.signal.aborted) return;
        dispatch({ type: 'phase', id, attempt, status });
      };
      const updateProgress = (progress: number) => {
        if (!mounted.current || controller.signal.aborted) return;
        dispatch({ type: 'progress', id, attempt, progress });
      };

      void uploadMemoryDraftAttachment(
        apis,
        apiBaseUrl,
        accessToken,
        spaceId,
        file,
        updatePhase,
        fetch,
        { signal: controller.signal, onProgress: updateProgress },
      )
        .then(({ attachmentId }) => {
          uploads.current.delete(id);
          if (!mounted.current || controller.signal.aborted) return;
          dispatch({ type: 'ready', id, attempt, attachmentId });
        })
        .catch((error: unknown) => {
          uploads.current.delete(id);
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
            progress: 0,
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
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrls.current.delete(id);
      dispatch({ type: 'remove', id });
    },
    [cancel],
  );

  const retry = useCallback(
    (draft: AttachmentDraft) => startUpload(draft.id, draft.file),
    [startUpload],
  );

  const clear = useCallback(() => {
    for (const controller of uploads.current.values()) controller.abort();
    uploads.current.clear();
    for (const previewUrl of previewUrls.current.values()) {
      URL.revokeObjectURL(previewUrl);
    }
    previewUrls.current.clear();
    dispatch({ type: 'clear' });
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
  };
}
