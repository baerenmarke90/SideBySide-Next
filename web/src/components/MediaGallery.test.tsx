import { renderToStaticMarkup } from 'react-dom/server';
import { MediaType } from '../api/generated/models/MediaType';
import { MediaGallery } from './MediaGallery';

describe('SBS-M5-Web-S2-SCOPE media gallery accessibility smoke', () => {
  it('renders keyboard-focusable gallery controls with accessible labels', () => {
    const html = renderToStaticMarkup(
      <MediaGallery
        items={[
          { id: 'image-1', mediaType: MediaType.IMAGE },
          { id: 'video-1', mediaType: MediaType.VIDEO },
        ]}
        loadMedia={async () => 'blob:test'}
      />,
    );

    expect(html).toContain('aria-label="Mediengalerie"');
    expect(html).toContain('aria-label="Medium 1 von 2 öffnen"');
    expect(html).toContain('aria-label="Medium 2 von 2 öffnen"');
    expect(html.match(/type="button"/g)).toHaveLength(2);
  });
});
