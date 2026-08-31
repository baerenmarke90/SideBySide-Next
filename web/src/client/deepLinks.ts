import { matchPath } from 'react-router-dom';
import {
  PRIVATE_COLLECTIONS_PATH,
  PRIVATE_GIFT_IDEAS_PATH,
  PRIVATE_NOTES_PATH,
  privateCollectionPath,
  privateGiftIdeaPath,
  privateNotePath,
} from './privateArea';
import {
  ACTIVITY_ROUTE,
  appRoutePath,
  CHAPTER_DETAIL_ROUTE_PATTERN,
  COLLECTION_DETAIL_ROUTE_PATTERN,
  HEART_MOMENT_DETAIL_ROUTE_PATTERN,
  MEMORY_DETAIL_ROUTE_PATTERN,
  MILESTONE_DETAIL_ROUTE_PATTERN,
  MORE_NOTIFICATIONS_ROUTE,
  MORE_PEOPLE_ROUTE,
  MORE_PROFILE_ROUTE,
  PLAN_DETAIL_ROUTE_PATTERN,
  PLACE_DETAIL_ROUTE_PATTERN,
  SEARCH_ROUTE,
  WISH_DETAIL_ROUTE_PATTERN,
  chapterDetailPath,
  collectionDetailPath,
  heartMomentDetailPath,
  memoryDetailPath,
  milestoneDetailPath,
  planDetailPath,
  placeDetailPath,
  wishDetailPath,
} from './routes';

export type CanonicalDeepLinkKind =
  | 'memory'
  | 'heartMoment'
  | 'milestone'
  | 'wish'
  | 'plan'
  | 'place'
  | 'chapter'
  | 'collection'
  | 'privateNote'
  | 'giftIdea'
  | 'privateCollection';

const AUTH_RETURN_STORAGE_KEY = 'sidebyside-auth-return-v1';
const AUTH_RETURN_MAX_AGE_MS = 30 * 60 * 1000;

const CANONICAL_RETURN_PATTERNS = [
  appRoutePath('today'),
  ACTIVITY_ROUTE,
  appRoutePath('story'),
  MEMORY_DETAIL_ROUTE_PATTERN,
  '/story/memories/:memoryId/edit',
  HEART_MOMENT_DETAIL_ROUTE_PATTERN,
  '/story/heart-moments/:heartMomentId/edit',
  MILESTONE_DETAIL_ROUTE_PATTERN,
  '/story/milestones/:milestoneId/edit',
  appRoutePath('plan'),
  WISH_DETAIL_ROUTE_PATTERN,
  PLAN_DETAIL_ROUTE_PATTERN,
  PLACE_DETAIL_ROUTE_PATTERN,
  CHAPTER_DETAIL_ROUTE_PATTERN,
  COLLECTION_DETAIL_ROUTE_PATTERN,
  SEARCH_ROUTE,
  appRoutePath('more'),
  MORE_PEOPLE_ROUTE,
  MORE_NOTIFICATIONS_ROUTE,
  MORE_PROFILE_ROUTE,
  PRIVATE_NOTES_PATH,
  `${PRIVATE_NOTES_PATH}/new`,
  `${PRIVATE_NOTES_PATH}/:noteId`,
  `${PRIVATE_NOTES_PATH}/:noteId/edit`,
  PRIVATE_GIFT_IDEAS_PATH,
  `${PRIVATE_GIFT_IDEAS_PATH}/new`,
  `${PRIVATE_GIFT_IDEAS_PATH}/:giftIdeaId`,
  `${PRIVATE_GIFT_IDEAS_PATH}/:giftIdeaId/edit`,
  PRIVATE_COLLECTIONS_PATH,
  `${PRIVATE_COLLECTIONS_PATH}/new`,
  `${PRIVATE_COLLECTIONS_PATH}/:collectionId`,
  `${PRIVATE_COLLECTIONS_PATH}/:collectionId/edit`,
] as const;

export function canonicalDeepLink(
  kind: CanonicalDeepLinkKind,
  resourceId: string,
): string {
  switch (kind) {
    case 'memory':
      return memoryDetailPath(resourceId);
    case 'heartMoment':
      return heartMomentDetailPath(resourceId);
    case 'milestone':
      return milestoneDetailPath(resourceId);
    case 'wish':
      return wishDetailPath(resourceId);
    case 'plan':
      return planDetailPath(resourceId);
    case 'place':
      return placeDetailPath(resourceId);
    case 'chapter':
      return chapterDetailPath(resourceId);
    case 'collection':
      return collectionDetailPath(resourceId);
    case 'privateNote':
      return privateNotePath(resourceId);
    case 'giftIdea':
      return privateGiftIdeaPath(resourceId);
    case 'privateCollection':
      return privateCollectionPath(resourceId);
  }
}

function containsControlCharacter(value: string): boolean {
  for (const character of value) {
    const codePoint = character.codePointAt(0);
    if (codePoint !== undefined && (codePoint < 0x20 || codePoint === 0x7f)) {
      return true;
    }
  }
  return false;
}

export function validateAppRelativeReturnTarget(target: string): string | null {
  if (!target.startsWith('/') || target.startsWith('//')) return null;
  if (target.includes('\\') || containsControlCharacter(target)) return null;
  if (target.includes('?') || target.includes('#')) return null;

  let parsed: URL;
  try {
    parsed = new URL(target, 'https://sidebyside.invalid');
  } catch {
    return null;
  }

  if (parsed.origin !== 'https://sidebyside.invalid') return null;
  if (parsed.pathname !== target) return null;

  const canonical = CANONICAL_RETURN_PATTERNS.some((pattern) =>
    Boolean(matchPath({ path: pattern, end: true }, parsed.pathname)),
  );
  return canonical ? parsed.pathname : null;
}

export function rememberCurrentAuthReturnTarget(): string | null {
  if (typeof window === 'undefined') return null;
  const target = validateAppRelativeReturnTarget(window.location.pathname);
  if (!target) {
    window.localStorage.removeItem(AUTH_RETURN_STORAGE_KEY);
    return null;
  }

  window.localStorage.setItem(
    AUTH_RETURN_STORAGE_KEY,
    JSON.stringify({ path: target, createdAt: Date.now() }),
  );
  return target;
}

export function consumeAuthReturnTarget(now = Date.now()): string | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(AUTH_RETURN_STORAGE_KEY);
  window.localStorage.removeItem(AUTH_RETURN_STORAGE_KEY);
  if (!raw) return null;

  try {
    const stored = JSON.parse(raw) as { path?: unknown; createdAt?: unknown };
    if (typeof stored.path !== 'string' || typeof stored.createdAt !== 'number') {
      return null;
    }
    if (stored.createdAt > now || now - stored.createdAt > AUTH_RETURN_MAX_AGE_MS) {
      return null;
    }
    return validateAppRelativeReturnTarget(stored.path);
  } catch {
    return null;
  }
}

export function restoreAuthReturnTarget(): string | null {
  if (typeof window === 'undefined') return null;
  const target = consumeAuthReturnTarget();
  if (!target || target === window.location.pathname) return target;

  window.history.replaceState(window.history.state, '', target);
  window.dispatchEvent(new PopStateEvent('popstate'));
  return target;
}
