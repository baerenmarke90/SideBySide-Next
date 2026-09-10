import { describe, expect, it } from 'vitest';
import type { ActivityItem } from '../api/generated/models/ActivityItem';
import type { DashboardItem } from '../api/generated/models/DashboardItem';
import {
  MONTHLY_STRIP_MAX_ITEMS,
  selectLivingModule,
  selectMonthlyStrip,
} from './todayComposition';

const PARTNER_ID = 'partner-1';
const VIEWER_ID = 'viewer-1';

function item(overrides: Partial<DashboardItem> & Pick<DashboardItem, 'id'>) {
  return {
    type: 'MEMORY',
    titleOrText: 'Ein Moment',
    occurredOn: null,
    scheduledAt: null,
    createdAt: null,
    previewAttachmentId: null,
    ...overrides,
  } as DashboardItem;
}

function comment(overrides: Partial<ActivityItem> = {}) {
  return {
    id: 'a1',
    kind: 'COMMENT_CREATED',
    actorId: PARTNER_ID,
    targetType: 'MEMORY',
    targetId: 'm1',
    createdAt: new Date('2026-09-09T10:00:00Z'),
    ...overrides,
  } as ActivityItem;
}

describe('selectLivingModule', () => {
  const wish = item({ id: 'w1', type: 'WISH' });
  const plan = item({ id: 'p1', type: 'PLAN' });
  const milestone = item({ id: 'ms1', type: 'MILESTONE' });
  const retrospective = item({ id: 'r1' });

  it('returns exactly one module, never a stack, when several candidates qualify', () => {
    const result = selectLivingModule({
      partnerId: PARTNER_ID,
      activityItems: [comment()],
      retrospective,
      recentShared: [wish, plan, milestone],
    });

    expect(result).toEqual({
      kind: 'partner_signal',
      activityItem: comment(),
    });
  });

  it('prefers the partner signal, then the retrospective, then wish, plan, milestone', () => {
    const chain = [
      {
        input: {
          activityItems: [comment()],
          retrospective,
          recentShared: [wish],
        },
        expected: 'partner_signal',
      },
      {
        input: { activityItems: [], retrospective, recentShared: [wish] },
        expected: 'retrospective',
      },
      {
        input: {
          activityItems: [],
          retrospective: null,
          recentShared: [milestone, plan, wish],
        },
        expected: 'wish',
      },
      {
        input: {
          activityItems: [],
          retrospective: null,
          recentShared: [milestone, plan],
        },
        expected: 'plan',
      },
      {
        input: {
          activityItems: [],
          retrospective: null,
          recentShared: [milestone],
        },
        expected: 'milestone',
      },
    ];

    for (const step of chain) {
      expect(
        selectLivingModule({ partnerId: PARTNER_ID, ...step.input })?.kind,
      ).toBe(step.expected);
    }
  });

  it('is deterministic: the same input always yields the same module', () => {
    const input = {
      partnerId: PARTNER_ID,
      activityItems: [],
      retrospective: null,
      recentShared: [milestone, plan, wish],
    };
    const first = selectLivingModule(input);
    for (let i = 0; i < 5; i += 1) {
      expect(selectLivingModule(input)).toEqual(first);
    }
  });

  it('returns null when nothing qualifies, so the section is omitted', () => {
    expect(
      selectLivingModule({
        partnerId: PARTNER_ID,
        activityItems: [],
        retrospective: null,
        recentShared: [item({ id: 'hm1', type: 'HEART_MOMENT' })],
      }),
    ).toBeNull();
  });

  it('never repeats an item the page already features above it', () => {
    expect(
      selectLivingModule({
        partnerId: PARTNER_ID,
        activityItems: [],
        retrospective,
        recentShared: [wish],
        excludeItemIds: [retrospective.id],
      })?.kind,
    ).toBe('wish');
  });

  it('does not treat the viewer’s own comment as a partner signal', () => {
    expect(
      selectLivingModule({
        partnerId: PARTNER_ID,
        activityItems: [comment({ actorId: VIEWER_ID })],
        retrospective: null,
        recentShared: [],
      }),
    ).toBeNull();
  });

  it('does not treat an unattributed comment as a partner signal', () => {
    expect(
      selectLivingModule({
        partnerId: PARTNER_ID,
        activityItems: [comment({ actorId: null })],
        retrospective: null,
        recentShared: [],
      }),
    ).toBeNull();
  });

  it('does not surface a partner signal when the space has no partner', () => {
    expect(
      selectLivingModule({
        partnerId: null,
        activityItems: [comment()],
        retrospective: null,
        recentShared: [],
      }),
    ).toBeNull();
  });

  it('ignores non-comment partner activity', () => {
    expect(
      selectLivingModule({
        partnerId: PARTNER_ID,
        activityItems: [comment({ kind: 'MEMORY_CREATED' })],
        retrospective: null,
        recentShared: [],
      }),
    ).toBeNull();
  });
});

