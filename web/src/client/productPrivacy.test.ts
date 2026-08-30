import { ContentVisibility } from '../api/generated/models/ContentVisibility';
import { commentsVisibleForParent } from './productPrivacy';

describe('product privacy presentation', () => {
  it('never exposes comment queries for owner-only HeartMoments', () => {
    expect(
      commentsVisibleForParent('HEART_MOMENT', ContentVisibility.PRIVATE),
    ).toBe(false);
    expect(
      commentsVisibleForParent('HEART_MOMENT', ContentVisibility.SHARED),
    ).toBe(true);
  });

  it('keeps shared Memory and Milestone comments available', () => {
    expect(commentsVisibleForParent('MEMORY')).toBe(true);
    expect(commentsVisibleForParent('MILESTONE')).toBe(true);
  });
});
