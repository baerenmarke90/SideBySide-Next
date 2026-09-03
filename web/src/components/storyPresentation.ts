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

export function storyItemKey(item: StoryItem): string {
  switch (item.kind) {
    case 'MEMORY':
      return `memory-${item.memory.id}`;
    case 'HEART_MOMENT':
      return `heart-${item.heartMoment.id}`;
    case 'MILESTONE':
      return `milestone-${item.milestone.id}`;
  }
}

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
