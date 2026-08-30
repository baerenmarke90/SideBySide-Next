export interface ReferenceClientConfig {
  apiBaseUrl: string;
}

export function loadReferenceClientConfig(): ReferenceClientConfig {
  const apiBaseUrl = (
    import.meta.env.VITE_SBS_API_BASE_URL || window.location.origin
  ).replace(/\/+$/, '');
  return { apiBaseUrl };
}
