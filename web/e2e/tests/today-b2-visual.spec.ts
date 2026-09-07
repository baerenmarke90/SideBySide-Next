import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import de from '../../src/i18n/locales/de';
import navigation from '../../src/i18n/locales/navigation';

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const PARTNER_ID = '22222222-2222-4222-8222-222222222222';
const SPACE_ID = '33333333-3333-4333-8333-333333333333';
const ACCOUNT_PROFILE_ID = '44444444-4444-4444-8444-444444444444';
const PARTNER_PROFILE_ID = '55555555-5555-4555-8555-555555555555';
const TEST_NOW = '2026-09-07T10:00:00Z';
const DEMO_IMAGE_PATH = '../../backend/demo_assets/images/cabin-lake.jpg';

type DashboardFixture = {
  recentShared: unknown[];
  relationshipDuration: unknown;
  retrospective: unknown;
  space: {
    partner: { id: string; displayName: string } | null;
    spaceId: string;
  };
  upcoming: unknown[];
};

type MockState = {
  dashboard: DashboardFixture;
  activityItems: unknown[];
};

const partner = { id: PARTNER_ID, displayName: 'Lea' };

const RICH_DASHBOARD: DashboardFixture = {
  space: { partner, spaceId: SPACE_ID },
  relationshipDuration: {
    daysTogether: 428,
    displayMode: 'YEARS_MONTHS',
    startedOn: '2025-07-06',
  },
  upcoming: [
    {
      id: 'plan-market',
      type: 'PLAN',
      titleOrText: 'Saturday flea market',
      createdAt: TEST_NOW,
      occurredOn: null,
      scheduledAt: '2026-09-18T10:00:00Z',
    },
    {
      id: 'plan-hike',
      type: 'PLAN',
      titleOrText: 'Autumn hike through the high forest',
      createdAt: TEST_NOW,
      occurredOn: null,
      scheduledAt: '2026-10-03T09:00:00Z',
    },
    {
      id: 'plan-concert',
      type: 'PLAN',
      titleOrText: 'Concert in autumn',
      createdAt: TEST_NOW,
      occurredOn: null,
      scheduledAt: '2026-10-24T18:30:00Z',
    },
  ],
  recentShared: [
    {
      id: 'memory-breakfast',
      type: 'MEMORY',
      titleOrText: 'Sunday morning, coffee and far too many croissants',
      createdAt: '2026-09-04T08:00:00Z',
      occurredOn: '2026-09-04',
      scheduledAt: null,
      previewAttachmentId: null,
    },
    {
      id: 'heart-note',
      type: 'HEART_MOMENT',
      titleOrText: 'Thank you for this ordinary, good evening together.',
      createdAt: '2026-09-03T20:15:00Z',
      occurredOn: '2026-09-03',
      scheduledAt: null,
      previewAttachmentId: null,
    },
  ],
  retrospective: {
    id: 'memory-cabin',
    type: 'MEMORY',
    titleOrText:
      'The morning by the lake when we simply stayed a little longer',
    createdAt: '2025-09-07T07:30:00Z',
    occurredOn: '2025-09-07',
    scheduledAt: null,
    previewAttachmentId: 'attachment-cabin',
  },
};

const NO_RETROSPECTIVE_DASHBOARD: DashboardFixture = {
  ...RICH_DASHBOARD,
  retrospective: null,
  recentShared: [
    {
      id: 'memory-lake-recent',
      type: 'MEMORY',
      titleOrText: 'One more late summer evening by the water',
      createdAt: '2026-09-05T18:30:00Z',
      occurredOn: '2026-09-05',
      scheduledAt: null,
      previewAttachmentId: 'attachment-cabin',
    },
    ...RICH_DASHBOARD.recentShared,
  ],
};

