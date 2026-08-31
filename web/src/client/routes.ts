export type AppRouteId =
  | 'story'
  | 'planning'
  | 'dashboard'
  | 'search'
  | 'activity'
  | 'notifications'
  | 'people'
  | 'profile'
  | 'memoryCreate';
/*
 * Sidebar grouping for the Web client. The App keeps a flat set of primary
 * destinations; the browser sidebar shows all of them at once and needs the
 * grouping to stay readable.
 */
export type AppRouteGroup = 'together' | 'discover' | 'you';

export type AppRouteIcon =
  | 'story'
  | 'planning'
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
  /** Omitted for routes that are offered as an action rather than a section. */
  group?: AppRouteGroup;
}

export const APP_ROUTE_GROUPS = [
  { id: 'together', labelKey: 'navigation.groups.together' },
  { id: 'discover', labelKey: 'navigation.groups.discover' },
  { id: 'you', labelKey: 'navigation.groups.you' },
] as const satisfies readonly { id: AppRouteGroup; labelKey: string }[];

export const APP_ROUTES = [
  {
    id: 'story',
    path: '/story',
    labelKey: 'navigation.story',
    icon: 'story',
    end: true,
    group: 'together',
  },
  {
    id: 'planning',
    path: '/planning',
    labelKey: 'navigation.planning',
    icon: 'planning',
    end: false,
    group: 'together',
  },
  {
    id: 'dashboard',
    path: '/dashboard',
    labelKey: 'navigation.dashboard',
    icon: 'dashboard',
    end: true,
    group: 'together',
  },
  {
    id: 'search',
    path: '/search',
    labelKey: 'navigation.search',
    icon: 'search',
    end: true,
    group: 'discover',
  },
  {
    id: 'activity',
    path: '/activity',
    labelKey: 'navigation.activity',
    icon: 'activity',
    end: true,
    group: 'discover',
  },
  {
    id: 'notifications',
    path: '/notifications',
    labelKey: 'navigation.notifications',
    icon: 'notifications',
    end: true,
    group: 'discover',
  },
  {
    id: 'people',
    path: '/people',
    labelKey: 'navigation.people',
    icon: 'people',
    end: true,
    group: 'you',
  },
  {
    id: 'profile',
    path: '/profile',
    labelKey: 'navigation.profile',
    icon: 'profile',
    end: true,
    group: 'you',
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

/**
 * Destinations of one sidebar group, in declaration order. Routes without a
 * group are offered as an action instead of a section and are not listed here.
 */
export function appRoutesInGroup(
  group: AppRouteGroup,
): readonly AppRouteDefinition[] {
  return (APP_ROUTES as readonly AppRouteDefinition[]).filter(
    (route) => route.group === group,
  );
}
export const MEMORY_DETAIL_ROUTE_PATTERN = '/memory/:memoryId';
export const MEMORY_EDIT_ROUTE_PATTERN = '/memory/:memoryId/edit';
export const HEART_MOMENT_CREATE_ROUTE = '/heart-moment/new';
export const HEART_MOMENT_DETAIL_ROUTE_PATTERN = '/heart-moment/:heartMomentId';
export const HEART_MOMENT_EDIT_ROUTE_PATTERN =
  '/heart-moment/:heartMomentId/edit';
export const MILESTONE_CREATE_ROUTE = '/milestone/new';
export const MILESTONE_DETAIL_ROUTE_PATTERN = '/milestone/:milestoneId';
export const MILESTONE_EDIT_ROUTE_PATTERN = '/milestone/:milestoneId/edit';
export const WISH_DETAIL_ROUTE_PATTERN = '/planning/wishes/:wishId';
export const PLAN_DETAIL_ROUTE_PATTERN = '/planning/plans/:planId';
export const PLACE_DETAIL_ROUTE_PATTERN = '/planning/places/:placeId';
export const CHAPTER_DETAIL_ROUTE_PATTERN = '/planning/chapters/:chapterId';
export const COLLECTION_DETAIL_ROUTE_PATTERN =
  '/planning/collections/:collectionId';

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

export function wishDetailPath(wishId: string): string {
  return `/planning/wishes/${encodeURIComponent(wishId)}`;
}

export function planDetailPath(planId: string): string {
  return `/planning/plans/${encodeURIComponent(planId)}`;
}

export function placeDetailPath(placeId: string): string {
  return `/planning/places/${encodeURIComponent(placeId)}`;
}

export function chapterDetailPath(chapterId: string): string {
  return `/planning/chapters/${encodeURIComponent(chapterId)}`;
}

export function collectionDetailPath(collectionId: string): string {
  return `/planning/collections/${encodeURIComponent(collectionId)}`;
}
