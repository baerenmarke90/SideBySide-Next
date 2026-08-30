import type { AccountMembershipView } from '../api/generated/models/AccountMembershipView';
import { resolveActiveSpaceId } from './spaceContext';

function membership(spaceId: string): AccountMembershipView {
  return { spaceId, role: 'PARTNER', status: 'ACTIVE' };
}

describe('authorized Space context', () => {
  it('selects the first server-authorized Space when none is active yet', () => {
    expect(
      resolveActiveSpaceId([membership('space-a'), membership('space-b')], null),
    ).toBe('space-a');
  });

  it('keeps the current Space while it remains authorized', () => {
    expect(
      resolveActiveSpaceId(
        [membership('space-a'), membership('space-b')],
        'space-b',
      ),
    ).toBe('space-b');
  });

  it('drops stale client state and never returns an unauthorized Space', () => {
    expect(
      resolveActiveSpaceId([membership('space-a')], 'space-removed'),
    ).toBe('space-a');
    expect(resolveActiveSpaceId([], 'space-removed')).toBeNull();
  });
});
