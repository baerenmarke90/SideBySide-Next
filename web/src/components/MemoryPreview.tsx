import { useEffect, useState } from 'react';
import { useTranslation } from '../i18n';

export function MemoryPreview({
  memoryId,
  attachmentId,
  loadImage,
}: {
  memoryId: string;
  attachmentId: string;
  loadImage: (memoryId: string, attachmentId: string) => Promise<string>;
}) {
  const { t } = useTranslation();
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;

    void loadImage(memoryId, attachmentId)
      .then((loadedUrl) => {
        if (!active) {
          URL.revokeObjectURL(loadedUrl);
          return;
        }
        objectUrl = loadedUrl;
        setUrl(loadedUrl);
      })
      .catch(() => {
        if (active) setFailed(true);
      });

    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [attachmentId, loadImage, memoryId]);

  if (failed) {
    return (
      <div className="story-media-placeholder">{t('media.unavailable')}</div>
    );
  }

  if (!url) {
    return (
      <div
        className="story-media-skeleton"
        role="status"
        aria-label={t('media.loading')}
      />
    );
  }

  return <img className="story-media-preview" src={url} alt={t('media.alt')} />;
}
