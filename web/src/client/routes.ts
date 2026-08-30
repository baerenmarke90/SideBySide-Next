export type AppRouteId =
  | 'story'
  | 'heartMoments'
  | 'people'
  | 'profile'
  | 'memoryCreate';
export type AppRouteIcon = 'story' | 'heart' | 'people' | 'profile' | 'add';

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
    id: 'heartMoments',
    path: '/heart-moments',
    labelKey: 'm5Product.navigation.heartMoments',
    icon: 'heart',
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
export const HEART_MOMENT_CREATE_ROUTE = '/heart-moments/new';
export const HEART_MOMENT_DETAIL_ROUTE_PATTERN =
  '/heart-moments/:heartMomentId';
export const HEART_MOMENT_EDIT_ROUTE_PATTERN =
  '/heart-moments/:heartMomentId/edit';
export const MILESTONE_CREATE_ROUTE = '/milestones/new';
export const MILESTONE_DETAIL_ROUTE_PATTERN = '/milestones/:milestoneId';
export const MILESTONE_EDIT_ROUTE_PATTERN = '/milestones/:milestoneId/edit';

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
  return `/heart-moments/${encodeURIComponent(heartMomentId)}`;
}

export function heartMomentEditPath(heartMomentId: string): string {
  return `${heartMomentDetailPath(heartMomentId)}/edit`;
}

export function milestoneDetailPath(milestoneId: string): string {
  return `/milestones/${encodeURIComponent(milestoneId)}`;
}

export function milestoneEditPath(milestoneId: string): string {
  return `${milestoneDetailPath(milestoneId)}/edit`;
}
