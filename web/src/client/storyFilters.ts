import type { GetStoryTimelineRequest } from '../api/generated/apis/StoryApi';
import type { StoryKind } from '../api/generated/models/StoryKind';
import type { StoryOrder } from '../api/generated/models/StoryOrder';

export const STORY_PAGE_SIZE = 25;

export interface StoryFilters {
  kinds: StoryKind[];
  year: string;
  order: StoryOrder;
}

export class InvalidStoryYearError extends Error {
  constructor() {
    super('Story year must be an integer between 1 and 9999.');
    this.name = 'InvalidStoryYearError';
  }
}

export function parseStoryYear(value: string): number | undefined {
  const normalized = value.trim();
  if (!normalized) return undefined;
  const year = Number(normalized);
  if (!Number.isInteger(year) || year < 1 || year > 9999) {
    throw new InvalidStoryYearError();
  }
  return year;
}

export function storyTimelineRequest(
  spaceId: string,
  filters: StoryFilters,
  cursor?: string | null,
): GetStoryTimelineRequest {
  return {
    spaceId,
    type: filters.kinds.length > 0 ? filters.kinds : undefined,
    year: parseStoryYear(filters.year),
    order: filters.order,
    cursor: cursor || undefined,
    limit: STORY_PAGE_SIZE,
  };
}
