import { QueryClient } from '@tanstack/react-query';
import { invalidateAuthorSummaryConsumers } from './authorSummaryConsumers';

describe('invalidateAuthorSummaryConsumers', () => {
  it('triggers query invalidation on all primary AuthorSummary consumer caches', async () => {
    const queryClient = new QueryClient();
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    await invalidateAuthorSummaryConsumers(queryClient, 'space-123', 'acc-456');

    const calledKeys = invalidateSpy.mock.calls.map(
      (call) => (call[0] as { queryKey: unknown[] }).queryKey,
    );

    expect(calledKeys).toContainEqual(['story', 'space-123']);
    expect(calledKeys).toContainEqual(['m4', 'activity', 'space-123']);
    expect(calledKeys).toContainEqual(['m5-s5', 'dashboard', 'space-123']);
    expect(calledKeys).toContainEqual(['comments', 'space-123']);
    expect(calledKeys).toContainEqual(['m5-s3', 'plans', 'space-123']);
    expect(calledKeys).toContainEqual(['m5-s3', 'wishes', 'space-123']);
    expect(calledKeys).toContainEqual(['m5-s3', 'places', 'space-123']);
    expect(calledKeys).toContainEqual(['m5-s3', 'collections', 'space-123']);
    expect(calledKeys).toContainEqual([
      'profile-identity',
      'space-123',
      'acc-456',
    ]);
  });
});
