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
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      for (const previewUrl of previewUrls.current.values()) {
        URL.revokeObjectURL(previewUrl);
      }
      previewUrls.current.clear();
    };
  }, []);

  const startUpload = useCallback(
    (id: string, file: File) => {
      const attempt = ++nextAttempt.current;
      dispatch({ type: 'start', id, attempt });

      const updatePhase = (status: DraftUploadPhase) => {
        if (!mounted.current) return;
        dispatch({ type: 'phase', id, attempt, status });
      };

      void uploadMemoryDraftAttachment(
        apis,
        apiBaseUrl,
        accessToken,
        spaceId,
        file,
        updatePhase,
      )
        .then(({ attachmentId }) => {
          if (!mounted.current) return;
          dispatch({ type: 'ready', id, attempt, attachmentId });
        })
        .catch((error: unknown) => {
          if (!mounted.current) return;
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

  const remove = useCallback((id: string) => {
    const previewUrl = previewUrls.current.get(id);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrls.current.delete(id);
    dispatch({ type: 'remove', id });
  }, []);

  const retry = useCallback(
    (draft: AttachmentDraft) => startUpload(draft.id, draft.file),
    [startUpload],
  );

  const clear = useCallback(() => {
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
