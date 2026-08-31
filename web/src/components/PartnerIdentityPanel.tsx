import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ProfilesApi } from '../api/generated/apis/ProfilesApi';
import { SpacesApi } from '../api/generated/apis/SpacesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { Configuration } from '../api/generated/runtime';
import { normalizeClientError } from '../client/problemDetails';
import { useProfileAvatarUrl } from '../client/useProfileAvatarUrl';
import { useTranslation } from '../i18n';
import { PersonIdentity } from './PersonIdentity';
import { ProblemState } from './ProblemState';

export function PartnerIdentityPanel({
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
  const spacesApi = useMemo(() => new SpacesApi(configuration), [configuration]);
  const profilesApi = useMemo(() => new ProfilesApi(configuration), [configuration]);

  const spaceQuery = useQuery({
    queryKey: ['space', spaceId],
    queryFn: async () => {
      try {
        return await spacesApi.getSpaceApiV1SpacesSpaceIdGet({ spaceId });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });

  const partner =
    spaceQuery.data?.partners.find((candidate) => candidate.id !== account.id) ?? null;
  const partnerId = partner?.id ?? '';
  const profileQuery = useQuery({
    queryKey: ['partner-profile', spaceId, partnerId],
    queryFn: async () => {
      try {
        return await profilesApi.getPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGet({
          accountId: partnerId,
          spaceId,
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    enabled: partnerId.length > 0,
    retry: false,
  });

  const { avatarUrl, loadFailed } = useProfileAvatarUrl(
    profilesApi,
    spaceId,
    partnerId,
    profileQuery.data?.profileAttachmentId,
  );

  if (!partner) return null;

  const displayName = profileQuery.data?.displayName ?? partner.displayName;
  return (
    <section className="form-card profile-identity-panel" aria-labelledby="partner-identity-title">
      <div>
        <h2 id="partner-identity-title">{t('profileIdentity.partnerTitle')}</h2>
        <p>{t('profileIdentity.partnerIntro')}</p>
      </div>
      {profileQuery.error ? (
        <ProblemState error={profileQuery.error} onRetry={() => void profileQuery.refetch()} />
      ) : (
        <PersonIdentity
          displayName={displayName}
          imageUrl={avatarUrl}
          size="large"
          imageAlt={t('profileIdentity.imageAlt', { name: displayName })}
          fallbackAlt={t('profileIdentity.fallbackAlt', { name: displayName })}
        />
      )}
      {loadFailed ? (
        <p className="field-help profile-identity-status" role="status">
          {t('profileIdentity.loadAvatarFailed')}
        </p>
      ) : null}
    </section>
  );
}
