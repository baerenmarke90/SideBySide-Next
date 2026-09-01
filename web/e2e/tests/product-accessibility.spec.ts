import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import de from '../../src/i18n/locales/de';
import m5s5 from '../../src/i18n/locales/m5s5';
import navigation from '../../src/i18n/locales/navigation';

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

    if (method === 'POST' && pathname === '/api/v1/auth/sign-in') {
      await fulfillJson({
        account: {
          displayName: 'Anna',
          id: ACCOUNT_ID,
        },
        tokens: {
          accessExpiresAt: '2026-09-01T11:00:00Z',
          accessToken: 'browser-e2e-access-token',
          refreshExpiresAt: '2026-09-08T10:00:00Z',
          refreshToken: 'browser-e2e-refresh-token',
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
        {
          role: 'MEMBER',
          spaceId: SPACE_ID,
          status: 'ACTIVE',
        },
      ]);
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard`
    ) {
      await fulfillJson({
        recentShared: [],
        relationshipDuration: null,
        retrospective: null,
        space: {
          partner: null,
          spaceId: SPACE_ID,
        },
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

async function signIn(page: Page): Promise<void> {
  await page.getByLabel(de.login.email).fill('anna@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
}

test('compact sign-in is keyboard operable, wraps German copy, and is axe-clean', async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto('/');

  await expect(page.locator('html')).toHaveAttribute('lang', 'de');
  await expect(
    page.getByRole('heading', {
      name: de.login.introHeading,
      level: 1,
    }),
  ).toBeVisible();

  await page.getByLabel(de.login.email).focus();
  await page.keyboard.press('Tab');
  await expect(page.getByLabel(de.login.password)).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(
    page.getByRole('button', { name: de.login.submit }),
  ).toBeFocused();

  await expectNoHorizontalOverflow(page);
  await expectNoWcagViolations(page);
});

test('expanded authenticated shell keeps deep links, back, focus, and accessibility intact', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const unexpectedRequests = await installAuthorizedApiMocks(page);

  // Exercise the deployed SPA/direct-entry contract through an existing legacy
  // deep link. After authentication, the route model must canonicalize it.
  await page.goto('/dashboard');
  await signIn(page);

  await expect(page).toHaveURL(/\/today$/);
  await expect(
    page.getByRole('heading', { name: m5s5.dashboard.title, level: 1 }),
  ).toBeVisible();
  await expect(page.getByText(m5s5.dashboard.recentEmpty)).toBeVisible();

  const skipLink = page.getByRole('link', {
    name: de.navigation.skipToContent,
  });
  await skipLink.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main-content')).toBeFocused();

  await page.getByRole('link', { name: navigation.more, exact: true }).click();
  await expect(page).toHaveURL(/\/more$/);
  await expect(
    page.getByRole('heading', { name: de.more.title, level: 1 }),
  ).toBeVisible();

  await page.goBack();
  await expect(page).toHaveURL(/\/today(?:#main-content)?$/);
  await expect(
    page.getByRole('heading', { name: m5s5.dashboard.title, level: 1 }),
  ).toBeVisible();

  await expectNoHorizontalOverflow(page);
  await expectNoWcagViolations(page);
  expect(unexpectedRequests).toEqual([]);
});
