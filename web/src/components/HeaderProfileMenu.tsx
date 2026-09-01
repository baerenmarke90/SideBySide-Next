import { useMemo, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ProfilesApi } from '../api/generated/apis/ProfilesApi';
import type { AccountView } from '../api/generated/models/AccountView';
import { Configuration } from '../api/generated/runtime';
import {
  ACTIVITY_ROUTE,
  MORE_PROFILE_ROUTE,
  SERVER_ADMIN_ROUTE,
} from '../client/routes';
import { useProfileAvatarUrl } from '../client/useProfileAvatarUrl';
import { useTranslation } from '../i18n';
import { DestinationIcon } from './DestinationIcon';
import { PersonIdentity } from './PersonIdentity';

/**
 * Compact account/profile utility for the persistent Web header.
 *
 * It shares the authoritative #368 profile query key and avatar loader so the
 * header updates when profile identity changes without introducing a second
 * identity representation or a public media URL.
 */
export function HeaderProfileMenu({
  apiBaseUrl,
  accessToken,
  account,
  spaceId,
  serverAdmin,
  onLogout,
}: {
  apiBaseUrl: string;
  accessToken: string;
  account: AccountView;
  spaceId: string;
  serverAdmin: boolean;
  onLogout: () => void;
}) {
  const { t } = useTranslation();
  const detailsRef = useRef<HTMLDetailsElement>(null);
  const configuration = useMemo(
    () =>
      new Configuration({
        basePath: apiBaseUrl,
        headers: { Authorization: `Bearer ${accessToken}` },
      }),
    [accessToken, apiBaseUrl],
  );
  const profilesApi = useMemo(
    () => new ProfilesApi(configuration),
    [configuration],
  );
  const profileQuery = useQuery({
    queryKey: ['profile-identity', spaceId, account.id],
    queryFn: () =>
      profilesApi.getPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGet({
        accountId: account.id,
        spaceId,
      }),
    retry: false,
  });
  const profile = profileQuery.data;
  const displayName = profile?.displayName ?? account.displayName;
  const { avatarUrl } = useProfileAvatarUrl(
    profilesApi,
    spaceId,
    account.id,
    profile?.profileAttachmentId,
  );

  function closeMenu() {
    detailsRef.current?.removeAttribute('open');
  }

  return (
    <details
      ref={detailsRef}
      className="header-profile-menu"
      onKeyDown={(event) => {
        if (event.key === 'Escape') {
          closeMenu();
          detailsRef.current?.querySelector<HTMLElement>('summary')?.focus();
        }
      }}
    >
      <summary
        className="header-profile-trigger"
        aria-label={t('navigation.profileMenu')}
        title={t('navigation.profileMenu')}
      >
        <PersonIdentity
          displayName={displayName}
          imageUrl={avatarUrl}
          size="small"
          showName={false}
          imageAlt={t('profileIdentity.imageAlt', { name: displayName })}
          fallbackAlt={t('profileIdentity.fallbackAlt', { name: displayName })}
        />
      </summary>
      <nav
        className="header-profile-popover"
        aria-label={t('navigation.profileMenu')}
      >
        <Link
          className="header-profile-menu-item"
          to={MORE_PROFILE_ROUTE}
          onClick={closeMenu}
        >
          <span className="shell-nav-icon" aria-hidden="true">
            <DestinationIcon icon="profile" />
          </span>
          <span>{t('navigation.profile')}</span>
        </Link>
        <Link
          className="header-profile-menu-item"
          to={ACTIVITY_ROUTE}
          onClick={closeMenu}
        >
          <span className="shell-nav-icon" aria-hidden="true">
            <DestinationIcon icon="activity" />
          </span>
          <span>{t('navigation.activity')}</span>
        </Link>
        {serverAdmin ? (
          <Link
            className="header-profile-menu-item"
            to={SERVER_ADMIN_ROUTE}
            onClick={closeMenu}
          >
            <span className="shell-nav-icon" aria-hidden="true">
              <DestinationIcon icon="more" />
            </span>
            <span>{t('serverAdmin.title')}</span>
          </Link>
        ) : null}
        <button
          type="button"
          className="header-profile-menu-item header-profile-menu-logout"
          onClick={() => {
            closeMenu();
            onLogout();
          }}
        >
          <span>{t('header.logout')}</span>
        </button>
      </nav>
    </details>
  );
}
