export type AppRouteId =
  | 'story'
  | 'dashboard'
  | 'search'
  | 'activity'
  | 'notifications'
  | 'people'
  | 'profile'
  | 'memoryCreate';
export type AppRouteIcon =
  | 'story'
  | 'dashboard'
  | 'search'
  | 'activity'
  | 'notifications'
  | 'people'
  | 'profile'
  | 'add';

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
    id: 'dashboard',
    path: '/dashboard',
    labelKey: 'navigation.dashboard',
    icon: 'dashboard',
    end: true,
  },
  {
    id: 'search',
    path: '/search',
    labelKey: 'navigation.search',
    icon: 'search',
    end: true,
  },
  {
    id: 'activity',
    path: '/activity',
    labelKey: 'navigation.activity',
    icon: 'activity',
    end: true,
  },
  {
    id: 'notifications',
    path: '/notifications',
    labelKey: 'navigation.notifications',
    icon: 'notifications',
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
export const HEART_MOMENT_CREATE_ROUTE = '/heart-moment/new';
export const HEART_MOMENT_DETAIL_ROUTE_PATTERN = '/heart-moment/:heartMomentId';
export const HEART_MOMENT_EDIT_ROUTE_PATTERN =
  '/heart-moment/:heartMomentId/edit';
export const MILESTONE_CREATE_ROUTE = '/milestone/new';
export const MILESTONE_DETAIL_ROUTE_PATTERN = '/milestone/:milestoneId';
export const MILESTONE_EDIT_ROUTE_PATTERN = '/milestone/:milestoneId/edit';

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

export function heartMomentDetailPath(heartMomentId: string): string {
  return `/heart-moment/${encodeURIComponent(heartMomentId)}`;
}

export function heartMomentEditPath(heartMomentId: string): string {
  return `${heartMomentDetailPath(heartMomentId)}/edit`;
}

export function milestoneDetailPath(milestoneId: string): string {
  return `/milestone/${encodeURIComponent(milestoneId)}`;
}

export function milestoneEditPath(milestoneId: string): string {
  return `${milestoneDetailPath(milestoneId)}/edit`;
}
