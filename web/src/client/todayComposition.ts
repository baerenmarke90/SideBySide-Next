/*
 * Today ("Wir") composition contracts.
 *
 * `docs/PARTNER-APP-EXPERIENCE-STANDARD.md` section 3 requires Today to be a
 * curated orchestration surface rather than a widget dashboard: deterministic
 * product rules, no black-box relevance ranking, and modules that disappear
 * when they have nothing to say.
 *
 * The two selections below are the parts of that orchestration that carry real
 * product rules, so they live here as pure functions the component only
 * renders. Everything they consume is already-authorized, Space-scoped server
 * data from the Dashboard and Activity projections; nothing is derived from a
 * client-side heuristic, a random rotation, or a per-viewer stored state.
 */
import type { ActivityItem } from '../api/generated/models/ActivityItem';
import type { DashboardItem } from '../api/generated/models/DashboardItem';

/** How many photos the monthly strip shows at most. */
export const MONTHLY_STRIP_MAX_ITEMS = 3;

/**
 * The kinds of module the single `Gerade bei euch` slot can hold, in the
 * order they take precedence.
 */
export type LivingModuleKind =
  | 'partner_signal'
  | 'retrospective'
  | 'wish'
  | 'plan'
  | 'milestone';

export type LivingModule =
  | { kind: 'partner_signal'; activityItem: ActivityItem }
  | {
      kind: 'retrospective' | 'wish' | 'plan' | 'milestone';
      item: DashboardItem;
    };

/**
 * Pick the one contextual relationship module for `Gerade bei euch`.
 *
 * Exactly one module is shown, never a stack. The chain is ordered by how
 * *current* and how *mutual* each candidate is:
 *
 * 1. a genuine partner interaction (the partner commented on shared content) —
 *    the only candidate that represents the partner acting today;
 * 2. the server-curated retrospective (`Weißt du noch?`) — date-specific, so it
 *    is only ever offered on the day it actually applies;
 * 3. a shared wish, then a shared plan, then a shared milestone — stable shared
 *    content that keeps the slot meaningful on a quiet day.
 *
 * `excludeItemIds` keeps the slot from repeating something the page already
 * shows prominently above it (the `Euer Moment` photo in particular).
 *
 * Returns `null` when nothing qualifies; the section is then omitted entirely
 * rather than rendered as an empty placeholder.
 */
export function selectLivingModule({
  partnerId,
  activityItems,
  retrospective,
  recentShared,
  excludeItemIds,
}: {
  partnerId: string | null | undefined;
  activityItems: readonly ActivityItem[] | undefined;
  retrospective: DashboardItem | null | undefined;
  recentShared: readonly DashboardItem[];
  excludeItemIds?: readonly string[];
}): LivingModule | null {
  const excluded = new Set(excludeItemIds ?? []);

  // Only a genuine partner comment counts. An item the viewer wrote, or one
  // with no attributable actor, is not a signal *from* the partner.
  const partnerSignal =
    partnerId != null
      ? activityItems?.find(
          (item) =>
            item.kind === 'COMMENT_CREATED' &&
            item.actorId != null &&
            item.actorId === partnerId,
        )
      : undefined;
  if (partnerSignal) {
    return { kind: 'partner_signal', activityItem: partnerSignal };
  }

  if (retrospective && !excluded.has(retrospective.id)) {
    return { kind: 'retrospective', item: retrospective };
  }

  const firstOfType = (type: DashboardItem['type']) =>
    recentShared.find((item) => item.type === type && !excluded.has(item.id));

  const wish = firstOfType('WISH');
  if (wish) return { kind: 'wish', item: wish };

  const plan = firstOfType('PLAN');
  if (plan) return { kind: 'plan', item: plan };

  const milestone = firstOfType('MILESTONE');
  if (milestone) return { kind: 'milestone', item: milestone };

  return null;
}

function itemMoment(item: DashboardItem): Date | null {
  return item.occurredOn ?? item.createdAt ?? null;
}

/**
 * Pick up to {@link MONTHLY_STRIP_MAX_ITEMS} real shared photos from the
 * current calendar month for `Diesen Monat`.
 *
 * Only Memories carry a preview attachment in the Dashboard projection, so the
 * strip is by construction made of genuine shared photos — never a generated
 * placeholder, never a decorative stock tile.
 *
 * The strip deliberately makes no claim about *how many* shared moments the
 * month contains. `DashboardView.recentShared` is capped server-side for
 * presentation, so any total counted from it would silently understate a busy
 * month. Showing life truthfully beats showing a number that can be wrong.
 */
export function selectMonthlyStrip({
  recentShared,
  now,
  excludeItemIds,
}: {
  recentShared: readonly DashboardItem[];
  now: Date;
  excludeItemIds?: readonly string[];
}): DashboardItem[] {
  const excluded = new Set(excludeItemIds ?? []);
  const year = now.getFullYear();
  const month = now.getMonth();

  return recentShared
    .filter((item) => {
      if (item.type !== 'MEMORY') return false;
      if (!item.previewAttachmentId) return false;
      if (excluded.has(item.id)) return false;
      const moment = itemMoment(item);
      if (!moment) return false;
      return moment.getFullYear() === year && moment.getMonth() === month;
    })
    .slice(0, MONTHLY_STRIP_MAX_ITEMS);
}
