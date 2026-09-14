import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import type { DashboardApi } from '../api/generated/apis/DashboardApi';
import type { DashboardModulePreferenceList } from '../api/generated/models/DashboardModulePreferenceList';
import type { DashboardModulePreferenceView } from '../api/generated/models/DashboardModulePreferenceView';
import {
  DASHBOARD_MODULE_CATALOG,
  type DashboardModuleKey,
} from '../client/dashboardModules';
import {
  dashboardPreferencesQueryKey,
  effectiveUpcomingItemLimit,
  isDashboardModuleVisible,
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

function upsertPreference(
  old: DashboardModulePreferenceList | undefined,
  updated: DashboardModulePreferenceView,
): DashboardModulePreferenceList {
  return {
    items: [
      ...(old?.items.filter((item) => item.moduleKey !== updated.moduleKey) ??
        []),
      updated,
    ],
  };
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
  const [savedModuleKey, setSavedModuleKey] =
    useState<DashboardModuleKey | null>(null);

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
      queryClient.setQueryData<DashboardModulePreferenceList>(queryKey, (old) =>
        upsertPreference(old, updated),
      );
      setPendingLimit(null);
      setSaved(true);
    },
    onError: () => {
      setPendingLimit(null);
      setSaved(false);
    },
  });

  const visibilityMutation = useMutation({
    mutationFn: async ({
      moduleKey,
      visible,
    }: {
      moduleKey: DashboardModuleKey;
      visible: boolean;
    }) => {
      try {
        return await dashboardApi.updateDashboardModulePreference({
          moduleKey,
          spaceId,
          dashboardModulePreferenceUpdate: { visible },
        });
      } catch (error) {
        throw await normalizeClientError(error);
      }
    },
    onMutate: () => {
      setSavedModuleKey(null);
    },
    onSuccess: (updated) => {
      queryClient.setQueryData<DashboardModulePreferenceList>(queryKey, (old) =>
        upsertPreference(old, updated),
      );
      setSavedModuleKey(updated.moduleKey as DashboardModuleKey);
    },
    onError: () => {
      setSavedModuleKey(null);
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

  const visibilityStatus = visibilityMutation.isPending
    ? t('profileIdentity.dashboardModuleSaving')
    : savedModuleKey
      ? t('profileIdentity.dashboardModuleSaved')
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
        className="dashboard-module-preference"
        aria-busy={visibilityMutation.isPending || preferencesQuery.isPending}
      >
        <legend>{t('profileIdentity.dashboardModulesTitle')}</legend>
        <p className="dashboard-module-question">
          {t('profileIdentity.dashboardModulesIntro')}
        </p>
        <div className="dashboard-module-list">
          {DASHBOARD_MODULE_CATALOG.map((entry) => {
            const visible = isDashboardModuleVisible(
              preferencesQuery.data,
              entry.key,
            );
            const isRowPending =
              visibilityMutation.isPending &&
              visibilityMutation.variables?.moduleKey === entry.key;
            return (
              <label key={entry.key} className="dashboard-module-option">
                <span className="dashboard-module-option-label">
                  {t(entry.labelKey)}
                </span>
                <input
                  type="checkbox"
                  checked={visible}
                  disabled={isRowPending || preferencesQuery.isPending}
                  onChange={(event) =>
                    visibilityMutation.mutate({
                      moduleKey: entry.key,
                      visible: event.target.checked,
                    })
                  }
                />
              </label>
            );
          })}
        </div>
      </fieldset>

      {visibilityStatus ? (
        <p className="dashboard-module-status" role="status" aria-live="polite">
          {visibilityStatus}
        </p>
      ) : null}
      {visibilityMutation.error ? (
        <ProblemState error={visibilityMutation.error} />
      ) : null}

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
