import {
  dashboardItemPath,
  engagementTargetPath,
  opaqueNextCursor,
  searchResultPath,
} from './m4Product';

describe('M5 S5 product navigation', () => {
  it('links only already-productized search targets', () => {
    expect(searchResultPath('MEMORY', 'memory/with space')).toBe(
      '/memory/memory%2Fwith%20space',
    );
    expect(searchResultPath('HEART_MOMENT', 'heart-id')).toBe('/story');
    expect(searchResultPath('MILESTONE', 'milestone-id')).toBe('/story');

    expect(searchResultPath('PRIVATE_NOTE', 'private-id')).toBeNull();
    expect(searchResultPath('GIFT_IDEA', 'gift-id')).toBeNull();
    expect(searchResultPath('PRIVATE_COLLECTION', 'collection-id')).toBeNull();
  });

  it('does not invent direct engagement routes for unsupported target types', () => {
    expect(engagementTargetPath('MEMORY', 'memory-id')).toBe('/memory/memory-id');
    expect(engagementTargetPath('HEART_MOMENT', 'heart-id')).toBe('/story');
    expect(engagementTargetPath('MILESTONE', 'milestone-id')).toBe('/story');

    expect(engagementTargetPath('PLAN', 'plan-id')).toBeNull();
    expect(engagementTargetPath('PLACE', 'place-id')).toBeNull();
    expect(engagementTargetPath(null, 'memory-id')).toBeNull();
    expect(engagementTargetPath('MEMORY', null)).toBeNull();
  });

  it('routes date dashboard entries through the already-authorized people surface', () => {
    expect(dashboardItemPath('IMPORTANT_DATE', 'date-id')).toBe('/people');
    expect(dashboardItemPath('BIRTHDAY', 'birthday-id')).toBe('/people');
    expect(dashboardItemPath('ANNIVERSARY', 'anniversary-id')).toBe('/people');
    expect(dashboardItemPath('PLAN', 'plan-id')).toBeNull();
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
