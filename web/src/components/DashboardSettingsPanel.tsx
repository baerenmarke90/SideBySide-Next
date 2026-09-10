import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import type { DashboardApi } from '../api/generated/apis/DashboardApi';
import type { DashboardModulePreferenceList } from '../api/generated/models/DashboardModulePreferenceList';
import {
  dashboardPreferencesQueryKey,
  effectiveUpcomingItemLimit,
  type UpcomingItemLimit,
  UPCOMING_ITEM_LIMITS,
  UPCOMING_MODULE_KEY,
} from '../client/dashboardPreferences';
import { normalizeClientError } from '../client/problemDetails';
import { useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';

export interface DashboardSettingsPanelProps {
  dashboardApi: DashboardApi;
  accountId: string;
  spaceId: string;
}

export function DashboardSettingsPanel({
  dashboardApi,
  accountId,
  spaceId,
}: DashboardSettingsPanelProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const queryKey = dashboardPreferencesQueryKey(accountId, spaceId);
  const [pendingLimit, setPendingLimit] = useState<UpcomingItemLimit | null>(
    null,
  );
  const [saved, setSaved] = useState(false);

  const preferencesQuery = useQuery({
    queryKey,
    queryFn: async () => {
      try {
        return await dashboardApi.listDashboardModulePreferences({ spaceId });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    retry: false,
  });

  const mutation = useMutation({
    mutationFn: async (itemLimit: UpcomingItemLimit) => {
      try {
        return await dashboardApi.updateDashboardModulePreference({
          moduleKey: UPCOMING_MODULE_KEY,
          spaceId,
          dashboardModulePreferenceUpdate: { itemLimit },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onMutate: (itemLimit) => {
      setPendingLimit(itemLimit);
      setSaved(false);
    },
    onSuccess: (updated) => {
      queryClient.setQueryData<DashboardModulePreferenceList>(
        queryKey,
        (old) => ({
          items: [
            ...(old?.items.filter(
              (item) => item.moduleKey !== UPCOMING_MODULE_KEY,
            ) ?? []),
            updated,
          ],
        }),
      );
      setPendingLimit(null);
      setSaved(true);
    },
    onError: () => {
      setPendingLimit(null);
      setSaved(false);
    },
  });

  const confirmedLimit = effectiveUpcomingItemLimit(preferencesQuery.data);
  const selectedLimit = pendingLimit ?? confirmedLimit;
  const status = mutation.isPending
    ? t('profileIdentity.dashboardUpcomingSaving')
    : saved
      ? t('profileIdentity.dashboardUpcomingSaved')
      : preferencesQuery.isPending
        ? t('profileIdentity.dashboardUpcomingLoading')
        : null;

  return (
    <section
      id="settings-dashboard"
      className="settings-section settings-dashboard-panel"
      aria-labelledby="settings-dashboard-heading"
    >
      <div className="settings-section-head">
        <h2 id="settings-dashboard-heading">
          {t('profileIdentity.settingsDashboard')}
        </h2>
        <p className="settings-section-intro">
          {t('profileIdentity.settingsDashboardIntro')}
        </p>
      </div>

      <fieldset
        className="dashboard-upcoming-preference"
        aria-busy={mutation.isPending || preferencesQuery.isPending}
      >
        <legend>{t('profileIdentity.dashboardUpcomingTitle')}</legend>
        <p className="dashboard-upcoming-question">
          {t('profileIdentity.dashboardUpcomingQuestion')}
        </p>
        <div className="dashboard-upcoming-options">
          {UPCOMING_ITEM_LIMITS.map((itemLimit) => (
            <label
              key={itemLimit}
              className={
                selectedLimit === itemLimit
                  ? 'dashboard-upcoming-option is-selected'
                  : 'dashboard-upcoming-option'
              }
            >
              <input
                type="radio"
                name="dashboardUpcomingItemLimit"
                value={itemLimit}
                checked={selectedLimit === itemLimit}
                disabled={mutation.isPending || preferencesQuery.isPending}
                onChange={() => mutation.mutate(itemLimit)}
              />
              <span>{itemLimit}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {status ? (
        <p
          className="dashboard-upcoming-status"
          role="status"
          aria-live="polite"
        >
          {status}
        </p>
      ) : null}

      {preferencesQuery.error ? (
        <ProblemState
          error={preferencesQuery.error}
          onRetry={() => void preferencesQuery.refetch()}
        />
      ) : null}
      {mutation.error ? <ProblemState error={mutation.error} /> : null}
    </section>
  );
}
