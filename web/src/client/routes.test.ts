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
  it('contains only the currently implemented primary authenticated routes', () => {
    expect(APP_ROUTES.map((route) => route.path)).toEqual([
      '/story',
      '/heart-moments',
      '/people',
      '/profile',
      '/memory/new',
    ]);
    expect(DEFAULT_APP_ROUTE).toBe('/story');
  });

  it('resolves primary route paths from stable ids', () => {
    expect(appRoutePath('story')).toBe('/story');
    expect(appRoutePath('heartMoments')).toBe('/heart-moments');
    expect(appRoutePath('people')).toBe('/people');
    expect(appRoutePath('profile')).toBe('/profile');
    expect(appRoutePath('memoryCreate')).toBe('/memory/new');
  });

  it('builds encoded Memory detail and edit paths', () => {
    expect(MEMORY_DETAIL_ROUTE_PATTERN).toBe('/memory/:memoryId');
    expect(MEMORY_EDIT_ROUTE_PATTERN).toBe('/memory/:memoryId/edit');
    expect(memoryDetailPath('memory/with slash')).toBe(
      '/memory/memory%2Fwith%20slash',
    );
    expect(memoryEditPath('memory-1')).toBe('/memory/memory-1/edit');
  });

  it('builds stable HeartMoment and Milestone deep links', () => {
    expect(HEART_MOMENT_CREATE_ROUTE).toBe('/heart-moments/new');
    expect(HEART_MOMENT_DETAIL_ROUTE_PATTERN).toBe(
      '/heart-moments/:heartMomentId',
    );
    expect(HEART_MOMENT_EDIT_ROUTE_PATTERN).toBe(
      '/heart-moments/:heartMomentId/edit',
    );
    expect(heartMomentDetailPath('heart/1')).toBe('/heart-moments/heart%2F1');
    expect(heartMomentEditPath('heart-1')).toBe('/heart-moments/heart-1/edit');

    expect(MILESTONE_CREATE_ROUTE).toBe('/milestones/new');
    expect(MILESTONE_DETAIL_ROUTE_PATTERN).toBe('/milestones/:milestoneId');
    expect(MILESTONE_EDIT_ROUTE_PATTERN).toBe('/milestones/:milestoneId/edit');
    expect(milestoneDetailPath('milestone/1')).toBe(
      '/milestones/milestone%2F1',
    );
    expect(milestoneEditPath('milestone-1')).toBe(
      '/milestones/milestone-1/edit',
    );
  });
});
