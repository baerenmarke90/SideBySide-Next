import {
  dashboardItemPath,
  engagementTargetPath,
  opaqueNextCursor,
  searchResultPath,
} from './m4Product';

describe('M5 S5/S3 product navigation', () => {
  it('links productized search targets and keeps private S4 targets closed', () => {
    expect(searchResultPath('MEMORY', 'memory/with space')).toBe(
      '/memory/memory%2Fwith%20space',
    );
    expect(searchResultPath('HEART_MOMENT', 'heart-id')).toBe('/story');
    expect(searchResultPath('MILESTONE', 'milestone-id')).toBe('/story');
    expect(searchResultPath('WISH', 'wish-id')).toBe('/planning/wishes/wish-id');
    expect(searchResultPath('PLAN', 'plan-id')).toBe('/planning/plans/plan-id');
    expect(searchResultPath('PLACE', 'place-id')).toBe('/planning/places/place-id');
    expect(searchResultPath('CHAPTER', 'chapter-id')).toBe('/planning/chapters/chapter-id');
    expect(searchResultPath('COLLECTION', 'collection-id')).toBe(
      '/planning/collections/collection-id',
    );
    expect(searchResultPath('COLLECTION_ITEM', 'item-id')).toBe('/planning');

    expect(searchResultPath('PRIVATE_NOTE', 'private-id')).toBeNull();
    expect(searchResultPath('GIFT_IDEA', 'gift-id')).toBeNull();
    expect(searchResultPath('PRIVATE_COLLECTION', 'collection-id')).toBeNull();
  });

  it('does not invent direct engagement routes for unsupported target types', () => {
    expect(engagementTargetPath('MEMORY', 'memory-id')).toBe(
      '/memory/memory-id',
    );
    expect(engagementTargetPath('HEART_MOMENT', 'heart-id')).toBe('/story');
    expect(engagementTargetPath('MILESTONE', 'milestone-id')).toBe('/story');

    expect(engagementTargetPath('PLAN', 'plan-id')).toBeNull();
    expect(engagementTargetPath('PLACE', 'place-id')).toBeNull();
    expect(engagementTargetPath(null, 'memory-id')).toBeNull();
    expect(engagementTargetPath('MEMORY', null)).toBeNull();
  });

  it('routes dashboard entries through the productized domain surfaces', () => {
    expect(dashboardItemPath('IMPORTANT_DATE', 'date-id')).toBe('/people');
    expect(dashboardItemPath('BIRTHDAY', 'birthday-id')).toBe('/people');
    expect(dashboardItemPath('ANNIVERSARY', 'anniversary-id')).toBe('/people');
    expect(dashboardItemPath('WISH', 'wish-id')).toBe('/planning/wishes/wish-id');
    expect(dashboardItemPath('PLAN', 'plan-id')).toBe('/planning/plans/plan-id');
    expect(dashboardItemPath('PLACE', 'place-id')).toBe('/planning/places/place-id');
    expect(dashboardItemPath('CHAPTER', 'chapter-id')).toBe('/planning/chapters/chapter-id');
    expect(dashboardItemPath('COLLECTION', 'collection-id')).toBe(
      '/planning/collections/collection-id',
    );
  });
});

describe('M5 S5 cursor handling', () => {
  it('passes opaque cursors through unchanged', () => {
    const cursor = 'opaque+/=cursor.with:punctuation';
    expect(opaqueNextCursor({ nextCursor: cursor })).toBe(cursor);
  });

  it('stops pagination only when the server omits the next cursor', () => {
    expect(opaqueNextCursor({ nextCursor: null })).toBeUndefined();
  });
});