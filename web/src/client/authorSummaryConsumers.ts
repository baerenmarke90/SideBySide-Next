import type { QueryClient } from '@tanstack/react-query';

/**
 * Centrally invalidates all TanStack Query caches that consume AuthorSummary projections.
 *
 * When an account's displayName or profileAttachmentId changes, this helper ensures
 * that all timelines, activity logs, dashboards, comments, and collaborative items
 * in the space immediately refetch the fresh author identity.
 */
export async function invalidateAuthorSummaryConsumers(
  queryClient: QueryClient,
  spaceId: string,
  accountId?: string,
): Promise<void> {
  const invalidations = [
    queryClient.invalidateQueries({ queryKey: ['profile-identity', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['partner-identity', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['partner-profile', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['space', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['space-profile', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['story', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['memory', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['heart-moment', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['milestone', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['m4', 'activity', spaceId] }),
    queryClient.invalidateQueries({
      queryKey: ['m5-s5', 'dashboard', spaceId],
    }),
    queryClient.invalidateQueries({
      queryKey: ['m5-s5', 'notifications', spaceId],
    }),
    queryClient.invalidateQueries({ queryKey: ['m5-s3', 'wishes', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['m5-s3', 'plans', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['m5-s3', 'places', spaceId] }),
    queryClient.invalidateQueries({
      queryKey: ['m5-s3', 'chapters', spaceId],
    }),
    queryClient.invalidateQueries({
      queryKey: ['m5-s3', 'collections', spaceId],
    }),
    queryClient.invalidateQueries({ queryKey: ['wish', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['plan', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['place', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['collection', spaceId] }),
    queryClient.invalidateQueries({ queryKey: ['comments', spaceId] }),
  ];

  if (accountId) {
    invalidations.push(
      queryClient.invalidateQueries({
        queryKey: ['profile-identity', spaceId, accountId],
      }),
    );
  }

  await Promise.all(invalidations);
}
