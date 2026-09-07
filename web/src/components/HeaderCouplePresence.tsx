import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { Configuration } from '../api/generated/runtime';
import { authorSummaryQueryKeys } from '../client/authorSummaryConsumers';
import { normalizeClientError } from '../client/problemDetails';
import { PartnerAvatarPair } from './PartnerAvatarPair';

/**
 * Quiet header signal that both partners share this Space, distinct from the
 * account menu (HeaderProfileMenu) which stays "my account" only.
 */
export function HeaderCouplePresence({
  apiBaseUrl,
  accessToken,
  account,
  spaceId,
}: {
  apiBaseUrl: string;
  accessToken: string;
  account: AccountView;
  spaceId: string;
}) {
  const configuration = useMemo(
    () =>
      new Configuration({
        basePath: apiBaseUrl,
        headers: { Authorization: `Bearer ${accessToken}` },
      }),
    [accessToken, apiBaseUrl],
  );
  const spacesApi = useMemo(
    () => new SpacesApi(configuration),
    [configuration],
  );

  const spaceQuery = useQuery({
    queryKey: authorSummaryQueryKeys.space(spaceId),
    queryFn: async () => {
      try {
        return await spacesApi.getSpaceApiV1SpacesSpaceIdGet({ spaceId });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    enabled: Boolean(spaceId && accessToken),
    retry: false,
  });

  const partner = spaceQuery.data?.partners.find(
    (candidate) => candidate.id !== account.id,
  );

  // Only a resolved partner is worth a couple-presence signal: with none, this
  // would just duplicate the account's own avatar next to a dashed invite
  // placeholder, which reads as a broken button rather than "no partner yet".
  if (!partner) return null;

  return (
    <PartnerAvatarPair
      className="header-couple-presence"
      primaryPerson={{ displayName: account.displayName }}
      secondaryPerson={{ displayName: partner.displayName }}
      size="small"
      status="connected"
    />
  );
}
