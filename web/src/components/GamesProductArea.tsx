import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { EntitlementsApi } from '../api/generated/apis/EntitlementsApi';
import type { SpaceEntitlementView } from '../api/generated/models/SpaceEntitlementView';
import { Configuration } from '../api/generated/runtime';
import { normalizeClientError } from '../client/problemDetails';
import { useTranslation } from '../i18n';
import { PageHeader } from './PageHeader';
import { ProblemState } from './ProblemState';
import { UiState } from './UiState';

export const GAMES_COUPLE_CAPABILITY = 'games.couple' as const;

const GAME_ENTRIES = [
  'moments',
  'wishes',
  'perspective',
  'happiness',
  'timeTravel',
] as const;

export function GamesProductArea({
  apiBaseUrl,
  accessToken,
  spaceId,
  loadEntitlement,
}: {
  apiBaseUrl: string;
  accessToken: string;
  spaceId: string;
  loadEntitlement?: () => Promise<SpaceEntitlementView>;
}) {
  const { t } = useTranslation();
  const [showPremiumDetails, setShowPremiumDetails] = useState(false);
  const entitlementApi = useMemo(
    () =>
      new EntitlementsApi(
        new Configuration({
          basePath: apiBaseUrl,
          headers: { Authorization: `Bearer ${accessToken}` },
        }),
      ),
    [apiBaseUrl, accessToken],
  );

  const entitlementQuery = useQuery({
    queryKey: ['games-entitlement', spaceId],
    queryFn: async () => {
      try {
        if (loadEntitlement) return await loadEntitlement();
        return await entitlementApi.getSpaceEntitlementsApiV1SpacesSpaceIdEntitlementsGet({
          spaceId,
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });

  const gamesUnlocked = Boolean(
    entitlementQuery.data?.capabilities.includes(GAMES_COUPLE_CAPABILITY),
  );

  return (
    <div className="page games-product-page">
      <PageHeader
        eyebrow={t('games.eyebrow')}
        title={t('games.title')}
        description={t('games.intro')}
        className="games-heading"
      />

      {entitlementQuery.isPending ? (
        <UiState kind="loading" title={t('states.loading.title')} />
      ) : entitlementQuery.error ? (
        <ProblemState
          error={entitlementQuery.error}
          onRetry={() => void entitlementQuery.refetch()}
        />
      ) : (
        <>
          {gamesUnlocked ? (
            <section className="games-access-panel games-access-panel-unlocked">
              <span className="games-premium-badge">{t('games.unlocked.badge')}</span>
              <div>
                <h2>{t('games.unlocked.title')}</h2>
                <p>{t('games.unlocked.body')}</p>
              </div>
            </section>
          ) : (
            <section className="games-access-panel" aria-labelledby="games-premium-heading">
              <span className="games-premium-badge">{t('games.premium.badge')}</span>
              <div className="games-access-copy">
                <h2 id="games-premium-heading">{t('games.premium.title')}</h2>
                <p>{t('games.premium.body')}</p>
              </div>
              <button
                type="button"
                className="games-premium-action"
                aria-expanded={showPremiumDetails}
                aria-controls="games-premium-details"
                onClick={() => setShowPremiumDetails((visible) => !visible)}
              >
                {t('games.premium.action')}
              </button>
              {showPremiumDetails ? (
                <div id="games-premium-details" className="games-premium-details">
                  <strong>{t('games.premium.detailsTitle')}</strong>
                  <p>{t('games.premium.detailsBody')}</p>
                </div>
              ) : null}
            </section>
          )}

          <section className="games-shelf" aria-label={t('games.title')}>
            {GAME_ENTRIES.map((entry, index) => (
              <article className="games-entry" key={entry}>
                <div className="games-entry-index" aria-hidden="true">
                  {String(index + 1).padStart(2, '0')}
                </div>
                <div className="games-entry-copy">
                  <p className="games-entry-role">{t(`games.entries.${entry}.role`)}</p>
                  <h2>{t(`games.entries.${entry}.title`)}</h2>
                  <p>{t(`games.entries.${entry}.description`)}</p>
                </div>
                <span className="games-entry-status">
                  {gamesUnlocked
                    ? t('games.status.comingSoon')
                    : t('games.status.premium')}
                </span>
              </article>
            ))}
          </section>
        </>
      )}
    </div>
  );
}
