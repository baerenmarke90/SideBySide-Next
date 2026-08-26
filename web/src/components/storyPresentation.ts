import type { StoryItem } from '../api/generated/models/StoryItem';

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

function emotionLabel(emotion: string): string {
  switch (emotion) {
    case 'LOVED': return 'Geliebt';
    case 'SEEN': return 'Gesehen';
    case 'APPRECIATED': return 'Wertgeschätzt';
    case 'SUPPORTED': return 'Unterstützt';
    case 'GRATEFUL': return 'Dankbar';
    case 'HAPPY': return 'Glücklich';
    default: return 'Herzmoment';
  }
}

export function storyItemKey(item: StoryItem): string {
  switch (item.kind) {
    case 'MEMORY': return `memory-${item.memory.id}`;
    case 'HEART_MOMENT': return `heart-${item.heartMoment.id}`;
    case 'MILESTONE': return `milestone-${item.milestone.id}`;
  }
}

export function storyItemPresentation(item: StoryItem): StoryPresentation {
  switch (item.kind) {
    case 'MEMORY': {
      const count = item.memory.attachments.length;
      return {
        kindLabel: 'Erinnerung',
        title: item.memory.title,
        author: item.memory.author.displayName,
        mediaLabel: count === 1 ? '1 Foto' : count > 1 ? `${count} Fotos` : undefined,
      };
    }
    case 'HEART_MOMENT':
      return {
        kindLabel: 'Herzmoment',
        title: compactText(item.heartMoment.text),
        preview: emotionLabel(item.heartMoment.emotion),
        author: item.heartMoment.author.displayName,
        mediaLabel: item.heartMoment.attachment ? '1 Foto' : undefined,
        sharedLabel: 'Geteilt',
      };
    case 'MILESTONE':
      return {
        kindLabel: 'Meilenstein',
        title: item.milestone.title,
        author: item.milestone.author.displayName,
      };
  }
}

export function formatStoryDate(date: Date): string {
  return date.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

export function groupStoryItems(items: StoryItem[]): StoryGroup[] {
  const groups = new Map<string, StoryGroup>();

  for (const item of items) {
    const year = item.effectiveDate.getUTCFullYear();
    const month = item.effectiveDate.getUTCMonth() + 1;
    const key = `${year}-${String(month).padStart(2, '0')}`;
    let group = groups.get(key);
    if (!group) {
      group = {
        key,
        label: item.effectiveDate.toLocaleDateString('de-DE', {
          month: 'long',
          year: 'numeric',
          timeZone: 'UTC',
        }),
        items: [],
      };
      groups.set(key, group);
    }
    group.items.push(item);
  }

  return [...groups.values()];
}
