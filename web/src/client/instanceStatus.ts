import { InstanceApi } from '../api/generated/apis/InstanceApi';
import type { AuthCapabilities } from '../api/generated/models/AuthCapabilities';
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

export interface InstanceStatusResult {
  availability: RegistrationAvailability;
  auth: AuthCapabilities | null;
}

export async function loadInstanceAccessStatus(
  apiBaseUrl: string,
  loadStatus?: () => Promise<InstanceAccessStatus>,
): Promise<InstanceStatusResult> {
  try {
    const operation =
      loadStatus ??
      (() =>
        new InstanceApi(
          new Configuration({ basePath: apiBaseUrl }),
        ).instanceStatusApiV1InstanceStatusGet());
    const status = await operation();
    return {
      availability: classifyRegistrationAvailability(status),
      auth: status.auth ?? null,
    };
  } catch {
    return {
      availability: 'unreachable',
      auth: null,
    };
  }
}

export async function loadRegistrationAvailability(
  apiBaseUrl: string,
  loadStatus?: () => Promise<InstanceAccessStatus>,
): Promise<RegistrationAvailability> {
  return (await loadInstanceAccessStatus(apiBaseUrl, loadStatus)).availability;
}
