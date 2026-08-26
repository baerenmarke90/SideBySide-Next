import { useEffect, useState } from 'react';

export function MemoryPreview({
  memoryId,
  attachmentId,
  loadImage,
}: {
  memoryId: string;
  attachmentId: string;
  loadImage: (memoryId: string, attachmentId: string) => Promise<string>;
}) {
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
    return <div className="story-media-placeholder">Foto derzeit nicht verfügbar</div>;
  }

  if (!url) {
    return <div className="story-media-skeleton" role="status" aria-label="Foto wird geladen" />;
  }

  return <img className="story-media-preview" src={url} alt="Foto zu dieser Erinnerung" />;
}
