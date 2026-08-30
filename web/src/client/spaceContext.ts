import type { AccountMembershipView } from '../api/generated/models/AccountMembershipView';
import { normalizeClientError } from './problemDetails';
import { createReferenceApis } from './referenceFlow';

export async function loadAuthorizedMemberships(
  apiBaseUrl: string,
  accessToken: string,
): Promise<AccountMembershipView[]> {
  try {
    return await createReferenceApis(
      apiBaseUrl,
      accessToken,
    ).auth.listAccountMembershipsApiV1AuthMembershipsGet();
  } catch (error) {
    throw await normalizeClientError(error);
  }
}

/**
 * Resolve an active Space exclusively from the server-authorized Membership set.
 * Existing client state is retained only while that Space remains authorized.
 */
export function resolveActiveSpaceId(
  memberships: AccountMembershipView[],
  currentSpaceId: string | null,
): string | null {
  if (
    currentSpaceId &&
    memberships.some((membership) => membership.spaceId === currentSpaceId)
  ) {
    return currentSpaceId;
  }

  return memberships[0]?.spaceId ?? null;
}
