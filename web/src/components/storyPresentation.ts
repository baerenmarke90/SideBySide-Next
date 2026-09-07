import type { TFunction } from 'i18next';
import type { StoryItem } from '../api/generated/models/StoryItem';
import type { StoryKind } from '../api/generated/models/StoryKind';

export interface StoryPresentation {
  kindLabel: string;
  title: string;
  preview?: string;
  author: string;
  mediaLabel?: string;
  sharedLabel?: string;
}

export interface StoryGroup {
  key: string;
  label: string;
  items: StoryItem[];
}

function compactText(value: string, maxLength = 150): string {
  const text = value.trim().replace(/\s+/g, ' ');
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1).trimEnd()}…`;
}

function emotionLabel(emotion: string, t: TFunction): string {
  switch (emotion) {
    case 'LOVED':
      return t('story.emotion.loved');
    case 'SEEN':
      return t('story.emotion.seen');
    case 'APPRECIATED':
      return t('story.emotion.appreciated');
    case 'SUPPORTED':
      return t('story.emotion.supported');
    case 'GRATEFUL':
      return t('story.emotion.grateful');
    case 'HAPPY':
      return t('story.emotion.happy');
    default:
      return t('story.emotion.fallback');
  }
}

export { storyItemKey } from '../client/storyProduct';

export function resolveStoryKindLabel(
  kind: StoryKind | string | null | undefined,
  t: TFunction,
): string {
  if (!kind) return '';
  switch (kind) {
    case 'MEMORY':
    case 'memory':
      return t('story.kind.memory');
    case 'HEART_MOMENT':
    case 'heartMoment':
      return t('story.kind.heartMoment');
    case 'MILESTONE':
    case 'milestone':
      return t('story.kind.milestone');
    default:
      return String(kind);
  }
}

export function storyItemPresentation(
  item: StoryItem,
  t: TFunction,
): StoryPresentation {
  const kindLabel = resolveStoryKindLabel(item.kind, t);
  switch (item.kind) {
    case 'MEMORY': {
      const count = item.memory.attachments.length;
      return {
        kindLabel,
        title: item.memory.title,
        author: item.memory.author.displayName,
        mediaLabel: count > 0 ? t('story.photos', { count }) : undefined,
      };
    }
    case 'HEART_MOMENT':
      return {
        kindLabel,
        title: compactText(item.heartMoment.text),
        preview: emotionLabel(item.heartMoment.emotion, t),
        author: item.heartMoment.author.displayName,
        mediaLabel: item.heartMoment.attachment
          ? t('story.photos', { count: 1 })
          : undefined,
        sharedLabel: t('story.shared'),
      };
    case 'MILESTONE':
      return {
        kindLabel,
        title: item.milestone.title,
        author: item.milestone.author.displayName,
      };
  }
}

export type TapestryRole = 'media' | 'note' | 'milestone' | 'text';

/**
 * The Discover tapestry gives each content type a distinct physical role
 * (#790): a photo Memory is image-first, a Heart Moment reads as a note, a
 * Milestone is a compact marker, and a Memory without media falls back to a
 * quiet text card.
 */
export function tapestryItemRole(item: StoryItem): TapestryRole {
  if (item.kind === 'MEMORY') {
    return item.memory.attachments.length > 0 ? 'media' : 'text';
  }
  if (item.kind === 'HEART_MOMENT') return 'note';
  return 'milestone';
}

/**
 * Relative weights approximating each role's real rendered height, used to
 * balance the tapestry's columns. A photo tile reads roughly as tall as three
 * or four milestone markers, so pure item-count balancing would leave a
 * media-heavy column much taller than the others.
 */
const TAPESTRY_ROLE_WEIGHT: Record<TapestryRole, number> = {
  media: 7,
  note: 2,
  text: 2,
  milestone: 1,
};

export function tapestryRoleWeight(role: TapestryRole): number {
  return TAPESTRY_ROLE_WEIGHT[role];
}

/**
 * Greedy shortest-column-first distribution. CSS multi-column's built-in
 * balancing can leave a trailing column mostly empty once a few tall,
 * break-inside-avoid photo tiles are mixed with short items (verified against
 * the real canonical demo dataset), which reproduces exactly the "large
 * unintended dead zone" #790 asks to remove. Assigning each entry to the
 * currently lightest column keeps the columns close to equal height without
 * requiring real DOM measurement.
 */
export function distributeIntoTapestryColumns<T>(
  entries: readonly T[],
  columnCount: number,
  weightOf: (entry: T) => number,
): T[][] {
  const count = Math.max(1, Math.floor(columnCount));
  const columns: T[][] = Array.from({ length: count }, () => []);
  const columnWeights = new Array(count).fill(0);
  for (const entry of entries) {
    let lightest = 0;
    for (let i = 1; i < count; i++) {
      if (columnWeights[i] < columnWeights[lightest]) lightest = i;
    }
    columns[lightest].push(entry);
    columnWeights[lightest] += weightOf(entry);
  }
  return columns;
}

export function formatStoryDate(date: Date, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(date);
}

export function groupStoryItems(
  items: StoryItem[],
  locale: string,
): StoryGroup[] {
  const groups = new Map<string, StoryGroup>();
  const monthFormatter = new Intl.DateTimeFormat(locale, {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  });

  for (const item of items) {
    const year = item.effectiveDate.getUTCFullYear();
    const month = item.effectiveDate.getUTCMonth() + 1;
    const key = `${year}-${String(month).padStart(2, '0')}`;
    let group = groups.get(key);
    if (!group) {
      group = {
        key,
        label: monthFormatter.format(item.effectiveDate),
        items: [],
      };
      groups.set(key, group);
    }
    group.items.push(item);
  }

  return [...groups.values()];
}
