import { QueryClient } from '@tanstack/react-query';
import {
  authorSummaryQueryKeys,
  invalidateAuthorSummaryConsumers,
} from './authorSummaryConsumers';

describe('invalidateAuthorSummaryConsumers', () => {
  it('triggers query invalidation on all primary AuthorSummary consumer caches using canonical keys', async () => {
    const queryClient = new QueryClient();
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const spaceId = 'space-123';
    const accountId = 'acc-456';

    await invalidateAuthorSummaryConsumers(queryClient, spaceId, accountId);

    const calledKeys = invalidateSpy.mock.calls.map(
      (call) => (call[0] as { queryKey: unknown[] }).queryKey,
    );

    // Canonical key assertions
    expect(calledKeys).toContainEqual(authorSummaryQueryKeys.story(spaceId));
    expect(calledKeys).toContainEqual(authorSummaryQueryKeys.memory(spaceId));
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.heartMoment(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.milestone(spaceId),
    );
    expect(calledKeys).toContainEqual(authorSummaryQueryKeys.activity(spaceId));
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.legacyActivity(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.dashboard(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.notifications(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.notificationUnreadCount(spaceId),
    );
    expect(calledKeys).toContainEqual(authorSummaryQueryKeys.search(spaceId));
    expect(calledKeys).toContainEqual(authorSummaryQueryKeys.wishes(spaceId));
    expect(calledKeys).toContainEqual(authorSummaryQueryKeys.plans(spaceId));
    expect(calledKeys).toContainEqual(authorSummaryQueryKeys.places(spaceId));
    expect(calledKeys).toContainEqual(authorSummaryQueryKeys.chapters(spaceId));
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.collections(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.relationTargets(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.wishDetail(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.planDetail(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.placeDetail(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.chapterDetail(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.collectionDetail(spaceId),
    );
    expect(calledKeys).toContainEqual(authorSummaryQueryKeys.comments(spaceId));
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.profileIdentity(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.profileIdentity(spaceId, accountId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.partnerIdentity(spaceId),
    );
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.partnerProfile(spaceId),
    );
    expect(calledKeys).toContainEqual(authorSummaryQueryKeys.space(spaceId));
    expect(calledKeys).toContainEqual(
      authorSummaryQueryKeys.spaceProfile(spaceId),
    );

    // Exact key structure regressions: verify actual prefixes match runtime consumers
    expect(calledKeys).toContainEqual(['m5-s5', 'activity', spaceId]);
    expect(calledKeys).toContainEqual(['heartMoment', spaceId]);
    expect(calledKeys).toContainEqual(['m5-s3', 'wish', spaceId]);
    expect(calledKeys).toContainEqual(['m5-s3', 'plan', spaceId]);
    expect(calledKeys).toContainEqual(['m5-s3', 'place', spaceId]);
    expect(calledKeys).toContainEqual(['m5-s3', 'chapter', spaceId]);
    expect(calledKeys).toContainEqual(['m5-s3', 'collection', spaceId]);

    // Regression checks: ensure obsolete prefixes without domain namespaces are not emitted
    expect(calledKeys).not.toContainEqual(['heart-moment', spaceId]);
    expect(calledKeys).not.toContainEqual(['wish', spaceId]);
    expect(calledKeys).not.toContainEqual(['plan', spaceId]);
    expect(calledKeys).not.toContainEqual(['place', spaceId]);
    expect(calledKeys).not.toContainEqual(['collection', spaceId]);
  });
});
