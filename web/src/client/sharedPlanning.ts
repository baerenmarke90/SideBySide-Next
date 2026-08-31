import { ChapterRelationsApi } from '../api/generated/apis/ChapterRelationsApi';
import { ChaptersApi } from '../api/generated/apis/ChaptersApi';
import { CollectionsApi } from '../api/generated/apis/CollectionsApi';
import { PlaceRelationsApi } from '../api/generated/apis/PlaceRelationsApi';
import { PlacesApi } from '../api/generated/apis/PlacesApi';
import { PlansApi } from '../api/generated/apis/PlansApi';
import { StoryApi } from '../api/generated/apis/StoryApi';
import { WishesApi } from '../api/generated/apis/WishesApi';
import type { StoryItem } from '../api/generated/models/StoryItem';
import { Configuration } from '../api/generated/runtime';

export interface SharedPlanningApis {
  wishes: WishesApi;
  plans: PlansApi;
  places: PlacesApi;
  placeRelations: PlaceRelationsApi;
  chapters: ChaptersApi;
  chapterRelations: ChapterRelationsApi;
  collections: CollectionsApi;
  story: StoryApi;
}

export interface VersionedResource {
  version: number;
}

export type PlanningRelationKind = 'MEMORY' | 'HEART_MOMENT' | 'MILESTONE';

export interface PlanningRelationTarget {
  id: string;
  kind: PlanningRelationKind;
  label: string;
  effectiveDate: Date;
}

export function createSharedPlanningApis(
  apiBaseUrl: string,
  accessToken: string,
): SharedPlanningApis {
  const configuration = new Configuration({
    basePath: apiBaseUrl,
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  return {
    wishes: new WishesApi(configuration),
    plans: new PlansApi(configuration),
    places: new PlacesApi(configuration),
    placeRelations: new PlaceRelationsApi(configuration),
    chapters: new ChaptersApi(configuration),
    chapterRelations: new ChapterRelationsApi(configuration),
    collections: new CollectionsApi(configuration),
    story: new StoryApi(configuration),
  };
}

export function planningIfMatch(resource: VersionedResource): string {
  return String(resource.version);
}

export function dateOnlyInput(value: Date | null | undefined): string {
  return value ? value.toISOString().slice(0, 10) : '';
}

export function dateFromInput(value: string): Date | undefined {
  return value ? new Date(`${value}T00:00:00Z`) : undefined;
}

export function localDateTimeInput(value: Date | null | undefined): string {
  if (!value) return '';
  const local = new Date(value.getTime() - value.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

export function dateTimeFromInput(value: string): Date | undefined {
  return value ? new Date(value) : undefined;
}

export function moveItemIds(
  ids: readonly string[],
  index: number,
  direction: -1 | 1,
): string[] {
  const target = index + direction;
  if (index < 0 || index >= ids.length || target < 0 || target >= ids.length) {
    return [...ids];
  }
  const next = [...ids];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}

export function storyRelationTarget(item: StoryItem): PlanningRelationTarget {
  switch (item.kind) {
    case 'MEMORY':
      return {
        id: item.memory.id,
        kind: 'MEMORY',
        label: item.memory.title,
        effectiveDate: item.effectiveDate,
      };
    case 'HEART_MOMENT':
      return {
        id: item.heartMoment.id,
        kind: 'HEART_MOMENT',
        label: item.heartMoment.text,
        effectiveDate: item.effectiveDate,
      };
    case 'MILESTONE':
      return {
        id: item.milestone.id,
        kind: 'MILESTONE',
        label: item.milestone.title,
        effectiveDate: item.effectiveDate,
      };
  }
}
