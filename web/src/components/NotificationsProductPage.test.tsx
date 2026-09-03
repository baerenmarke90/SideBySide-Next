import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import type { NotificationsApi } from '../api/generated/apis/NotificationsApi';
import type { M4ProductApis } from '../client/m4Product';
import { NotificationsProductPage } from './M4ProductPages';

const SPACE_ID = 'space-1';

function renderNotificationsPage(
  items: unknown[],
  unreadCount = 1,
  currentAccountId = 'user-self',
): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(['m5-s5', 'notifications', SPACE_ID], {
    pages: [
      {
        items,
        nextCursor: null,
      },
    ],
    pageParams: [null],
  });
  queryClient.setQueryData(['m5-s5', 'notification-unread-count', SPACE_ID], {
    unreadCount,
  });

  return renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <NotificationsProductPage
          apis={{ notifications: {} as NotificationsApi } as M4ProductApis}
          spaceId={SPACE_ID}
          currentAccountId={currentAccountId}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Notifications Product Experience', () => {
  it('renders interactive notification card for comment with target, chevron, and no separate open button', () => {
    const html = renderNotificationsPage([
      {
        id: 'notif-1',
        sourceEventId: 'evt-1',
        kind: 'COMMENT_CREATED',
        actorId: 'user-partner',
        actor: {
          id: 'user-partner',
          displayName: 'Alex',
          profileAttachmentId: null,
        },
        targetType: 'PLAN',
        targetId: 'plan-123',
        target: {
          targetType: 'PLAN',
          targetId: 'plan-123',
          title: 'Konzert im Herbst',
        },
        createdAt: new Date('2026-09-03T18:03:00Z'),
        readAt: null,
      },
    ]);

    expect(html).toContain('Alex');
    expect(html).toContain('Konzert im Herbst');
    expect(html).toContain('href="/plan/plans/plan-123"');
    expect(html).toContain('activity-card-chevron');
    expect(html).not.toContain('button-link secondary-link');
    expect(html).not.toContain('>Öffnen<');
  });

  it('renders warm thinking-of-you notification as static card without chevron or fake link', () => {
    const html = renderNotificationsPage([
      {
        id: 'notif-2',
        sourceEventId: 'evt-2',
        kind: 'THINKING_OF_YOU',
        actorId: 'user-partner',
        actor: {
          id: 'user-partner',
          displayName: 'Alex',
          profileAttachmentId: null,
        },
        targetType: null,
        targetId: null,
        target: null,
        createdAt: new Date('2026-09-03T19:00:00Z'),
        readAt: null,
      },
    ]);

    expect(html).toContain('Alex');
    expect(html).toContain('denkt an dich.');
    expect(html).not.toContain('activity-card-chevron');
    expect(html).not.toContain('<a class="m4-notification-link"');
    expect(html).toContain('m4-mark-read-btn');
  });

  it('renders reminder due notification with target and link', () => {
    const html = renderNotificationsPage([
      {
        id: 'notif-3',
        sourceEventId: 'evt-3',
        kind: 'REMINDER_DUE',
        actorId: null,
        actor: null,
        targetType: 'PLAN',
        targetId: 'plan-456',
        target: {
          targetType: 'PLAN',
          targetId: 'plan-456',
          title: 'Zahnarzttermin',
        },
        createdAt: new Date('2026-09-03T08:00:00Z'),
        readAt: new Date('2026-09-03T08:05:00Z'),
      },
    ]);

    expect(html).toContain('Zahnarzttermin');
    expect(html).toContain('href="/plan/plans/plan-456"');
  });
});
