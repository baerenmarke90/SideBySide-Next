import { StoryKind } from '../api/generated/models/StoryKind';
import { StoryOrder } from '../api/generated/models/StoryOrder';
import type { StoryPage } from '../api/generated/models/StoryPage';
import {
  aggregateStoryPages,
  parseStoryFilters,
  storyCacheResourceId,
  storyFiltersToSearch,
  storyRequest,
} from './storyProduct';

describe('SBS-M5-Web-S2-SCOPE Story product query', () => {
  it('parses only supported Story filters and preserves a stable cache identity', () => {
    const filters = parseStoryFilters(
      new URLSearchParams('type=HEART_MOMENT&year=2026&order=ASC'),
    );

    expect(filters).toEqual({
      kind: StoryKind.HEART_MOMENT,
      year: 2026,
      order: StoryOrder.ASC,
    });
    expect(storyCacheResourceId(filters)).toBe(
      'timeline:HEART_MOMENT:2026:ASC',
    );
    expect(storyFiltersToSearch(filters).toString()).toBe(
      'type=HEART_MOMENT&year=2026&order=ASC',
    );
  });

  it('maps filters and cursor directly to the generated Story API request', () => {
    expect(
      storyRequest(
        'space-1',
        {
          kind: StoryKind.MEMORY,
          year: 2025,
          order: StoryOrder.DESC,
        },
        'cursor-2',
      ),
    ).toEqual({
      spaceId: 'space-1',
      type: [StoryKind.MEMORY],
      year: 2025,
      order: StoryOrder.DESC,
      cursor: 'cursor-2',
      limit: 25,
    });
  });

  it('aggregates loaded cursor pages without inventing pagination state', () => {
    const first = {
      items: [{ kind: 'MEMORY' }],
      hasMore: true,
      nextCursor: 'cursor-2',
    } as unknown as StoryPage;
    const second = {
      items: [{ kind: 'MILESTONE' }],
      hasMore: false,
      nextCursor: null,
    } as unknown as StoryPage;

    const combined = aggregateStoryPages([first, second]);
    expect(combined.items).toHaveLength(2);
    expect(combined.hasMore).toBe(false);
    expect(combined.nextCursor).toBeNull();
  });
});
