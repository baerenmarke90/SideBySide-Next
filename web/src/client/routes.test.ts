import {
  APP_ROUTES,
  CHAPTER_DETAIL_ROUTE_PATTERN,
  COLLECTION_DETAIL_ROUTE_PATTERN,
  DEFAULT_APP_ROUTE,
  HEART_MOMENT_CREATE_ROUTE,
  HEART_MOMENT_DETAIL_ROUTE_PATTERN,
  HEART_MOMENT_EDIT_ROUTE_PATTERN,
  MEMORY_DETAIL_ROUTE_PATTERN,
  MEMORY_EDIT_ROUTE_PATTERN,
  MILESTONE_CREATE_ROUTE,
  MILESTONE_DETAIL_ROUTE_PATTERN,
  MILESTONE_EDIT_ROUTE_PATTERN,
  PLAN_DETAIL_ROUTE_PATTERN,
  PLACE_DETAIL_ROUTE_PATTERN,
  WISH_DETAIL_ROUTE_PATTERN,
  appRoutePath,
  chapterDetailPath,
  collectionDetailPath,
  heartMomentDetailPath,
  heartMomentEditPath,
  memoryDetailPath,
  memoryEditPath,
  milestoneDetailPath,
  milestoneEditPath,
  planDetailPath,
  placeDetailPath,
  wishDetailPath,
} from './routes';

describe('app route registry', () => {
  it('contains only the primary authenticated routes', () => {
    expect(APP_ROUTES.map((route) => route.path)).toEqual([
      '/story',
      '/planning',
      '/dashboard',
      '/search',
      '/activity',
      '/notifications',
      '/people',
      '/profile',
      '/memory/new',
    ]);
    expect(DEFAULT_APP_ROUTE).toBe('/story');
  });

  it('resolves primary route paths from stable ids', () => {
    expect(appRoutePath('story')).toBe('/story');
    expect(appRoutePath('planning')).toBe('/planning');
    expect(appRoutePath('dashboard')).toBe('/dashboard');
    expect(appRoutePath('search')).toBe('/search');
    expect(appRoutePath('activity')).toBe('/activity');
    expect(appRoutePath('notifications')).toBe('/notifications');
    expect(appRoutePath('people')).toBe('/people');
    expect(appRoutePath('profile')).toBe('/profile');
    expect(appRoutePath('memoryCreate')).toBe('/memory/new');
  });

  it('builds encoded story-product detail and edit paths', () => {
    expect(MEMORY_DETAIL_ROUTE_PATTERN).toBe('/memory/:memoryId');
    expect(MEMORY_EDIT_ROUTE_PATTERN).toBe('/memory/:memoryId/edit');
    expect(memoryDetailPath('memory/with slash')).toBe(
      '/memory/memory%2Fwith%20slash',
    );
    expect(memoryEditPath('memory-1')).toBe('/memory/memory-1/edit');

    expect(HEART_MOMENT_CREATE_ROUTE).toBe('/heart-moment/new');
    expect(HEART_MOMENT_DETAIL_ROUTE_PATTERN).toBe(
      '/heart-moment/:heartMomentId',
    );
    expect(HEART_MOMENT_EDIT_ROUTE_PATTERN).toBe(
      '/heart-moment/:heartMomentId/edit',
    );
    expect(heartMomentDetailPath('heart/moment')).toBe(
      '/heart-moment/heart%2Fmoment',
    );
    expect(heartMomentEditPath('heart-1')).toBe('/heart-moment/heart-1/edit');

    expect(MILESTONE_CREATE_ROUTE).toBe('/milestone/new');
    expect(MILESTONE_DETAIL_ROUTE_PATTERN).toBe('/milestone/:milestoneId');
    expect(MILESTONE_EDIT_ROUTE_PATTERN).toBe('/milestone/:milestoneId/edit');
    expect(milestoneDetailPath('mile/stone')).toBe('/milestone/mile%2Fstone');
    expect(milestoneEditPath('milestone-1')).toBe(
      '/milestone/milestone-1/edit',
    );
  });

  it('builds encoded shared-planning deep links', () => {
    expect(WISH_DETAIL_ROUTE_PATTERN).toBe('/planning/wishes/:wishId');
    expect(PLAN_DETAIL_ROUTE_PATTERN).toBe('/planning/plans/:planId');
    expect(PLACE_DETAIL_ROUTE_PATTERN).toBe('/planning/places/:placeId');
    expect(CHAPTER_DETAIL_ROUTE_PATTERN).toBe('/planning/chapters/:chapterId');
    expect(COLLECTION_DETAIL_ROUTE_PATTERN).toBe(
      '/planning/collections/:collectionId',
    );
    expect(wishDetailPath('wish/one')).toBe('/planning/wishes/wish%2Fone');
    expect(planDetailPath('plan one')).toBe('/planning/plans/plan%20one');
    expect(placeDetailPath('place-1')).toBe('/planning/places/place-1');
    expect(chapterDetailPath('chapter-1')).toBe('/planning/chapters/chapter-1');
    expect(collectionDetailPath('collection-1')).toBe(
      '/planning/collections/collection-1',
    );
  });
});