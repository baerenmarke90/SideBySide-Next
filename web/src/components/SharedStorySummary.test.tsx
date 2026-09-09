import { renderToStaticMarkup } from 'react-dom/server';
import m5s5 from '../i18n/locales/m5s5';
import {
  SharedStorySummary,
  sharedStorySummaryIsEligible,
} from './SharedStorySummary';

describe('SharedStorySummary', () => {
  it('uses the ratified sparse threshold', () => {
    expect(
      sharedStorySummaryIsEligible({
        memories: 4,
        heartMoments: 1,
        milestones: 0,
      }),
    ).toBe(true);
    expect(
      sharedStorySummaryIsEligible({
        memories: 3,
        heartMoments: 1,
        milestones: 0,
      }),
    ).toBe(false);
    expect(
      sharedStorySummaryIsEligible({
        memories: 20,
        heartMoments: 0,
        milestones: 0,
      }),
    ).toBe(false);
  });

  it('renders one editorial surface, omits zero metrics, and preserves metric order', () => {
    const html = renderToStaticMarkup(
      <SharedStorySummary
        summary={{ memories: 4, heartMoments: 1, milestones: 0 }}
      />,
    );

    expect(html).toContain(m5s5.dashboard.storySummaryTitle);
    expect(html).toContain(m5s5.dashboard.storySummaryMemories);
    expect(html).toContain(m5s5.dashboard.storySummaryHeartMoments);
    expect(html).not.toContain(m5s5.dashboard.storySummaryMilestones);
    expect(html.indexOf(m5s5.dashboard.storySummaryMemories)).toBeLessThan(
      html.indexOf(m5s5.dashboard.storySummaryHeartMoments),
    );
    expect(html).toContain('<dl');
    expect(html).not.toContain('button');
  });
});
