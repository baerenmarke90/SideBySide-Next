import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import type { M4ProductApis } from '../client/m4Product';
import { DurationDisplayMode } from '../api/generated/models/DurationDisplayMode';
import { i18n } from '../i18n';
import m5s5 from '../i18n/locales/m5s5';
import { formatRelationshipDuration, TodayPage } from './TodayPage';


function renderTodayPage(dashboardData: unknown): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], dashboardData);

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TodayPage apis={{} as M4ProductApis} spaceId="space-1" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('TodayPage', () => {
  it('renders couple presence hero, days together, thinking-of-you button, and cards', () => {
    const html = renderTodayPage({
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: { daysTogether: 420 },
      upcoming: [
        {
          id: 'plan-1',
          type: 'PLAN',
          titleOrText: 'Weekend trip to Paris',
          scheduledAt: new Date('2026-09-15T10:00:00Z'),
        },
      ],
      recentShared: [
        {
          id: 'mem-1',
          type: 'MEMORY',
          titleOrText: 'Park Picnic',
          occurredOn: new Date('2026-09-01T14:00:00Z'),
        },
      ],
      retrospective: {
        id: 'heart-1',
        type: 'HEART_MOMENT',
        titleOrText: 'Morning Smile',
        createdAt: new Date('2025-09-03T08:00:00Z'),
      },
    });

    expect(html).toContain('Marie');
    expect(html).toContain('420');
    expect(html).toContain('today-hero-action');
    expect(html).toContain('Weekend trip to Paris');
    expect(html).toContain('Park Picnic');
    expect(html).toContain('Morning Smile');
    expect(html).toContain('today-card-badges');
  });

  it('renders welcoming new-space experience when there are no items yet', () => {
    const html = renderTodayPage({
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: null,
      upcoming: [],
      recentShared: [],
      retrospective: null,
    });

    expect(html).toContain('new-space-experience');
    expect(html).toContain('new-space-mark');
    expect(html).toContain('Marie');
    expect(html).toContain('href="/story/memories/new"');
  });

  it('renders image-first card when previewAttachmentId is present and typography-first card when absent', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: { id: 'space-1', partner: { id: 'p-1', displayName: 'Sam' } },
      relationshipDuration: null,
      upcoming: [
        {
          id: 'plan-primary',
          type: 'PLAN',
          titleOrText: 'Primary Plan',
          scheduledAt: new Date('2026-09-02T10:00:00Z'),
        },
        {
          id: 'mem-photo',
          type: 'MEMORY',
          titleOrText: 'Photo Memory',
          occurredOn: new Date('2026-09-01T12:00:00Z'),
          previewAttachmentId: 'att-123',
        },
        {
          id: 'mem-text',
          type: 'MEMORY',
          titleOrText: 'Text Memory',
          occurredOn: new Date('2026-08-30T12:00:00Z'),
        },
      ],
      recentShared: [],
      retrospective: null,
    });


    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage
            apis={{} as M4ProductApis}
            spaceId="space-1"
            loadMemoryImage={() =>
              Promise.resolve('blob:http://localhost/mock')
            }
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('today-card-has-media');
    expect(html).toContain('today-card-typography-first');
    expect(html).toContain('Photo Memory');
    expect(html).toContain('Text Memory');
  });

  it('renders compact recent activity cards and secondary all-activity action', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: { id: 'space-1', partner: { id: 'p-1', displayName: 'Sam' } },
      relationshipDuration: null,
      upcoming: [],
      recentShared: [
        {
          id: 'item-1',
          type: 'CHAPTER',
          titleOrText: 'Summer Chapter',
          occurredOn: new Date('2026-09-04T10:00:00Z'),
        },
        {
          id: 'item-2',
          type: 'COLLECTION',
          titleOrText: 'Rainy Day Movies',
          createdAt: new Date('2026-09-03T10:00:00Z'),
        },
        {
          id: 'item-3',
          type: 'HEART_MOMENT',
          titleOrText: 'Love Note',
          occurredOn: new Date('2026-09-01T10:00:00Z'),
        },
        {
          id: 'item-4',
          type: 'MILESTONE',
          titleOrText: 'First Shared Home',
          occurredOn: new Date('2026-08-01T10:00:00Z'),
        },
        {
          id: 'item-5',
          type: 'MEMORY',
          titleOrText: 'Should be sliced out',
          occurredOn: new Date('2026-07-01T10:00:00Z'),
        },
      ],
      retrospective: null,
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage apis={{} as M4ProductApis} spaceId="space-1" />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // Renders section with distinct kicker and heading (no duplicate wording)
    expect(html).toContain(m5s5.dashboard.recentKicker);
    expect(html).toContain(m5s5.dashboard.recentTitle);
    expect(html).toContain(m5s5.dashboard.recentSubline);

    // Renders compact items
    expect(html).toContain('recent-shared-card');
    expect(html).toContain('Summer Chapter');
    expect(html).toContain(m5s5.kind.CHAPTER);
    expect(html).toContain('Rainy Day Movies');
    expect(html).toContain(m5s5.kind.COLLECTION);

    // Slices to max 4 items
    expect(html).not.toContain('Should be sliced out');

    // Offers secondary action to full activity page
    expect(html).toContain('href="/today/activity"');
    expect(html).toContain(m5s5.dashboard.allActivityAction);
  });



  it('orchestrates primary contextual slot and relationship signal when partner activity exists', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: { daysTogether: 100 },
      upcoming: [
        {
          id: 'plan-1',
          type: 'PLAN',
          titleOrText: 'Candlelight Dinner',
          scheduledAt: new Date('2026-09-10T19:00:00Z'),
        },
      ],
      recentShared: [
        {
          id: 'mem-1',
          type: 'MEMORY',
          titleOrText: 'Lake Walk',
          occurredOn: new Date('2026-09-02T16:00:00Z'),
        },
      ],
      retrospective: null,
    });
    queryClient.setQueryData(['m4', 'activity', 'space-1'], {
      items: [
        {
          id: 'act-1',
          kind: 'COMMENT_CREATED',
          actorId: 'partner-1',
          targetId: 'mem-1',
          targetType: 'MEMORY',
          createdAt: new Date('2026-09-03T12:00:00Z'),
          occurredAt: new Date('2026-09-03T12:00:00Z'),
          sourceEventId: 'ev-1',
        },
      ],
      nextCursor: null,
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage
            apis={
              {
                activity: {
                  getActivity: () =>
                    Promise.resolve({ items: [], nextCursor: null }),
                },
              } as unknown as M4ProductApis
            }
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // Primary contextual card
    expect(html).toContain('today-context-area');
    expect(html).toContain('today-context-dual');
    expect(html).toContain('Candlelight Dinner');
    expect(html).toContain('today-context-kicker');

    // Relationship signal card
    expect(html).toContain('today-signal-card');
    expect(html).toContain('today-signal-kicker');
    expect(html).toContain('today-signal-message');
    expect(html).toContain('href="/story/memories/mem-1"');
    expect(html).toContain('today-signal-action');

    // Zero duplication: single upcoming item is NOT duplicated in a separate upcoming section
    expect(html).not.toContain('today-section-upcoming');
  });

  it('omits context area entirely when neither upcoming item nor relationship activity exists', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: { daysTogether: 50 },
      upcoming: [],
      recentShared: [
        {
          id: 'mem-1',
          type: 'MEMORY',
          titleOrText: 'Lake Walk',
          occurredOn: new Date('2026-09-02T16:00:00Z'),
        },
      ],
      retrospective: null,
    });
    queryClient.setQueryData(['m4', 'activity', 'space-1'], {
      items: [],
      nextCursor: null,
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage
            apis={
              {
                activity: {
                  getActivity: () =>
                    Promise.resolve({ items: [], nextCursor: null }),
                },
              } as unknown as M4ProductApis
            }
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // Context area is completely omitted
    expect(html).not.toContain('today-context-area');
    expect(html).not.toContain('today-signal-card');

    // Page flows directly into recent shared
    expect(html).toContain('today-section-recent');
    expect(html).toContain('Lake Walk');
  });

  it('renders single-column context area when only primary contextual item exists', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: { daysTogether: 50 },
      upcoming: [
        {
          id: 'plan-1',
          type: 'PLAN',
          titleOrText: 'Cooking Night',
          scheduledAt: new Date('2026-09-05T18:00:00Z'),
        },
      ],
      recentShared: [],
      retrospective: null,
    });
    queryClient.setQueryData(['m4', 'activity', 'space-1'], {
      items: [],
      nextCursor: null,
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage
            apis={
              {
                activity: {
                  getActivity: () =>
                    Promise.resolve({ items: [], nextCursor: null }),
                },
              } as unknown as M4ProductApis
            }
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('today-context-area');
    expect(html).toContain('today-context-single');
    expect(html).toContain('Cooking Night');
    expect(html).not.toContain('today-signal-card');
  });

  it('renders single-column context area when only relationship signal exists', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: { daysTogether: 50 },
      upcoming: [],
      recentShared: [],
      retrospective: null,
    });
    queryClient.setQueryData(['m4', 'activity', 'space-1'], {
      items: [
        {
          id: 'act-1',
          kind: 'COMMENT_CREATED',
          actorId: 'partner-1',
          targetId: 'mem-99',
          targetType: 'MEMORY',
          createdAt: new Date('2026-09-03T14:00:00Z'),
          occurredAt: new Date('2026-09-03T14:00:00Z'),
          sourceEventId: 'ev-99',
        },
      ],
      nextCursor: null,
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage
            apis={
              {
                activity: {
                  getActivity: () =>
                    Promise.resolve({ items: [], nextCursor: null }),
                },
              } as unknown as M4ProductApis
            }
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('today-context-area');
    expect(html).toContain('today-context-single');
    expect(html).toContain('today-signal-card');
    expect(html).toContain('href="/story/memories/mem-99"');
    expect(html).not.toContain('today-context-card');
  });

  it('renders secondary upcoming section when more than 1 upcoming item exists', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: { daysTogether: 50 },
      upcoming: [
        {
          id: 'plan-primary',
          type: 'PLAN',
          titleOrText: 'First Next Plan',
          scheduledAt: new Date('2026-09-05T18:00:00Z'),
        },
        {
          id: 'plan-secondary',
          type: 'PLAN',
          titleOrText: 'Second Future Plan',
          scheduledAt: new Date('2026-09-20T18:00:00Z'),
        },
      ],
      recentShared: [],
      retrospective: null,
    });
    queryClient.setQueryData(['m4', 'activity', 'space-1'], {
      items: [],
      nextCursor: null,
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage
            apis={
              {
                activity: {
                  getActivity: () =>
                    Promise.resolve({ items: [], nextCursor: null }),
                },
              } as unknown as M4ProductApis
            }
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // First plan is in primary context card
    expect(html).toContain('today-context-card');
    expect(html).toContain('First Next Plan');

    // Second plan is in secondary upcoming section
    expect(html).toContain('today-section-upcoming');
    expect(html).toContain('Second Future Plan');
  });

  it('does not render relationship signal when comment is from the user or another actor', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: { daysTogether: 50 },
      upcoming: [],
      recentShared: [
        {
          id: 'mem-1',
          type: 'MEMORY',
          titleOrText: 'Lake Walk',
          occurredOn: new Date('2026-09-02T16:00:00Z'),
        },
      ],
      retrospective: null,
    });
    queryClient.setQueryData(['m4', 'activity', 'space-1'], {
      items: [
        {
          id: 'act-own',
          kind: 'COMMENT_CREATED',
          actorId: 'user-self',
          targetId: 'mem-1',
          targetType: 'MEMORY',
          createdAt: new Date('2026-09-03T14:00:00Z'),
          occurredAt: new Date('2026-09-03T14:00:00Z'),
          sourceEventId: 'ev-own',
        },
      ],
      nextCursor: null,
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage
            apis={
              {
                activity: {
                  getActivity: () =>
                    Promise.resolve({ items: [], nextCursor: null }),
                },
              } as unknown as M4ProductApis
            }
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).not.toContain('today-signal-card');
  });

  it('does not render relationship signal when comment actorId is null', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: { daysTogether: 50 },
      upcoming: [],
      recentShared: [
        {
          id: 'mem-1',
          type: 'MEMORY',
          titleOrText: 'Lake Walk',
          occurredOn: new Date('2026-09-02T16:00:00Z'),
        },
      ],
      retrospective: null,
    });
    queryClient.setQueryData(['m4', 'activity', 'space-1'], {
      items: [
        {
          id: 'act-null',
          kind: 'COMMENT_CREATED',
          actorId: null,
          targetId: 'mem-1',
          targetType: 'MEMORY',
          createdAt: new Date('2026-09-03T14:00:00Z'),
          occurredAt: new Date('2026-09-03T14:00:00Z'),
          sourceEventId: 'ev-null',
        },
      ],
      nextCursor: null,
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage
            apis={
              {
                activity: {
                  getActivity: () =>
                    Promise.resolve({ items: [], nextCursor: null }),
                },
              } as unknown as M4ProductApis
            }
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).not.toContain('today-signal-card');
  });

  it('does not render relationship signal when space has no partner', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: {
        id: 'space-1',
        partner: null,
      },
      relationshipDuration: null,
      upcoming: [],
      recentShared: [
        {
          id: 'mem-1',
          type: 'MEMORY',
          titleOrText: 'Solo Memory',
          occurredOn: new Date('2026-09-02T16:00:00Z'),
        },
      ],
      retrospective: null,
    });
    queryClient.setQueryData(['m4', 'activity', 'space-1'], {
      items: [
        {
          id: 'act-1',
          kind: 'COMMENT_CREATED',
          actorId: 'partner-1',
          targetId: 'mem-1',
          targetType: 'MEMORY',
          createdAt: new Date('2026-09-03T14:00:00Z'),
          occurredAt: new Date('2026-09-03T14:00:00Z'),
          sourceEventId: 'ev-1',
        },
      ],
      nextCursor: null,
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage
            apis={
              {
                activity: {
                  getActivity: () =>
                    Promise.resolve({ items: [], nextCursor: null }),
                },
              } as unknown as M4ProductApis
            }
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).not.toContain('today-signal-card');
  });

  it('does not render relationship signal for non-comment activity', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: { daysTogether: 50 },
      upcoming: [],
      recentShared: [
        {
          id: 'mem-1',
          type: 'MEMORY',
          titleOrText: 'Lake Walk',
          occurredOn: new Date('2026-09-02T16:00:00Z'),
        },
      ],
      retrospective: null,
    });
    queryClient.setQueryData(['m4', 'activity', 'space-1'], {
      items: [
        {
          id: 'act-memory',
          kind: 'MEMORY_CREATED',
          actorId: 'partner-1',
          targetId: 'mem-1',
          targetType: 'MEMORY',
          createdAt: new Date('2026-09-03T14:00:00Z'),
          occurredAt: new Date('2026-09-03T14:00:00Z'),
          sourceEventId: 'ev-mem',
        },
      ],
      nextCursor: null,
    });

    const html = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TodayPage
            apis={
              {
                activity: {
                  getActivity: () =>
                    Promise.resolve({ items: [], nextCursor: null }),
                },
              } as unknown as M4ProductApis
            }
            spaceId="space-1"
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(html).not.toContain('today-signal-card');
  });

  it('renders neutral settings CTA when relationshipDuration is null without assuming missing start date', () => {
    const html = renderTodayPage({
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: null,
      upcoming: [
        {
          id: 'plan-1',
          type: 'PLAN',
          titleOrText: 'Picnic in the park',
          scheduledAt: new Date('2026-09-15T10:00:00Z'),
        },
      ],
      recentShared: [],
      retrospective: null,
    });

    expect(html).not.toContain('today-hero-settings-link');
    expect(html).not.toContain('today-hero-duration-link');
    expect(html).not.toContain('Beziehungseinstellungen öffnen');
    expect(html).not.toContain('Beziehungsstart festlegen');
  });

  it('links duration pill to relationship profile when relationshipDuration is present in DAYS mode', () => {
    const html = renderTodayPage({
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: {
        daysTogether: 100,
        displayMode: DurationDisplayMode.DAYS,
        startedOn: new Date('2026-01-01T00:00:00Z'),
      },
      upcoming: [
        {
          id: 'plan-1',
          type: 'PLAN',
          titleOrText: 'Picnic in the park',
          scheduledAt: new Date('2026-09-15T10:00:00Z'),
        },
      ],
      recentShared: [],
      retrospective: null,
    });

    expect(html).toContain('today-hero-duration-link');
    expect(html).toContain('100 Tage zusammen');
    expect(html).toContain('href="/more/profile#relationship-profile-title"');
    expect(html).not.toContain('today-hero-settings-link');
  });

  it('renders formatted duration in YEARS_MONTHS mode', () => {
    const html = renderTodayPage({
      space: {
        id: 'space-1',
        partner: { id: 'partner-1', displayName: 'Marie' },
      },
      relationshipDuration: {
        daysTogether: 1156,
        displayMode: DurationDisplayMode.YEARS_MONTHS,
        startedOn: new Date('2023-01-01T00:00:00Z'),
      },
      upcoming: [
        {
          id: 'plan-1',
          type: 'PLAN',
          titleOrText: 'Picnic in the park',
          scheduledAt: new Date('2026-09-15T10:00:00Z'),
        },
      ],
      recentShared: [],
      retrospective: null,
    });

    expect(html).toContain('today-hero-duration-link');
    expect(html).toContain('3 Jahre, 2 Monate zusammen');
    expect(html).not.toContain('today-hero-settings-link');
  });
});

