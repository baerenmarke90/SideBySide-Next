import {
  APP_ROUTES,
  DEFAULT_APP_ROUTE,
  HEART_MOMENT_CREATE_ROUTE,
  HEART_MOMENT_DETAIL_ROUTE_PATTERN,
  HEART_MOMENT_EDIT_ROUTE_PATTERN,
  MEMORY_DETAIL_ROUTE_PATTERN,
  MEMORY_EDIT_ROUTE_PATTERN,
  MILESTONE_CREATE_ROUTE,
  MILESTONE_DETAIL_ROUTE_PATTERN,
  MILESTONE_EDIT_ROUTE_PATTERN,
  appRoutePath,
  heartMomentDetailPath,
  heartMomentEditPath,
  memoryDetailPath,
  memoryEditPath,
  milestoneDetailPath,
  milestoneEditPath,
} from './routes';

describe('app route registry', () => {
  it('contains only the primary authenticated routes', () => {
    expect(APP_ROUTES.map((route) => route.path)).toEqual([
      '/story',
      '/people',
      '/profile',
      '/memory/new',
    ]);
    expect(DEFAULT_APP_ROUTE).toBe('/story');
  });

  it('resolves primary route paths from stable ids', () => {
    expect(appRoutePath('story')).toBe('/story');
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
});
