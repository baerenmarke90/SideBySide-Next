import { useEffect } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';
import { applyRouteEntryHandoff } from '../client/routeEntryHandoff';

/**
 * Mounted once by `AppShell`. Applies the shared destination handoff (see
 * `routeEntryHandoff.ts`) on every route change, so every Quick Create
 * target - and any other in-app navigation - lands on a visible, correctly
 * positioned composition without a per-destination scroll hack.
 *
 * POP navigation (browser Back/Forward, and the initial load) is left
 * alone when there is no hash to honor, so native scroll restoration for
 * Back/Forward is not overridden.
 */
export function RouteEntryHandoff(): null {
  const location = useLocation();
  const navigationType = useNavigationType();

  useEffect(() => {
    if (navigationType === 'POP' && !location.hash) return;
    applyRouteEntryHandoff(location.hash);
    // `location` (not just `.hash`) is the dependency: a pathname-only
    // change between two hash-less routes must still re-run the handoff.
  }, [location, navigationType]);

  return null;
}
