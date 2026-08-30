import { StoryKind } from '../api/generated/models/StoryKind';
import { StoryOrder } from '../api/generated/models/StoryOrder';
import {
  InvalidStoryYearError,
  parseStoryYear,
  storyTimelineRequest,
} from './storyFilters';

describe('story filters', () => {
  it('maps generated Story values and the server cursor without inventing client ordering', () => {
    expect(
      storyTimelineRequest(
        'space-1',
        {
          kinds: [StoryKind.MEMORY, StoryKind.MILESTONE],
          year: '2026',
          order: StoryOrder.DESC,
        },
        'opaque-server-cursor',
      ),
    ).toEqual({
      spaceId: 'space-1',
      type: [StoryKind.MEMORY, StoryKind.MILESTONE],
      year: 2026,
      order: StoryOrder.DESC,
      cursor: 'opaque-server-cursor',
      limit: 25,
    });
  });

  it('omits optional filters instead of serializing empty client values', () => {
    expect(
      storyTimelineRequest('space-1', {
        kinds: [],
        year: '',
        order: StoryOrder.ASC,
      }),
    ).toEqual({
      spaceId: 'space-1',
      type: undefined,
      year: undefined,
      order: StoryOrder.ASC,
      cursor: undefined,
      limit: 25,
    });
  });

  it('rejects malformed years instead of silently broadening the Story query', () => {
    expect(() => parseStoryYear('2026.5')).toThrow(InvalidStoryYearError);
    expect(() => parseStoryYear('10000')).toThrow(InvalidStoryYearError);
  });
});
