const DEMO_MODE_SESSION_KEY = 'sbs-demo-mode';

/**
 * Reuses the Web demo-environment marker established by the entry surface.
 *
 * The backend remains authoritative for destructive-action rejection. This
 * helper only keeps client presentation consistent with the configured Demo
 * deployment and the existing demo-entry session marker.
 */
export function isDemoModeConfigured(): boolean {
  if (typeof window === 'undefined') return false;
  if (import.meta.env.VITE_SBS_DEMO_MODE === 'true') return true;
  if (new URLSearchParams(window.location.search).get('demo') === 'true') {
    window.sessionStorage?.setItem(DEMO_MODE_SESSION_KEY, 'true');
    return true;
  }
  return window.sessionStorage?.getItem(DEMO_MODE_SESSION_KEY) === 'true';
}
