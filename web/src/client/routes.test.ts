import {
  APP_ROUTES,
  DEFAULT_APP_ROUTE,
  MEMORY_DETAIL_ROUTE_PATTERN,
  MEMORY_EDIT_ROUTE_PATTERN,
  appRoutePath,
  memoryDetailPath,
  memoryEditPath,
} from './routes';

describe('app route registry', () => {
  it('contains only the currently implemented primary authenticated routes', () => {
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

  it('builds encoded memory detail and edit paths', () => {
    expect(MEMORY_DETAIL_ROUTE_PATTERN).toBe('/memory/:memoryId');
    expect(MEMORY_EDIT_ROUTE_PATTERN).toBe('/memory/:memoryId/edit');
    expect(memoryDetailPath('memory/with slash')).toBe(
      '/memory/memory%2Fwith%20slash',
    );
    expect(memoryEditPath('memory-1')).toBe('/memory/memory-1/edit');
  });
});
