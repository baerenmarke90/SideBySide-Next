import { InstanceApi } from '../api/generated/apis/InstanceApi';
import type { InstanceAccessStatus } from '../api/generated/models/InstanceAccessStatus';
import { Configuration } from '../api/generated/runtime';

export type RegistrationAvailability =
  | 'available'
  | 'administrator'
  | 'maintenance'
  | 'unreachable';

export function classifyRegistrationAvailability(
  status: InstanceAccessStatus,
): RegistrationAvailability {
  if (
    status.maintenanceMode ||
    status.registrationUnavailableReason === 'maintenance'
  ) {
    return 'maintenance';
  }
  if (status.registrationAvailable) return 'available';
  if (status.registrationUnavailableReason === 'administrator') {
    return 'administrator';
  }
  return 'unreachable';
}

export async function loadRegistrationAvailability(
  apiBaseUrl: string,
  loadStatus?: () => Promise<InstanceAccessStatus>,
): Promise<RegistrationAvailability> {
  try {
    const operation =
      loadStatus ??
      (() =>
        new InstanceApi(
          new Configuration({ basePath: apiBaseUrl }),
        ).instanceStatusApiV1InstanceStatusGet());
    return classifyRegistrationAvailability(await operation());
  } catch {
    return 'unreachable';
  }
}
