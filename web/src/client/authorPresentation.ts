import { i18n } from '../i18n';

export type PresentableAuthor = {
  displayName: string;
  isFormerMember?: boolean;
  profileAttachmentId?: string | null;
};

export function authorDisplayName(author: PresentableAuthor): string {
  return author.isFormerMember === true
    ? i18n.t('formerMemberLabel')
    : author.displayName;
}

export function authorProfileAttachmentId(
  author: PresentableAuthor,
): string | undefined {
  return author.isFormerMember === true
    ? undefined
    : (author.profileAttachmentId ?? undefined);
}
