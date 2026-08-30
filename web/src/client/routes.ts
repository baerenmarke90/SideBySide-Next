export type AppRouteId = 'story' | 'people' | 'profile' | 'memoryCreate';
export type AppRouteIcon = 'story' | 'people' | 'profile' | 'add';

export interface AppRouteDefinition {
  id: AppRouteId;
  path: string;
  labelKey: string;
  icon: AppRouteIcon;
  end: boolean;
}

export const APP_ROUTES = [
  {
    id: 'story',
    path: '/story',
    labelKey: 'navigation.story',
    icon: 'story',
    end: true,
  },
  {
    id: 'people',
    path: '/people',
    labelKey: 'navigation.people',
    icon: 'people',
    end: true,
  },
  {
    id: 'profile',
    path: '/profile',
    labelKey: 'navigation.profile',
    icon: 'profile',
    end: true,
  },
  {
    id: 'memoryCreate',
    path: '/memory/new',
    labelKey: 'navigation.newMemory',
    icon: 'add',
    end: true,
  },
] as const satisfies readonly AppRouteDefinition[];

export const DEFAULT_APP_ROUTE = APP_ROUTES[0].path;
export const MEMORY_DETAIL_ROUTE_PATTERN = '/memory/:memoryId';
export const MEMORY_EDIT_ROUTE_PATTERN = '/memory/:memoryId/edit';

export function appRoutePath(id: AppRouteId): string {
  const route = APP_ROUTES.find((candidate) => candidate.id === id);
  if (!route) throw new Error(`Unknown app route: ${id}`);
  return route.path;
}

export function memoryDetailPath(memoryId: string): string {
  return `/memory/${encodeURIComponent(memoryId)}`;
}

export function memoryEditPath(memoryId: string): string {
  return `${memoryDetailPath(memoryId)}/edit`;
}
