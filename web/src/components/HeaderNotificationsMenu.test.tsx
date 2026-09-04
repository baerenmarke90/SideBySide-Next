// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import type { NotificationItem } from '../api/generated/models/NotificationItem';
import { notificationUnreadCountQueryKey, notificationsListQueryKey } from '../client/notificationQueries';
import m5s5 from '../i18n/locales/m5s5';
import navigation from '../i18n/locales/navigation';
import { HeaderNotificationsMenu } from './HeaderNotificationsMenu';

function LocationTracker({ onLocation }: { onLocation: (loc: string) => void }) {
  const loc = useLocation();
  onLocation(loc.pathname);
  return null;
}

function createSampleNotification(overrides: Partial<NotificationItem> = {}): NotificationItem {
  return {
    id: 'notif-1',
    spaceId: 'space-1',
    actor: { id: 'account-partner', displayName: 'Alex Partner' },
    kind: 'COMMENT_CREATED',
    targetType: 'PLAN',
    targetId: 'plan-123',
    target: { id: 'plan-123', title: 'Summer Trip' },
    readAt: null,
    createdAt: new Date('2026-09-04T09:00:00Z'),
    ...overrides,
  };
}

function renderNotificationMenu({
  unreadCount = 1,
  items = [createSampleNotification()],
}: {
  unreadCount?: number;
  items?: NotificationItem[];
} = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  const spaceId = 'space-1';
  queryClient.setQueryData(notificationUnreadCountQueryKey(spaceId), { unreadCount });
  queryClient.setQueryData(notificationsListQueryKey(spaceId), {
    pages: [{ items, nextCursor: null }],
    pageParams: [null],
  });

  let currentLocation = '/today';

  const result = render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/today']}>
        <div>
          <LocationTracker onLocation={(loc) => { currentLocation = loc; }} />
          <button data-testid="outside-target">Outside Element</button>
          <HeaderNotificationsMenu
            apiBaseUrl="http://api.example.test"
            accessToken="test-token"
            spaceId={spaceId}
            unreadCount={unreadCount}
            currentAccountId="account-user"
          />
        </div>
      </MemoryRouter>
    </QueryClientProvider>,
  );

  return {
    ...result,
    queryClient,
    getLocation: () => currentLocation,
  };
}

describe('HeaderNotificationsMenu', () => {
  it('renders unread indicator dot and aria-label when unreadCount > 0', () => {
    renderNotificationMenu({ unreadCount: 2 });
    const trigger = screen.getByRole('button', {
      name: /2 ungelesen/i,
    });
    expect(trigger.getAttribute('aria-expanded')).toBe('false');
    expect(trigger.querySelector('.notification-dot')).not.toBeNull();
  });

  it('opens preview on bell click without mounting full notifications page', () => {
    renderNotificationMenu({ unreadCount: 1 });
    const trigger = screen.getByRole('button', {
      name: /1 ungelesen/i,
    });

    act(() => {
      fireEvent.click(trigger);
    });

    expect(trigger.getAttribute('aria-expanded')).toBe('true');
    expect(screen.getByText(m5s5.notifications.previewTitle)).toBeDefined();
    // Verify preview contains the notification item
    expect(screen.getByText(/Alex Partner/)).toBeDefined();
  });

  it('clicking a target notification triggers optimistic read, updates count, navigates, and closes popover', async () => {
    const { queryClient, getLocation } = renderNotificationMenu({
      unreadCount: 1,
      items: [
        createSampleNotification({
          id: 'notif-1',
          readAt: null,
          targetType: 'PLAN',
          targetId: 'plan-123',
        }),
      ],
    });

    const trigger = screen.getByRole('button', { name: /1 ungelesen/i });
    act(() => {
      fireEvent.click(trigger);
    });

    const notifButton = screen.getByRole('button', { name: /Alex Partner/i });
    act(() => {
      fireEvent.click(notifButton);
    });

    // Popover closed
    expect(trigger.getAttribute('aria-expanded')).toBe('false');

    // Navigated to plan target
    expect(getLocation()).toBe('/plan/plans/plan-123');

    // Optimistic unread count decremented
    const unreadData = queryClient.getQueryData<{ unreadCount: number }>(
      notificationUnreadCountQueryKey('space-1'),
    );
    expect(unreadData?.unreadCount).toBe(0);

    // Optimistic item readAt set
    const listData = queryClient.getQueryData<any>(
      notificationsListQueryKey('space-1'),
    );
    expect(listData?.pages[0]?.items[0]?.readAt).not.toBeNull();
  });

  it('clicking "Alle Benachrichtigungen anzeigen" navigates to /more/notifications and closes', () => {
    const { getLocation } = renderNotificationMenu({ unreadCount: 0 });
    const trigger = screen.getByRole('button', { name: navigation.notifications });

    act(() => {
      fireEvent.click(trigger);
    });

    const allLink = screen.getByRole('link', { name: m5s5.notifications.showAll });
    expect(allLink.getAttribute('href')).toBe('/more/notifications');

    act(() => {
      fireEvent.click(allLink);
    });

    expect(trigger.getAttribute('aria-expanded')).toBe('false');
  });

  it('dismisses on outside pointerdown but stays open on inside click', () => {
    renderNotificationMenu({ unreadCount: 0 });
    const trigger = screen.getByRole('button', { name: navigation.notifications });
    const outside = screen.getByTestId('outside-target');

    act(() => {
      fireEvent.click(trigger);
    });
    expect(trigger.getAttribute('aria-expanded')).toBe('true');

    // Inside panel click
    const panel = screen.getByRole('region', { name: m5s5.notifications.previewTitle });
    act(() => {
      fireEvent.pointerDown(panel);
    });
    expect(trigger.getAttribute('aria-expanded')).toBe('true');

    // Outside click
    act(() => {
      fireEvent.pointerDown(outside);
    });
    expect(trigger.getAttribute('aria-expanded')).toBe('false');
  });

  it('dismisses on Escape key and restores focus to bell trigger', () => {
    renderNotificationMenu({ unreadCount: 0 });
    const trigger = screen.getByRole('button', { name: navigation.notifications });

    act(() => {
      fireEvent.click(trigger);
    });
    expect(trigger.getAttribute('aria-expanded')).toBe('true');

    act(() => {
      fireEvent.keyDown(window, { key: 'Escape' });
    });
    expect(trigger.getAttribute('aria-expanded')).toBe('false');
    expect(document.activeElement).toBe(trigger);
  });

  it('renders empty state when there are no notifications', () => {
    renderNotificationMenu({ unreadCount: 0, items: [] });
    const trigger = screen.getByRole('button', { name: navigation.notifications });

    act(() => {
      fireEvent.click(trigger);
    });

    expect(screen.getByText(m5s5.notifications.emptyPreview)).toBeDefined();
  });
});
