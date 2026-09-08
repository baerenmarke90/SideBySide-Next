import AxeBuilder from '@axe-core/playwright';
import { expect, type Page, test } from '@playwright/test';
import de from '../../src/i18n/locales/de';

const ACCOUNT_ID = '00000000-0000-0000-0000-000000000001';
const PARTNER_ID = '00000000-0000-0000-0000-000000000002';
const SPACE_ID = '00000000-0000-0000-0000-000000000010';
const PROFILE_ID = '00000000-0000-0000-0000-000000000020';

/**
 * Reproduces the real-demo composition complaint (#790/#791 second
 * follow-up): several short upcoming items, each previously stretched into
 * a nearly full-width row (title far left, date far right) that read as a
 * scheduling table rather than shared planning. Four items with varied
 * title lengths and no Relationship Signal card (single-column planning
 * area, the widest/worst case for a stretched row) is enough to reproduce
 * it on a real desktop viewport.
 */
const UPCOMING_ITEMS = [
  {
    id: 'p1',
    type: 'PLAN',
    titleOrText: 'Wanderung',
    scheduledAt: '2026-09-10T10:00:00Z',
  },
  {
    id: 'p2',
    type: 'PLAN',
    titleOrText: 'Kino-Abend mit Popcorn',
    scheduledAt: '2026-09-12T18:00:00Z',
  },
  {
    id: 'p3',
    type: 'PLAN',
    titleOrText: 'Brunch',
    scheduledAt: '2026-09-15T09:00:00Z',
  },
  {
    id: 'p4',
    type: 'PLAN',
    titleOrText: 'Wochenendtrip an die Ostsee',
    scheduledAt: '2026-09-20T09:00:00Z',
  },
];

async function installMocks(page: Page): Promise<void> {
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
        account: { displayName: 'Anna', id: ACCOUNT_ID },
        tokens: {
          accessExpiresAt: new Date(Date.now() + 3600_000).toISOString(),
          accessToken: 'today-agenda-access-token',
          refreshExpiresAt: new Date(Date.now() + 86400_000).toISOString(),
          refreshToken: 'today-agenda-refresh-token',
        },
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
    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}`) {
      await fulfillJson({
        id: SPACE_ID,
        createdAt: '2026-01-01T00:00:00Z',
        partners: [
          { id: ACCOUNT_ID, displayName: 'Anna' },
          { id: PARTNER_ID, displayName: 'Ben' },
        ],
      });
      return;
    }
    if (
      method === 'GET' &&
      (pathname === `/api/v1/spaces/${SPACE_ID}/profiles/${ACCOUNT_ID}` ||
        pathname === `/api/v1/spaces/${SPACE_ID}/profiles/${PARTNER_ID}`)
    ) {
      const isPartner = pathname.endsWith(PARTNER_ID);
      await fulfillJson({
        accountId: isPartner ? PARTNER_ID : ACCOUNT_ID,
        createdAt: '2026-01-01T00:00:00Z',
        displayName: isPartner ? 'Ben' : 'Anna',
        id: isPartner ? '00000000-0000-0000-0000-000000000022' : PROFILE_ID,
        preferences: [],
        profileAttachmentId: null,
        updatedAt: '2026-01-01T00:00:00Z',
        version: 1,
      });
      return;
    }
    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/activity`
    ) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }
    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/notifications/unread-count`
    ) {
      await fulfillJson({ unreadCount: 0 });
      return;
    }
    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard`
    ) {
      await fulfillJson({
        space: {
          spaceId: SPACE_ID,
          partner: { id: PARTNER_ID, displayName: 'Ben' },
        },
        relationshipDuration: { daysTogether: 250, startedOn: '2026-01-01' },
        retrospective: null,
        recentShared: [],
        upcoming: UPCOMING_ITEMS,
      });
      return;
    }
    await fulfillJson({}, 200);
  });
}

async function signIn(page: Page): Promise<void> {
  await page.getByLabel(de.login.email).fill('anna@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
  await expect(page).toHaveURL(/\/today$/);
}

test('Today "Demnächst" renders compact, bounded-width planning tiles instead of full-width table rows on desktop', async ({
  page,
}) => {
  await installMocks(page);
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto('/today');
  await signIn(page);
  await page.waitForSelector('.today-agenda-row');

  const rowWidths = await page
    .locator('.today-agenda-row')
    .evaluateAll((rows) =>
      rows.map((row) => row.getBoundingClientRect().width),
    );

  expect(rowWidths).toHaveLength(UPCOMING_ITEMS.length);
  // None of these tiles carries more than a short title, date, and icon -
  // a row spanning most of a 1920px viewport is the "administrative table
  // row" regression this fix removes.
  for (const width of rowWidths) {
    expect(width).toBeLessThan(320);
  }

  // Wrapping into multiple tiles per line is how the available width gets
  // used intentionally instead of stretching a single item across it.
  const rowTops = await page
    .locator('.today-agenda-row')
    .evaluateAll((rows) => rows.map((row) => row.getBoundingClientRect().top));
  expect(new Set(rowTops).size).toBeLessThan(rowTops.length);

  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);

  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations).toEqual([]);
});

test('Today "Demnächst" stays a single stacked column with no overflow on mobile (no regression)', async ({
  page,
}) => {
  await installMocks(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/today');
  await signIn(page);
  await page.waitForSelector('.today-agenda-row');

  const rowLefts = await page
    .locator('.today-agenda-row')
    .evaluateAll((rows) => rows.map((row) => row.getBoundingClientRect().left));
  expect(new Set(rowLefts).size).toBe(1);

  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);

  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations).toEqual([]);
});
