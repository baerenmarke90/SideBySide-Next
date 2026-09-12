import { describe, expect, it } from 'vitest';
import {
  authorDisplayName,
  authorProfileAttachmentId,
} from './authorPresentation';

describe('authorPresentation', () => {
  it('uses localized former-member copy and suppresses avatars from semantic state', () => {
    const author = {
      displayName: '',
      isFormerMember: true,
      profileAttachmentId: 'private-avatar',
    };
    expect(authorDisplayName(author)).toBe('Ehemaliges Mitglied');
    expect(authorProfileAttachmentId(author)).toBeUndefined();
  });
  it('keeps active author identity unchanged', () => {
    const author = {
      displayName: 'Lea Sommer',
      isFormerMember: false,
      profileAttachmentId: 'avatar',
    };
    expect(authorDisplayName(author)).toBe('Lea Sommer');
    expect(authorProfileAttachmentId(author)).toBe('avatar');
  });

  it('does not infer former-member state from the persistence tombstone text', () => {
    const author = { displayName: 'Deleted account', isFormerMember: false };
    expect(authorDisplayName(author)).toBe('Deleted account');
  });
});
