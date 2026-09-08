import type { PlanDetail } from '../api/generated/models/PlanDetail';
import { PlanStatus } from '../api/generated/models/PlanStatus';
import { selectIdeaPlans, selectUpcomingPlans } from './planningOverview';

const NOW = new Date('2026-09-08T12:00:00Z');

function plan(
  overrides: Pick<PlanDetail, 'id' | 'status'> & Partial<PlanDetail>,
): PlanDetail {
  const { id, status, ...rest } = overrides;
  const createdAt = rest.createdAt ?? new Date('2026-08-01T10:00:00Z');
  return {
    capabilities: { canComment: true, canDelete: true, canEdit: true },
    createdAt,
    createdBy: 'account-lea',
    creator: { id: 'account-lea', displayName: 'Lea' },
    description: null,
    experiencedOn: null,
    id,
    placeId: null,
    plannedEnd: null,
    plannedStart: null,
    sourceWishId: null,
    spaceId: 'space-lea-alex',
    status,
    title: id,
    updatedAt: createdAt,
    version: 1,
    ...rest,
  };
}

describe('planning overview selectors', () => {
  it('keeps only future PLANNED items in Dashboard order and leaves dateless ideas separate', () => {
    const convertedWishPlan = plan({
      id: 'plan-b',
      status: PlanStatus.PLANNED,
      plannedStart: new Date('2026-09-18T18:00:00Z'),
      sourceWishId: 'wish-autumn-hike',
      createdAt: new Date('2026-06-01T10:00:00Z'),
    });
    const plans = [
      plan({
        id: 'plan-later',
        status: PlanStatus.PLANNED,
        plannedStart: new Date('2026-09-25T09:00:00Z'),
        createdAt: new Date('2026-05-01T10:00:00Z'),
      }),
      convertedWishPlan,
      plan({
        id: 'plan-idea',
        status: PlanStatus.IDEA,
        plannedStart: null,
      }),
      plan({
        id: 'plan-completed',
        status: PlanStatus.COMPLETED,
        plannedStart: new Date('2026-09-30T09:00:00Z'),
        experiencedOn: new Date('2026-07-26T00:00:00Z'),
      }),
      plan({
        id: 'plan-a',
        status: PlanStatus.PLANNED,
        plannedStart: new Date('2026-09-18T18:00:00Z'),
        createdAt: new Date('2026-07-01T10:00:00Z'),
      }),
      plan({
        id: 'plan-past',
        status: PlanStatus.PLANNED,
        plannedStart: new Date('2026-09-01T09:00:00Z'),
      }),
    ];
    const inputOrder = plans.map((item) => item.id);

    expect(selectUpcomingPlans(plans, NOW).map((item) => item.id)).toEqual([
      'plan-a',
      'plan-b',
      'plan-later',
    ]);
    expect(selectIdeaPlans(plans).map((item) => item.id)).toEqual(['plan-idea']);
    expect(convertedWishPlan.sourceWishId).toBe('wish-autumn-hike');
    expect(plans.map((item) => item.id)).toEqual(inputOrder);
  });
});
