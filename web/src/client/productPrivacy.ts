import { ContentVisibility } from '../api/generated/models/ContentVisibility';

export type CommentParentKind = 'MEMORY' | 'HEART_MOMENT' | 'MILESTONE';

export function commentsVisibleForParent(
  parentKind: CommentParentKind,
  visibility?: ContentVisibility,
): boolean {
  if (parentKind !== 'HEART_MOMENT') return true;
  return visibility === ContentVisibility.SHARED;
}
