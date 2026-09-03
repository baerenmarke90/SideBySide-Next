import type { GetStoryTimelineRequest } from '../api/generated/apis/StoryApi';
import {
  StoryKind,
  type StoryKind as StoryKindValue,
} from '../api/generated/models/StoryKind';
import {
  StoryOrder,
  type StoryOrder as StoryOrderValue,
} from '../api/generated/models/StoryOrder';
import type { StoryPage } from '../api/generated/models/StoryPage';

export interface StoryFilters {
  kind: StoryKindValue | null;
  year: number | null;
  order: StoryOrderValue;
}

export const DEFAULT_STORY_FILTERS: StoryFilters = {
  kind: null,
  year: null,
  order: StoryOrder.DESC,
};

function isStoryKind(value: string | null): value is StoryKindValue {
  return (
    value !== null && Object.values(StoryKind).includes(value as StoryKindValue)
  );
}

export function parseStoryFilters(search: URLSearchParams): StoryFilters {
  const kindValue = search.get('type');
  const yearValue = search.get('year');
  const parsedYear = yearValue ? Number(yearValue) : Number.NaN;
  const order =
    search.get('order') === StoryOrder.ASC ? StoryOrder.ASC : StoryOrder.DESC;

  return {
    kind: isStoryKind(kindValue) ? kindValue : null,
    year: Number.isInteger(parsedYear) && parsedYear > 0 ? parsedYear : null,
    order,
  };
}

export function storyFiltersToSearch(filters: StoryFilters): URLSearchParams {
  const search = new URLSearchParams();
  if (filters.kind) search.set('type', filters.kind);
  if (filters.year) search.set('year', String(filters.year));
  if (filters.order === StoryOrder.ASC) search.set('order', StoryOrder.ASC);
  return search;
}

export function storyCacheResourceId(filters: StoryFilters): string {
  return [
    'timeline',
    filters.kind ?? 'ALL',
    filters.year ?? 'ALL',
    filters.order,
  ].join(':');
}

export function storyRequest(
  spaceId: string,
  filters: StoryFilters,
  cursor: string | null,
): GetStoryTimelineRequest {
  return {
    spaceId,
    type: filters.kind ? [filters.kind] : undefined,
    year: filters.year ?? undefined,
    order: filters.order,
    cursor: cursor ?? undefined,
    limit: 25,
  };
}

export function aggregateStoryPages(pages: StoryPage[]): StoryPage {
  const lastPage = pages.at(-1);
  return {
    items: pages.flatMap((page) => page.items),
    hasMore: lastPage?.hasMore ?? false,
    nextCursor: lastPage?.nextCursor ?? null,
    availableYears: pages[0]?.availableYears ?? [],
  };
}
