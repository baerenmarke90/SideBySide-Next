import { DashboardModuleKey } from '../api/generated/models/DashboardModuleKey';

export const dashboardPreferencesQueryKey = (spaceId: string) =>
  ['m5-s5', 'dashboard-preferences', spaceId] as const;

export const SHARED_STORY_SUMMARY_MODULE =
  DashboardModuleKey.SHARED_STORY_SUMMARY;
