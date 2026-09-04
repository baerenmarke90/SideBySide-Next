import { useEffect, useState } from 'react';
import type { AttachmentsApi } from '../api/generated/apis/AttachmentsApi';

export function useRelatedPersonAvatarUrl(
  attachmentsApi: AttachmentsApi | undefined | null,
  spaceId: string,
  avatarAttachmentId: string | null | undefined,
): { avatarUrl: string | null; loadFailed: boolean } {
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    let disposed = false;
    const controller = new AbortController();

    setLoadFailed(false);
    setAvatarUrl(null);
    if (!attachmentsApi || !avatarAttachmentId) {
      return () => controller.abort();
    }

    void attachmentsApi
      .getAttachmentContentRaw(
        { spaceId, attachmentId: avatarAttachmentId },
        { signal: controller.signal },
      )
      .then(async (response) => {
        const blob = await response.raw.blob();
        objectUrl = URL.createObjectURL(blob);
        if (disposed) {
          URL.revokeObjectURL(objectUrl);
          objectUrl = null;
          return;
        }
        setAvatarUrl(objectUrl);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError')
          return;
        if (!disposed) setLoadFailed(true);
      });

    return () => {
      disposed = true;
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [attachmentsApi, avatarAttachmentId, spaceId]);

  return { avatarUrl, loadFailed };
}
