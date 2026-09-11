import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import de from '../../src/i18n/locales/de';
import privateArea from '../../src/i18n/locales/privateArea';

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const SPACE_ID = '22222222-2222-4222-8222-222222222222';
const PROFILE_ID = '33333333-3333-4333-8333-333333333333';
const TEST_NOW = '2026-09-01T10:00:00Z';

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

async function installAuthorizedApiMocks(page: Page): Promise<string[]> {
  const unexpectedRequests: string[] = [];

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
          accessExpiresAt: new Date(Date.now() + 3_600_000).toISOString(),
          accessToken: 'browser-e2e-access-token',
          refreshExpiresAt: new Date(Date.now() + 86_400_000).toISOString(),
          refreshToken: 'browser-e2e-refresh-token',
        },
      });
      return;
    }

    if (method === 'GET' && pathname === '/api/v1/auth/me') {
      await fulfillJson({ displayName: 'Anna', id: ACCOUNT_ID });
      return;
    }

    if (method === 'POST' && pathname === '/api/v1/auth/refresh') {
      await fulfillJson({
        accessExpiresAt: new Date(Date.now() + 3_600_000).toISOString(),
        accessToken: 'browser-e2e-access-token-refreshed',
        refreshExpiresAt: new Date(Date.now() + 86_400_000).toISOString(),
        refreshToken: 'browser-e2e-refresh-token-refreshed',
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
      await fulfillJson({ id: SPACE_ID, createdAt: TEST_NOW, partners: [] });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/profile`) {
      await fulfillJson({
        spaceId: SPACE_ID,
        version: 1,
        relationshipStartedOn: null,
        showRelationshipDuration: false,
      });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/profile-preferences`
    ) {
      await fulfillJson({ items: [] });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard/preferences`
    ) {
      await fulfillJson({ items: [{ moduleKey: 'upcoming', itemLimit: 2 }] });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/dashboard`) {
      await fulfillJson({
        recentShared: [],
        relationshipDuration: null,
        retrospective: null,
        space: { partner: null, spaceId: SPACE_ID },
        upcoming: [],
      });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/profiles/${ACCOUNT_ID}`
    ) {
      await fulfillJson({
        accountId: ACCOUNT_ID,
        createdAt: TEST_NOW,
        displayName: 'Anna',
        id: PROFILE_ID,
        preferences: [],
        profileAttachmentId: null,
        updatedAt: TEST_NOW,
        version: 1,
      });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/notifications/unread-count`
    ) {
      await fulfillJson({ unreadCount: 0 });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/activity`) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    if (
      method === 'GET' &&
      [
        `/api/v1/spaces/${SPACE_ID}/search`,
        `/api/v1/spaces/${SPACE_ID}/notifications`,
        `/api/v1/spaces/${SPACE_ID}/story`,
        `/api/v1/spaces/${SPACE_ID}/collections`,
        `/api/v1/spaces/${SPACE_ID}/plans`,
        `/api/v1/spaces/${SPACE_ID}/places`,
        `/api/v1/spaces/${SPACE_ID}/wishes`,
      ].includes(pathname)
    ) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    unexpectedRequests.push(`${method} ${pathname}`);
    await fulfillJson(
      {
        code: 'E2E_UNEXPECTED_REQUEST',
        detail: 'The browser test did not define this API request.',
        status: 500,
        title: 'Unexpected browser test request',
      },
      500,
    );
  });

  return unexpectedRequests;
}

async function signInAndOpenPrivateArea(page: Page): Promise<string[]> {
  const unexpectedRequests = await installAuthorizedApiMocks(page);
  await page.goto('/today');
  await page.getByLabel(de.login.email).fill('anna@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
  await expect(page.getByLabel(de.login.email)).toHaveCount(0);

  await page.goto('/more/private');
  await expect(page).toHaveURL(/\/more\/private$/);
  await expect(
    page.getByRole('heading', { name: privateArea.eyebrow, level: 1 }),
  ).toBeVisible();

  return unexpectedRequests;
}

async function expectPrivateReferenceStructure(page: Page): Promise<void> {
  const banner = page.getByRole('note');
  await expect(banner).toContainText(privateArea.privacyLabel);
  await expect(banner).toContainText(privateArea.entry.privacy);

  const cards = page.locator('.private-area-destination-card');
  await expect(cards).toHaveCount(3);
  await expect(cards.nth(0)).toHaveAttribute('href', '/more/private/notes');
  await expect(cards.nth(1)).toHaveAttribute('href', '/more/private/gift-ideas');
  await expect(cards.nth(2)).toHaveAttribute('href', '/more/private/collections');
  await expect(cards.nth(0)).toContainText(privateArea.notes.title);
  await expect(cards.nth(1)).toContainText(privateArea.gifts.title);
  await expect(cards.nth(2)).toContainText(privateArea.collections.title);

  await expectNoHorizontalOverflow(page);
  await expectNoWcagViolations(page);
}

for (const colorScheme of ['light', 'dark'] as const) {
  test(`private area matches the 390 product-reference composition in ${colorScheme} mode`, async ({
    page,
  }, testInfo) => {
    await page.emulateMedia({ colorScheme });
    await page.addInitScript(() => {
      window.localStorage.setItem('sidebyside.theme', 'system');
    });
    await page.setViewportSize({ width: 390, height: 844 });

    const unexpectedRequests = await signInAndOpenPrivateArea(page);
    await expect(page.locator('html')).toHaveAttribute('data-theme', colorScheme);
    await expectPrivateReferenceStructure(page);

    await page.screenshot({
      path: testInfo.outputPath(`private-area-390-${colorScheme}.png`),
      fullPage: true,
    });
    expect(unexpectedRequests).toEqual([]);
  });
}

test('private area reflows at 320 CSS px and removes decorative motion', async ({
  page,
}, testInfo) => {
  await page.emulateMedia({ colorScheme: 'light', reducedMotion: 'reduce' });
  await page.addInitScript(() => {
    window.localStorage.setItem('sidebyside.theme', 'system');
  });
  await page.setViewportSize({ width: 320, height: 844 });

  const unexpectedRequests = await signInAndOpenPrivateArea(page);
  await expectPrivateReferenceStructure(page);

  const firstCard = page.locator('.private-area-destination-card').first();
  const transitionDuration = await firstCard.evaluate(
    (element) => getComputedStyle(element).transitionDuration,
  );
  expect(transitionDuration).toBe('0s');

  const box = await firstCard.boundingBox();
  expect(box).not.toBeNull();
  expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(320);

  await page.screenshot({
    path: testInfo.outputPath('private-area-320-light.png'),
    fullPage: true,
  });
  expect(unexpectedRequests).toEqual([]);
});

test('private area keeps the accepted hierarchy in expanded Web', async ({
  page,
}, testInfo) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.addInitScript(() => {
    window.localStorage.setItem('sidebyside.theme', 'system');
  });
  await page.setViewportSize({ width: 1440, height: 900 });

  const unexpectedRequests = await signInAndOpenPrivateArea(page);
  await expectPrivateReferenceStructure(page);

  await page.screenshot({
    path: testInfo.outputPath('private-area-1440-light.png'),
    fullPage: true,
  });
  expect(unexpectedRequests).toEqual([]);
});

test('private area remains usable at 200 percent layout zoom', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.setViewportSize({ width: 780, height: 900 });

  const unexpectedRequests = await signInAndOpenPrivateArea(page);
  await page.locator('html').evaluate((element) => {
    element.style.zoom = '2';
  });

  await expectNoHorizontalOverflow(page);
  await expectNoWcagViolations(page);
  expect(unexpectedRequests).toEqual([]);
});
