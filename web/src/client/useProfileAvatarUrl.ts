import { useEffect, useState } from 'react';
import type { ProfilesApi } from '../api/generated/apis/ProfilesApi';

export function useProfileAvatarUrl(
  profilesApi: ProfilesApi,
  spaceId: string,
  accountId: string,
  profileAttachmentId: string | null | undefined,
): { avatarUrl: string | null; loadFailed: boolean } {
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    let disposed = false;
    const controller = new AbortController();

    setLoadFailed(false);
    setAvatarUrl(null);
    if (!profileAttachmentId) {
      return () => controller.abort();
    }

    void profilesApi
      .getProfileAvatarContentRaw(
        { accountId, spaceId },
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
        if (error instanceof DOMException && error.name === 'AbortError') return;
        if (!disposed) setLoadFailed(true);
      });

    return () => {
      disposed = true;
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [accountId, profileAttachmentId, profilesApi, spaceId]);

  return { avatarUrl, loadFailed };
}
