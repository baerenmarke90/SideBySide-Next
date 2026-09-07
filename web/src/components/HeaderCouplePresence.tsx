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

  if (!spaceQuery.data) return null;

  const partner =
    spaceQuery.data.partners.find((candidate) => candidate.id !== account.id) ??
    null;

  return (
    <PartnerAvatarPair
      className="header-couple-presence"
      primaryPerson={{ displayName: account.displayName }}
      secondaryPerson={partner ? { displayName: partner.displayName } : null}
      size="small"
      status={partner ? 'connected' : 'waiting'}
    />
  );
}