const NO_IMAGE_DASHBOARD: DashboardFixture = {
  ...RICH_DASHBOARD,
  retrospective: null,
  recentShared: [
    {
      id: 'memory-text-only',
      type: 'MEMORY',
      titleOrText:
        'A walk after the rain, with wet shoes, long conversations, and the detour we now always take',
      createdAt: '2026-09-06T19:10:00Z',
      occurredOn: '2026-09-06',
      scheduledAt: null,
      previewAttachmentId: null,
    },
    {
      id: 'heart-text-only',
      type: 'HEART_MOMENT',
      titleOrText: 'For later: this is exactly what home feels like.',
      createdAt: '2026-09-05T21:00:00Z',
      occurredOn: '2026-09-05',
      scheduledAt: null,
      previewAttachmentId: null,
    },
  ],
};

const SPARSE_DASHBOARD: DashboardFixture = {
  space: { partner, spaceId: SPACE_ID },
  relationshipDuration: {
    daysTogether: 19,
    displayMode: 'DAYS',
    startedOn: '2026-08-19',
  },
  upcoming: [],
  recentShared: [],
  retrospective: null,
};

const PARTNER_ACTIVITY = [
  {
    id: 'activity-comment',
    kind: 'COMMENT_CREATED',
    actorId: PARTNER_ID,
    targetId: 'memory-breakfast',
    targetType: 'MEMORY',
    createdAt: '2026-09-07T08:30:00Z',
    occurredAt: '2026-09-07T08:30:00Z',
    sourceEventId: 'event-comment',
  },
];

async function expectNoWcagViolations(page: Page): Promise<void> {
  const result = await new AxeBuilder({ page })
    .withTags([
      'wcag2a',
      'wcag2aa',
      'wcag21a',
      'wcag21aa',
      'wcag22a',
      'wcag22aa',
    ])
    .analyze();
  const summary = result.violations
    .map(
      (violation) =>
        `${violation.id} (${violation.impact ?? 'unknown'}): ${violation.nodes.length} node(s)`,
    )
    .join('\n');
  expect(result.violations, summary || 'No axe violations').toEqual([]);
}

async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
}

