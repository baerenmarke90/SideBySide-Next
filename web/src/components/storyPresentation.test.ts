import type { StoryItem } from '../api/generated/models/StoryItem';
import { groupStoryItems, storyItemPresentation } from './storyPresentation';

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
    ]);

    expect(groups.map((group) => group.key)).toEqual(['2026-08', '2026-07']);
    expect(groups[0].items).toHaveLength(2);
    expect(groups[1].items).toHaveLength(1);
  });
});

describe('storyItemPresentation', () => {
  it('keeps Memory cards concise and exposes media count', () => {
    expect(storyItemPresentation(memory('m-1', '2026-08-26', 'Am See', 2))).toEqual({
      kindLabel: 'Erinnerung',
      title: 'Am See',
      author: 'Anna',
      mediaLabel: '2 Fotos',
    });
  });

  it('marks HeartMoments as shared because only shared HeartMoments enter Story', () => {
    expect(storyItemPresentation(heart('h-1', '2026-08-12'))).toMatchObject({
      kindLabel: 'Herzmoment',
      title: 'Danke für den schönen Abend.',
      preview: 'Dankbar',
      author: 'Ben',
      sharedLabel: 'Geteilt',
    });
  });
});
