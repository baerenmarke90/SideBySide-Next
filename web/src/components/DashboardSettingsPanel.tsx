import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { DashboardApi } from '../api/generated/apis/DashboardApi';
import type { DashboardModuleKey } from '../api/generated/models/DashboardModuleKey';
import type { DashboardModulePreferenceList } from '../api/generated/models/DashboardModulePreferenceList';
import {
  dashboardPreferencesQueryKey,
  SHARED_STORY_SUMMARY_MODULE,
} from '../client/dashboardPreferences';
import { useTranslation } from '../i18n';
import { ProblemState } from './ProblemState';

export interface DashboardSettingsPanelProps {
  dashboardApi: DashboardApi;
  spaceId: string;
}

export function DashboardSettingsPanel({
  dashboardApi,
  spaceId,
}: DashboardSettingsPanelProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const queryKey = dashboardPreferencesQueryKey(spaceId);
  const preferenceQuery = useQuery({
    queryKey,
    queryFn: () => dashboardApi.listDashboardModulePreferences({ spaceId }),
    retry: false,
  });

  const mutation = useMutation({
    mutationFn: ({
      moduleKey,
      visible,
    }: {
      moduleKey: DashboardModuleKey;
      visible: boolean;
    }) =>
      dashboardApi.setDashboardModulePreference({
        spaceId,
        moduleKey,
        dashboardModulePreferenceUpdate: { visible },
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData<DashboardModulePreferenceList>(
        queryKey,
        (current) =>
          current
            ? {
                ...current,
                items: current.items.map((item) =>
                  item.moduleKey === updated.moduleKey ? updated : item,
                ),
              }
            : current,
      );
    },
  });

  if (preferenceQuery.isLoading) {
    return (
      <p className="form-hint">
        {t('profileIdentity.dashboardSettingsLoading')}
      </p>
    );
  }
  if (preferenceQuery.error) {
    return (
      <ProblemState
        error={preferenceQuery.error}
        onRetry={() => void preferenceQuery.refetch()}
      />
    );
  }

  return (
    <div className="dashboard-settings-list">
      {preferenceQuery.data?.items.map((item) => {
        const label =
          item.moduleKey === SHARED_STORY_SUMMARY_MODULE
            ? t('profileIdentity.dashboardModuleSharedStorySummary')
            : item.moduleKey;
        const pending =
          mutation.isPending &&
          mutation.variables?.moduleKey === item.moduleKey;
        return (
          <label className="form-checkbox-label" key={item.moduleKey}>
            <input
              type="checkbox"
              checked={item.visible}
              disabled={pending}
              onChange={(event) =>
                mutation.mutate({
                  moduleKey: item.moduleKey,
                  visible: event.target.checked,
                })
              }
            />
            <span>
              <strong>{label}</strong>
              <small>
                {pending
                  ? t('profileIdentity.dashboardSettingsSaving')
                  : t('profileIdentity.dashboardModuleVisibleHelp')}
              </small>
            </span>
          </label>
        );
      })}
      {mutation.error ? <ProblemState error={mutation.error} /> : null}
    </div>
  );
}
