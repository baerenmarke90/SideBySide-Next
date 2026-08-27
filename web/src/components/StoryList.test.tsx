import { renderToStaticMarkup } from 'react-dom/server';
import { StoryItemFromJSON } from '../api/generated/models/StoryItem';
import { StoryList } from './StoryList';

const loadMemoryImage = async () => 'blob:test-image';

describe('StoryList', () => {
  it('renders a generated MEMORY discriminator with semantic list markup', () => {
    const item = StoryItemFromJSON({
      kind: 'MEMORY',
      effectiveDate: '2026-08-26',
      memory: {
        attachments: [],
        author: { id: '00000000-0000-0000-0000-000000000001', displayName: 'A' },
        capabilities: { canComment: true, canDelete: true, canEdit: true },
        createdAt: '2026-08-26T08:00:00Z',
        happenedOn: '2026-08-26',
        id: '00000000-0000-0000-0000-000000000002',
        title: 'Am See',
      },
    });

    const html = renderToStaticMarkup(
      <StoryList items={[item]} loadMemoryImage={loadMemoryImage} />,
    );
    expect(html).toContain('<ol');
    expect(html).toContain('aria-label="Gemeinsame Story"');
    expect(html).toContain('Erinnerung');
    expect(html).toContain('Am See');
    expect(html).toContain('<time');
  });

  it('announces an empty story as a status', () => {
    const html = renderToStaticMarkup(
      <StoryList items={[]} loadMemoryImage={loadMemoryImage} />,
    );
    expect(html).toContain('role="status"');
    expect(html).toContain('Eure Story beginnt hier.');
  });
});
