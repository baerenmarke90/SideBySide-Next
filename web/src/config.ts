export interface ReferenceConfig {
  apiBaseUrl: string;
  spaceId: string | null;
}

function normalizeBaseUrl(value: string | undefined): string {
  if (!value) return '';
  return value.replace(/\/+$/, '');
}

export const referenceConfig: ReferenceConfig = {
  apiBaseUrl: normalizeBaseUrl(import.meta.env.VITE_SBS_API_BASE_URL),
  spaceId: import.meta.env.VITE_SBS_SPACE_ID?.trim() || null,
};
