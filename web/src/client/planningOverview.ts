import type { PlanDetail } from '../api/generated/models/PlanDetail';
import {
  PlanStatus,
  type PlanStatus as PlanStatusValue,
} from '../api/generated/models/PlanStatus';
import type { SharedPlanningApis } from './sharedPlanning';

const OVERVIEW_PAGE_SIZE = 50;

async function loadPlansForStatus(
  apis: Pick<SharedPlanningApis, 'plans'>,
  spaceId: string,
  status: PlanStatusValue,
): Promise<PlanDetail[]> {
  const items: PlanDetail[] = [];
  let cursor: string | null | undefined = null;
  const seenCursors = new Set<string>();

  do {
    const page = await apis.plans.listPlans({
      spaceId,
      cursor,
      limit: OVERVIEW_PAGE_SIZE,
      status,
    });
    items.push(...page.items);
    cursor = page.nextCursor;
    if (cursor) {
      if (seenCursors.has(cursor)) {
        throw new Error('Plan pagination returned a repeated cursor.');
      }
      seenCursors.add(cursor);
    }
  } while (cursor);

  return items;
}

/**
 * Loads the two Plan lifecycle states that belong on the planning overview.
 * Completed Plans keep their existing detail/history semantics and are not
 * fetched into the Planen overview.
 */
export async function loadPlanningOverviewPlans(
  apis: Pick<SharedPlanningApis, 'plans'>,
  spaceId: string,
): Promise<PlanDetail[]> {
  const [planned, ideas] = await Promise.all([
    loadPlansForStatus(apis, spaceId, PlanStatus.PLANNED),
    loadPlansForStatus(apis, spaceId, PlanStatus.IDEA),
  ]);
  return [...planned, ...ideas];
}

/**
 * Mirrors the Dashboard Plan predicate and ordering used by /today:
 * PLANNED + plannedStart >= current instant, ordered by plannedStart then id.
 * Keep this aligned with backend dashboard.service._upcoming.
 */
export function selectUpcomingPlans(
  plans: readonly PlanDetail[],
  now: Date = new Date(),
): PlanDetail[] {
  const nowMs = now.getTime();

  return plans
    .filter(
      (plan) =>
        plan.status === PlanStatus.PLANNED &&
        plan.plannedStart !== null &&
        plan.plannedStart.getTime() >= nowMs,
    )
    .sort((left, right) => {
      const leftStart =
        left.plannedStart?.getTime() ?? Number.POSITIVE_INFINITY;
      const rightStart =
        right.plannedStart?.getTime() ?? Number.POSITIVE_INFINITY;
      if (leftStart !== rightStart) return leftStart - rightStart;
      if (left.id < right.id) return -1;
      if (left.id > right.id) return 1;
      return 0;
    });
}
