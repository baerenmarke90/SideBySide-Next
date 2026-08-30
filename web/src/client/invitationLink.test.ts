import { buildInvitationLink } from './invitationLink';

describe('invitation link mapping', () => {
  it('uses the existing invitation entry route and URL-encodes the secret token', () => {
    const link = buildInvitationLink(
      'https://sidebyside.example',
      'secret+token/with?symbols=1',
    );
    const url = new URL(link);

    expect(url.origin).toBe('https://sidebyside.example');
    expect(url.pathname).toBe('/auth/invitation');
    expect(url.searchParams.get('token')).toBe('secret+token/with?symbols=1');
  });
});
