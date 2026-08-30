import { readSensitiveEntryToken, stripSensitiveEntryTokens } from './entryToken';

describe('sensitive identity entry tokens', () => {
  it('prefers a recovery token when conflicting sensitive parameters exist', () => {
    expect(readSensitiveEntryToken('?invite=invite-token&recovery=recovery-token')).toEqual({
      kind: 'recovery',
      token: 'recovery-token',
    });
  });

  it('reads an invitation token without exposing unrelated query state', () => {
    expect(readSensitiveEntryToken('?from=email&invite=invite-token')).toEqual({
      kind: 'invitation',
      token: 'invite-token',
    });
  });

  it('ignores empty sensitive parameters', () => {
    expect(readSensitiveEntryToken('?invite=%20%20')).toBeNull();
  });

  it('removes sensitive parameters while preserving unrelated URL state', () => {
    expect(
      stripSensitiveEntryTokens(
        '/welcome',
        '?invite=secret&from=email&recovery=other-secret',
        '#section',
      ),
    ).toBe('/welcome?from=email#section');
  });
});
