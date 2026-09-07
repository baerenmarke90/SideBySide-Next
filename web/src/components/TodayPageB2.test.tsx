import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import type { M4ProductApis } from '../client/m4Product';
import { TodayPage } from './TodayPage';

type NodeFs = {
  readFileSync(path: URL, encoding: 'utf8'): string;
};

type NodeProcess = {
  getBuiltinModule(name: 'fs'): NodeFs;
};

function renderToday(
  dashboardData: unknown,
  loadMemoryImage?: (memoryId: string, attachmentId: string) => Promise<string>,
): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], dashboardData);

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TodayPage
          apis={{} as M4ProductApis}
          spaceId="space-1"
          loadMemoryImage={loadMemoryImage}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function readB2Css(): string {
  const processRef = (
    globalThis as typeof globalThis & { process?: NodeProcess }
  ).process;
  if (!processRef)
    throw new Error('Node process API is unavailable in the test run.');
  return processRef
    .getBuiltinModule('fs')
    .readFileSync(new URL('./TodayPageB2.css', import.meta.url), 'utf8');
}

describe('Direction B2 /today composition', () => {
  it('keeps couple presence as the first anchor in a sparse new Space', () => {
    const html = renderToday({
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: null,
      upcoming: [],
      recentShared: [],
      retrospective: null,
    });

    expect(html).toContain('couple-presence-card');
    expect(html).toContain('new-space-experience');
    expect(html.indexOf('couple-presence-card')).toBeLessThan(
      html.indexOf('new-space-experience'),
    );
  });

  it('promotes a genuine recent Memory preview when no retrospective exists', () => {
    const html = renderToday(
      {
        space: {
          id: 'space-1',
          partner: { id: 'partner-1', displayName: 'Marie' },
        },
        relationshipDuration: { daysTogether: 420 },
        upcoming: [],
        recentShared: [
          {
            id: 'memory-photo',
            type: 'MEMORY',
            titleOrText: 'Evening by the lake',
            occurredOn: new Date('2026-09-01T18:00:00Z'),
            previewAttachmentId: 'attachment-1',
          },
          {
            id: 'heart-text',
            type: 'HEART_MOMENT',
            titleOrText: 'Small note',
            occurredOn: new Date('2026-08-31T08:00:00Z'),
          },
        ],
        retrospective: null,
      },
      () => Promise.resolve('blob:http://localhost/memory-photo'),
    );

    expect(html).toContain('today-section-keepsake-recent');
    expect(html).toContain('today-card-keepsake');
    expect(html).toContain('Evening by the lake');
    expect(html).toContain('Small note');
    expect(html.match(/Evening by the lake/g)).toHaveLength(1);
  });

  it('uses semantic tokens and explicitly supports reduced motion', () => {
    const css = readB2Css();

    expect(css).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(css).toContain('@media (prefers-reduced-motion: reduce)');
    expect(css).toContain('var(--font-display)');
    expect(css).toContain('var(--font-ui)');
  });
});
