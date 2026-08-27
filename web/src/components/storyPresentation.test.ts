import type { StoryItem } from '../api/generated/models/StoryItem';
import { i18n } from '../i18n';
import { formatStoryDate, groupStoryItems, storyItemPresentation } from './storyPresentation';

function memory(id: string, date: string, title: string, attachmentCount = 0): StoryItem {
  return {
    kind: 'MEMORY',
    effectiveDate: new Date(`${date}T00:00:00Z`),
    memory: {
      id,
      title,
      author: { id: 'author-1', displayName: 'Anna' },
      attachments: Array.from({ length: attachmentCount }, (_, position) => ({ id: `a-${position}`, position })),
    },
  } as unknown as StoryItem;
}

function heart(id: string, date: string): StoryItem {
  return {
    kind: 'HEART_MOMENT',
    effectiveDate: new Date(`${date}T00:00:00Z`),
    heartMoment: {
      id,
      text: 'Danke für den schönen Abend.',
      emotion: 'GRATEFUL',
      author: { id: 'author-2', displayName: 'Ben' },
      attachment: null,
    },
  } as unknown as StoryItem;
}

describe('groupStoryItems', () => {
  it('groups the existing timeline order by calendar month', () => {
    const groups = groupStoryItems([
      memory('m-1', '2026-08-26', 'Sommerabend'),
      heart('h-1', '2026-08-12'),
      memory('m-2', '2026-07-31', 'Ausflug'),
    ], 'de');

    expect(groups.map((group) => group.key)).toEqual(['2026-08', '2026-07']);
    expect(groups[0].label).toBe('August 2026');
    expect(groups[0].items).toHaveLength(2);
    expect(groups[1].items).toHaveLength(1);
  });

  it('formats dates through the requested locale instead of a fixed de-DE value', () => {
    expect(formatStoryDate(new Date('2026-08-26T00:00:00Z'), 'de')).toContain('2026');
    expect(formatStoryDate(new Date('2026-08-26T00:00:00Z'), 'en')).toContain('2026');
  });
});

describe('storyItemPresentation', () => {
  it('keeps Memory cards concise and exposes locale-aware media count', () => {
    expect(storyItemPresentation(memory('m-1', '2026-08-26', 'Am See', 2), i18n.t)).toEqual({
      kindLabel: 'Erinnerung',
      title: 'Am See',
      author: 'Anna',
      mediaLabel: '2 Fotos',
    });
    expect(storyItemPresentation(memory('m-2', '2026-08-26', 'Am See', 1), i18n.t).mediaLabel).toBe('1 Foto');
  });

  it('marks HeartMoments as shared because only shared HeartMoments enter Story', () => {
    expect(storyItemPresentation(heart('h-1', '2026-08-12'), i18n.t)).toMatchObject({
      kindLabel: 'Herzmoment',
      title: 'Danke für den schönen Abend.',
      preview: 'Dankbar',
      author: 'Ben',
      sharedLabel: 'Geteilt',
    });
  });
});
