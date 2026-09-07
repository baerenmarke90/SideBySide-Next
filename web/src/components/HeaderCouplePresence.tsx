import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { Configuration } from '../api/generated/runtime';
import { authorSummaryQueryKeys } from '../client/authorSummaryConsumers';
import { normalizeClientError } from '../client/problemDetails';
import { useTranslation } from '../i18n';
import { PersonIdentity } from './PersonIdentity';

/**
 * Quiet header signal that the partner shares this Space. The account's own
 * avatar already lives in HeaderProfileMenu right next to this, so this only
 * ever renders the partner — never the account a second time.
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
  const { t } = useTranslation();
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

  // Only a resolved partner is worth a couple-presence signal: with none,
  // there is nothing distinct from the account's own avatar to show.
  if (!partner) return null;

  return (
    <span className="header-couple-presence" title={partner.displayName}>
      <PersonIdentity
        displayName={partner.displayName}
        size="small"
        showName={false}
        imageAlt={t('profileIdentity.imageAlt', { name: partner.displayName })}
        fallbackAlt={t('profileIdentity.fallbackAlt', {
          name: partner.displayName,
        })}
      />
    </span>
  );
}
