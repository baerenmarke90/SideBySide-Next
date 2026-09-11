import type { TFunction } from 'i18next';
import type { PlanDetail } from '../api/generated/models/PlanDetail';
import type { WishDetail } from '../api/generated/models/WishDetail';
import { formatCompactWeekdayDate } from './formatRecency';

/**
 * Shared Planen product-reference (#859) status/date pill presentation for
 * both the overview cards and the Plan detail hierarchy, so the two surfaces
 * never drift apart on what a given lifecycle state is called.
 */
export function wishPillTone(status: WishDetail['status']): string {
  if (status === 'COMPLETED') return 'completed';
  if (status === 'PLANNED') return 'scheduled';
  return 'open';
}

export function planPillTone(
  plan: Pick<PlanDetail, 'status' | 'plannedStart'>,
): string {
  if (plan.status === 'IDEA') return 'idea';
  if (plan.status === 'PLANNED')
    return plan.plannedStart ? 'scheduled' : 'idea';
  return 'completed';
}

/** Bare status word, e.g. for the Plan detail page's separate status pill. */
export function planStatusWord(
  t: TFunction,
  plan: Pick<PlanDetail, 'status'>,
): string {
  if (plan.status === 'IDEA') return t('m5s3.plan.status.IDEA');
  if (plan.status === 'PLANNED') return t('m5s3.plan.statusPillPlanned');
  return t(`m5s3.plan.status.${plan.status}`);
}

/**
 * Combined "{{status}} → {{date}}" pill label for the Planen overview list,
 * where a scheduled Plan gets a single compact pill (see planStatusWord for
 * the Plan detail page's separate status pill).
 */
export function planPillLabel(
  t: TFunction,
  plan: Pick<PlanDetail, 'status' | 'plannedStart'>,
): string {
  const statusWord = planStatusWord(t, plan);
  if (plan.status === 'PLANNED' && plan.plannedStart) {
    return t('m5s3.overview.scheduledMeta', {
      status: statusWord,
      date: formatCompactWeekdayDate(plan.plannedStart),
    });
  }
  return statusWord;
}