describe('formatRelationshipDuration', () => {
  it('formats DAYS mode for singular and plural', () => {
    expect(
      formatRelationshipDuration(
        {
          daysTogether: 1,
          displayMode: DurationDisplayMode.DAYS,
          startedOn: new Date('2026-01-01T00:00:00Z'),
        },
        i18n.t,
      ),
    ).toBe('1 Tag zusammen');

    expect(
      formatRelationshipDuration(
        {
          daysTogether: 1178,
          displayMode: DurationDisplayMode.DAYS,
          startedOn: new Date('2023-01-01T00:00:00Z'),
        },
        i18n.t,
      ),
    ).toBe('1178 Tage zusammen');
  });

  it('formats YEARS_MONTHS mode with singular and plural units', () => {
    // Exactly 3 years, 2 months:
    // start 2023-01-01, + 1156 days -> 2026-03-02
    expect(
      formatRelationshipDuration(
        {
          daysTogether: 1156,
          displayMode: DurationDisplayMode.YEARS_MONTHS,
          startedOn: new Date('2023-01-01T00:00:00Z'),
        },
        i18n.t,
      ),
    ).toBe('3 Jahre, 2 Monate zusammen');

    // 1 year, 1 month:
    // start 2025-01-01, + 396 days -> 2026-02-01
    expect(
      formatRelationshipDuration(
        {
          daysTogether: 396,
          displayMode: DurationDisplayMode.YEARS_MONTHS,
          startedOn: new Date('2025-01-01T00:00:00Z'),
        },
        i18n.t,
      ),
    ).toBe('1 Jahr, 1 Monat zusammen');
  });

  it('formats YEARS_MONTHS mode when months == 0', () => {
    // Exactly 3 years, 0 months:
    // start 2023-01-01, + 1096 days -> 2026-01-01
    expect(
      formatRelationshipDuration(
        {
          daysTogether: 1096,
          displayMode: DurationDisplayMode.YEARS_MONTHS,
          startedOn: new Date('2023-01-01T00:00:00Z'),
        },
        i18n.t,
      ),
    ).toBe('3 Jahre zusammen');
  });

  it('formats YEARS_MONTHS mode when years == 0 and months > 0', () => {
    // 0 years, 2 months:
    // start 2026-01-01, + 62 days -> 2026-03-04
    expect(
      formatRelationshipDuration(
        {
          daysTogether: 62,
          displayMode: DurationDisplayMode.YEARS_MONTHS,
          startedOn: new Date('2026-01-01T00:00:00Z'),
        },
        i18n.t,
      ),
    ).toBe('2 Monate zusammen');

    // 0 years, 1 month:
    expect(
      formatRelationshipDuration(
        {
          daysTogether: 32,
          displayMode: DurationDisplayMode.YEARS_MONTHS,
          startedOn: new Date('2026-01-01T00:00:00Z'),
        },
        i18n.t,
      ),
    ).toBe('1 Monat zusammen');
  });

  it('falls back to days when years == 0 and months == 0', () => {
    expect(
      formatRelationshipDuration(
        {
          daysTogether: 15,
          displayMode: DurationDisplayMode.YEARS_MONTHS,
          startedOn: new Date('2026-01-01T00:00:00Z'),
        },
        i18n.t,
      ),
    ).toBe('15 Tage zusammen');
  });

  describe('issue #617: keep third-party dates out of primary context', () => {
    it('selects shared plan as primary context when upcoming contains couple plan', () => {
      const html = renderTodayPage({
        space: {
          id: 'space-1',
          partner: { id: 'partner-1', displayName: 'Sam' },
        },
        relationshipDuration: null,
        upcoming: [
          {
            id: 'plan-1',
            type: 'PLAN',
            titleOrText: 'Weekend by the lake',
            scheduledAt: new Date('2026-09-10T10:00:00Z'),
          },
        ],
        recentShared: [],
        retrospective: null,
      });

      expect(html).toContain('today-context-area');
      expect(html).toContain('Weekend by the lake');
      expect(html).not.toContain('today-section-upcoming');
    });

    it('omits primary context slot when upcoming is empty (no forced fallback for third-party dates)', () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      queryClient.setQueryData(['m5-s5', 'dashboard', 'space-1'], {
        space: {
          id: 'space-1',
          partner: { id: 'partner-1', displayName: 'Sam' },
        },
        relationshipDuration: { daysTogether: 100 },
        upcoming: [], // Filtered at projection boundary (#617)
        recentShared: [
          {
            id: 'mem-1',
            type: 'MEMORY',
            titleOrText: 'Konzertbesuch',
            occurredOn: new Date('2026-09-01T19:00:00Z'),
          },
        ],
        retrospective: null,
      });
      queryClient.setQueryData(['m4', 'activity', 'space-1'], {
        items: [],
        nextCursor: null,
      });

      const html = renderToStaticMarkup(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <TodayPage apis={{} as M4ProductApis} spaceId="space-1" />
          </MemoryRouter>
        </QueryClientProvider>,
      );

      // Context area must disappear cleanly; page flows directly into recent shared
      expect(html).not.toContain('today-context-area');
      expect(html).toContain('Konzertbesuch');
    });

    it('renders couple anniversary as eligible primary context', () => {
      const html = renderTodayPage({
        space: {
          id: 'space-1',
          partner: { id: 'partner-1', displayName: 'Sam' },
        },
        relationshipDuration: { daysTogether: 730 },
        upcoming: [
          {
            id: 'anniv-1',
            type: 'ANNIVERSARY',
            titleOrText: 'Jahrestag',
            occurredOn: new Date('2026-09-12T00:00:00Z'),
          },
        ],
        recentShared: [],
        retrospective: null,
      });

      expect(html).toContain('today-context-area');
      expect(html).toContain('today-context-card');
    });

    it('renders couple important date as eligible primary context', () => {
      const html = renderTodayPage({
        space: {
          id: 'space-1',
          partner: { id: 'partner-1', displayName: 'Sam' },
        },
        relationshipDuration: { daysTogether: 730 },
        upcoming: [
          {
            id: 'date-1',
            type: 'IMPORTANT_DATE',
            titleOrText: 'Zusammengezogen',
            occurredOn: new Date('2026-09-15T00:00:00Z'),
          },
        ],
        recentShared: [],
        retrospective: null,
      });

      expect(html).toContain('today-context-area');
      expect(html).toContain('Zusammengezogen');
    });
  });
});
