import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import type { StoryItem } from '../api/generated/models/StoryItem';
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
        author: {
          id: '00000000-0000-0000-0000-000000000001',
          displayName: 'A',
        },
        capabilities: { canComment: true, canDelete: true, canEdit: true },
        createdAt: '2026-08-26T08:00:00Z',
        happenedOn: '2026-08-26',
        id: '00000000-0000-0000-0000-000000000002',
        title: 'Am See',
      },
    });

    const html = renderToStaticMarkup(
      <MemoryRouter>
        <StoryList items={[item]} loadMemoryImage={loadMemoryImage} />
      </MemoryRouter>,
    );
    expect(html).toContain('<ol');
    expect(html).toContain('aria-label="Gemeinsame Story"');
    expect(html).toContain('Erinnerung');
    expect(html).toContain('Am See');
    expect(html).toContain('<time');
    expect(html).toContain(
      'href="/memory/00000000-0000-0000-0000-000000000002"',
    );
    expect(html).toContain('Erinnerung öffnen');
  });

  it('links HeartMoments and Milestones to their deep-link detail routes', () => {
    const heartMoment = {
      kind: 'HEART_MOMENT',
      effectiveDate: new Date('2026-08-26T00:00:00Z'),
      heartMoment: {
        id: 'heart-1',
        text: 'Danke für heute.',
        emotion: 'GRATEFUL',
        author: { id: 'author-1', displayName: 'A' },
        attachment: null,
      },
    } as unknown as StoryItem;
    const milestone = {
      kind: 'MILESTONE',
      effectiveDate: new Date('2026-08-25T00:00:00Z'),
      milestone: {
        id: 'milestone-1',
        title: 'Erste Wohnung',
        body: null,
        author: { id: 'author-2', displayName: 'B' },
      },
    } as unknown as StoryItem;

    const html = renderToStaticMarkup(
      <MemoryRouter>
        <StoryList
          items={[heartMoment, milestone]}
          loadMemoryImage={loadMemoryImage}
        />
      </MemoryRouter>,
    );

    expect(html).toContain('href="/heart-moment/heart-1"');
    expect(html).toContain('Herzmoment öffnen');
    expect(html).toContain('href="/milestone/milestone-1"');
    expect(html).toContain('Meilenstein öffnen');
  });

  it('announces an empty story as a status', () => {
    const html = renderToStaticMarkup(
      <StoryList items={[]} loadMemoryImage={loadMemoryImage} />,
    );
    expect(html).toContain('role="status"');
    expect(html).toContain('Eure Story beginnt hier.');
  });
});
