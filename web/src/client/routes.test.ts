import { APP_ROUTES, DEFAULT_APP_ROUTE, appRoutePath } from './routes';

describe('app route registry', () => {
  it('contains only the currently implemented authenticated routes', () => {
    expect(APP_ROUTES.map((route) => route.path)).toEqual([
      '/story',
      '/memory/new',
    ]);
    expect(DEFAULT_APP_ROUTE).toBe('/story');
  });

  it('resolves route paths from stable ids', () => {
    expect(appRoutePath('story')).toBe('/story');
    expect(appRoutePath('memoryCreate')).toBe('/memory/new');
  });
});