async function installAuthorizedApiMocks(
  page: Page,
  state: MockState,
): Promise<string[]> {
  const unexpectedRequests: string[] = [];

  await page.route('**/qa/eimir-cabin-lake.jpg', (route) =>
    route.fulfill({ path: DEMO_IMAGE_PATH, contentType: 'image/jpeg' }),
  );

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const method = request.method();
    const pathname = new URL(request.url()).pathname;
    const fulfillJson = async (body: unknown, status = 200) =>
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(body),
      });

    if (method === 'GET' && pathname === '/api/v1/instance/status') {
      await fulfillJson({
        maintenanceMode: false,
        registrationAvailable: true,
        registrationUnavailableReason: null,
        auth: {
          localPassword: true,
          passkey: true,
          magicLink: true,
          oidc: false,
        },
      });
      return;
    }

    if (method === 'POST' && pathname === '/api/v1/auth/sign-in') {
      await fulfillJson({
        account: { displayName: 'Philipp', id: ACCOUNT_ID },
        tokens: {
          accessExpiresAt: new Date(Date.now() + 3600_000).toISOString(),
          accessToken: 'b2-browser-access-token',
          refreshExpiresAt: new Date(Date.now() + 86400_000).toISOString(),
          refreshToken: 'b2-browser-refresh-token',
        },
      });
      return;
    }

    if (method === 'GET' && pathname === '/api/v1/auth/me') {
      await fulfillJson({ displayName: 'Philipp', id: ACCOUNT_ID });
      return;
    }

    if (method === 'POST' && pathname === '/api/v1/auth/refresh') {
      await fulfillJson({
        accessExpiresAt: new Date(Date.now() + 3600_000).toISOString(),
        accessToken: 'b2-browser-access-token-refreshed',
        refreshExpiresAt: new Date(Date.now() + 86400_000).toISOString(),
        refreshToken: 'b2-browser-refresh-token-refreshed',
      });
      return;
    }

    if (method === 'GET' && pathname === '/api/v1/auth/capabilities') {
      await fulfillJson({ serverAdmin: false });
      return;
    }

    if (method === 'GET' && pathname === '/api/v1/auth/memberships') {
      await fulfillJson([
        { role: 'MEMBER', spaceId: SPACE_ID, status: 'ACTIVE' },
      ]);
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard`
    ) {
      await fulfillJson(state.dashboard);
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/activity`
    ) {
      await fulfillJson({
        hasMore: false,
        items: state.activityItems,
        nextCursor: null,
      });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/notifications/unread-count`
    ) {
      await fulfillJson({ unreadCount: 2 });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/profiles/${ACCOUNT_ID}`
    ) {
      await fulfillJson({
        accountId: ACCOUNT_ID,
        createdAt: TEST_NOW,
        displayName: 'Philipp',
        id: ACCOUNT_PROFILE_ID,
        preferences: [],
        profileAttachmentId: null,
        updatedAt: TEST_NOW,
        version: 1,
      });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/profiles/${PARTNER_ID}`
    ) {
      await fulfillJson({
        accountId: PARTNER_ID,
        createdAt: TEST_NOW,
        displayName: 'Lea',
        id: PARTNER_PROFILE_ID,
        preferences: [],
        profileAttachmentId: null,
        updatedAt: TEST_NOW,
        version: 1,
      });
      return;
    }

    if (
      method === 'POST' &&
      /^\/api\/v1\/spaces\/[^/]+\/attachments\/[^/]+\/read-access$/.test(
        pathname,
      )
    ) {
      await fulfillJson({
        method: 'STREAM',
        url: '/qa/eimir-cabin-lake.jpg',
      });
      return;
    }

    unexpectedRequests.push(`${method} ${pathname}`);
    await fulfillJson(
      {
        code: 'E2E_UNEXPECTED_REQUEST',
        detail: 'B2 visual QA did not define this API request.',
        status: 500,
        title: 'Unexpected browser test request',
      },
      500,
    );
  });

  return unexpectedRequests;
}

async function signIn(page: Page): Promise<void> {
  await page.getByLabel(de.login.email).fill('philipp@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
  await expect(page).toHaveURL(/\/today$/);
}

async function applyTheme(
  page: Page,
  colorScheme: 'light' | 'dark',
): Promise<void> {
  await page.emulateMedia({ colorScheme, reducedMotion: 'reduce' });
  await page.evaluate(() => {
    window.localStorage.setItem('sidebyside.theme', 'system');
  });
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', colorScheme);
}

async function waitForToday(page: Page, expectImage: boolean): Promise<void> {
  await expect(page.locator('.today-hero.couple-presence-card')).toBeVisible();
  if (expectImage) {
    await expect(page.locator('.today-card-media img').first()).toBeVisible();
  }
  await expectNoHorizontalOverflow(page);
  await expectNoWcagViolations(page);
}

test('B2 rich runtime evidence covers expanded and compact light/dark', async ({
  page,
}, testInfo) => {
  const state: MockState = {
    dashboard: RICH_DASHBOARD,
    activityItems: PARTNER_ACTIVITY,
  };
  const unexpectedRequests = await installAuthorizedApiMocks(page, state);

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/today');
  await signIn(page);

  for (const colorScheme of ['light', 'dark'] as const) {
    await applyTheme(page, colorScheme);
    await waitForToday(page, true);
    await expect(page.locator('.shell-nav-desktop')).toBeVisible();
    await expect(page.locator('.shell-sidebar')).toHaveCount(0);
    await expect(
      page.getByRole('link', { name: navigation.search }),
    ).toBeVisible();
    await expect(page.locator('.header-notifications-trigger')).toBeVisible();
    await expect(page.locator('.header-profile-trigger')).toBeVisible();
    await expect(
      page.locator('.shell-header-create .quick-create-trigger'),
    ).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath(`today-b2-rich-expanded-${colorScheme}.png`),
      fullPage: true,
    });
  }

  await page.setViewportSize({ width: 390, height: 844 });
  for (const colorScheme of ['light', 'dark'] as const) {
    await applyTheme(page, colorScheme);
    await waitForToday(page, true);
    await expect(page.locator('.mobile-bottom-nav')).toBeVisible();
    await expect(page.locator('.mobile-quick-create')).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath(`today-b2-rich-compact-${colorScheme}.png`),
      fullPage: true,
    });
  }

  expect(unexpectedRequests).toEqual([]);
});

test('B2 no-retrospective runtime promotes a real recent memory instead of restoring dashboard cards', async ({
  page,
}, testInfo) => {
  const state: MockState = {
    dashboard: NO_RETROSPECTIVE_DASHBOARD,
    activityItems: PARTNER_ACTIVITY,
  };
  const unexpectedRequests = await installAuthorizedApiMocks(page, state);

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/today');
  await signIn(page);
  await applyTheme(page, 'light');
  await waitForToday(page, true);
  await expect(page.locator('.today-section-keepsake-recent')).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath('today-b2-no-retrospective-expanded-light.png'),
    fullPage: true,
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await applyTheme(page, 'light');
  await waitForToday(page, true);
  await expect(page.locator('.today-section-keepsake-recent')).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath('today-b2-no-retrospective-compact-light.png'),
    fullPage: true,
  });

  expect(unexpectedRequests).toEqual([]);
});

test('B2 no-image state, keyboard flow and 200 percent zoom-equivalent reflow remain usable', async ({
  page,
}, testInfo) => {
  const state: MockState = {
    dashboard: NO_IMAGE_DASHBOARD,
    activityItems: PARTNER_ACTIVITY,
  };
  const unexpectedRequests = await installAuthorizedApiMocks(page, state);

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/today');
  await signIn(page);
  await applyTheme(page, 'light');
  await waitForToday(page, false);
  await expect(page.locator('.today-card-media')).toHaveCount(0);

  const skipLink = page.getByRole('link', {
    name: de.navigation.skipToContent,
  });
  await skipLink.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main-content')).toBeFocused();

  const quickCreate = page.locator(
    '.shell-header-create .quick-create-trigger',
  );
  await quickCreate.focus();
  await expect(quickCreate).toBeFocused();
  await page.keyboard.press('ArrowDown');
  await expect(page.getByRole('menu')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(quickCreate).toBeFocused();

  await page.screenshot({
    path: testInfo.outputPath('today-b2-no-image-expanded-light.png'),
    fullPage: true,
  });

  // Chromium exposes page scale separately from layout viewport. A 1440px
  // desktop at 200% browser zoom reflows against roughly 720 CSS pixels, so
  // exercise that equivalent layout width rather than CSS `zoom`, which scales
  // after layout and can manufacture overflow that real browser zoom avoids.
  await page.setViewportSize({ width: 720, height: 900 });
  await expect(page.locator('.mobile-bottom-nav')).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectNoWcagViolations(page);
  expect(unexpectedRequests).toEqual([]);
});

test('B2 sparse new Space preserves couple presence and intentional breathing room', async ({
  page,
}, testInfo) => {
  const state: MockState = {
    dashboard: SPARSE_DASHBOARD,
    activityItems: [],
  };
  const unexpectedRequests = await installAuthorizedApiMocks(page, state);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/today');
  await signIn(page);
  await applyTheme(page, 'dark');
  await waitForToday(page, false);
  await expect(page.locator('.new-space-experience')).toBeVisible();
  await expect(page.locator('.couple-presence-card')).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath('today-b2-sparse-compact-dark.png'),
    fullPage: true,
  });

  expect(unexpectedRequests).toEqual([]);
});
