import { identityBuildVariable } from './identityEnvironment';

export interface ReferenceClientConfig {
  apiBaseUrl: string;
}

export function loadReferenceClientConfig(): ReferenceClientConfig {
  const apiBaseUrl = (
    identityBuildVariable('API_BASE_URL') || window.location.origin
  ).replace(/\/+$/, '');
  return { apiBaseUrl };
}
