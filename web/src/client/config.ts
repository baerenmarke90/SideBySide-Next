export interface ReferenceClientConfig {
  apiBaseUrl: string;
  spaceId: string;
}

export function loadReferenceClientConfig(): ReferenceClientConfig {
  const apiBaseUrl = (
    import.meta.env.VITE_SBS_API_BASE_URL || window.location.origin
  ).replace(/\/+$/, '');
  const spaceId = (import.meta.env.VITE_SBS_SPACE_ID || '').trim();
  return { apiBaseUrl, spaceId };
}