describe('selectMonthlyStrip', () => {
  const now = new Date('2026-09-10T12:00:00Z');
  const thisMonth = (day: number) => new Date(2026, 8, day, 12, 0, 0);

  const photo = (id: string, day: number) =>
    item({
      id,
      type: 'MEMORY',
      previewAttachmentId: `att-${id}`,
      occurredOn: thisMonth(day),
    });

  it('shows at most three photos', () => {
    const result = selectMonthlyStrip({
      recentShared: [1, 2, 3, 4, 5].map((n) => photo(`m${n}`, n)),
      now,
    });
    expect(result).toHaveLength(MONTHLY_STRIP_MAX_ITEMS);
    expect(result.map((i) => i.id)).toEqual(['m1', 'm2', 'm3']);
  });

  it('composes one and two photos rather than padding to three', () => {
    expect(
      selectMonthlyStrip({ recentShared: [photo('m1', 1)], now }),
    ).toHaveLength(1);
    expect(
      selectMonthlyStrip({
        recentShared: [photo('m1', 1), photo('m2', 2)],
        now,
      }),
    ).toHaveLength(2);
  });

  it('is empty when the month has no shared photo, so the section is omitted', () => {
    expect(selectMonthlyStrip({ recentShared: [], now })).toEqual([]);
  });

  it('excludes entries from other months so the heading stays true', () => {
    const lastMonth = item({
      id: 'old',
      type: 'MEMORY',
      previewAttachmentId: 'att-old',
      occurredOn: new Date(2026, 7, 20, 12, 0, 0),
    });
    const lastYear = item({
      id: 'ancient',
      type: 'MEMORY',
      previewAttachmentId: 'att-ancient',
      occurredOn: new Date(2025, 8, 20, 12, 0, 0),
    });

    expect(
      selectMonthlyStrip({
        recentShared: [lastMonth, lastYear, photo('m1', 3)],
        now,
      }).map((i) => i.id),
    ).toEqual(['m1']);
  });

  it('shows only real photos, never a placeholder for a text-only entry', () => {
    const noPhoto = item({
      id: 'm-nophoto',
      type: 'MEMORY',
      occurredOn: thisMonth(4),
    });
    const notAMemory = item({
      id: 'hm1',
      type: 'HEART_MOMENT',
      previewAttachmentId: 'att-hm1',
      occurredOn: thisMonth(5),
    });

    expect(
      selectMonthlyStrip({
        recentShared: [noPhoto, notAMemory, photo('m1', 6)],
        now,
      }).map((i) => i.id),
    ).toEqual(['m1']);
  });

  it('falls back to the creation date when a memory has no happened-on date', () => {
    const created = item({
      id: 'm-created',
      type: 'MEMORY',
      previewAttachmentId: 'att-created',
      createdAt: thisMonth(7),
    });
    expect(
      selectMonthlyStrip({ recentShared: [created], now }).map((i) => i.id),
    ).toEqual(['m-created']);
  });

  it('never repeats the photo already shown large as Euer Moment', () => {
    const featured = photo('m1', 2);
    expect(
      selectMonthlyStrip({
        recentShared: [featured, photo('m2', 3)],
        now,
        excludeItemIds: [featured.id],
      }).map((i) => i.id),
    ).toEqual(['m2']);
  });
});
