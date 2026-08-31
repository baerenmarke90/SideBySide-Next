import { renderToStaticMarkup } from 'react-dom/server';
import { MediaType } from '../api/generated/models/MediaType';
import { i18n } from '../i18n';
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

    expect(html).toContain(`aria-label="${i18n.t('gallery.aria')}"`);
    expect(html).toContain(
      `aria-label="${i18n.t('gallery.openItem', { index: 1, count: 2 })}"`,
    );
    expect(html).toContain(
      `aria-label="${i18n.t('gallery.openItem', { index: 2, count: 2 })}"`,
    );
    expect(html.match(/type="button"/g)).toHaveLength(2);
  });
});
