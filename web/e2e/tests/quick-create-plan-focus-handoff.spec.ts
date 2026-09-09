import { expect, type Page, test } from '@playwright/test';
import de from '../../src/i18n/locales/de';
import m5s3 from '../../src/i18n/locales/m5s3';
import navigation from '../../src/i18n/locales/navigation';

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const SPACE_ID = '22222222-2222-4222-8222-222222222222';
const PROFILE_ID = '33333333-3333-4333-8333-333333333333';
const TEST_NOW = '2026-09-01T10:00:00Z';

/**
 * Focused browser harness for the #810/#839 P2 remediation: Quick Create's
 * Wunsch/Plan actions must land the user directly inside the already
 * existing Planning composer with the primary title input focused, instead
 * of merely opening and scrolling to the disclosure that contains it.
 */
async function installPlanningMocks(page: Page): Promise<void> {
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

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/activity`
    ) {
      await fulfillJson({ items: [], nextCursor: null });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard`
    ) {
      await fulfillJson({
        keepsake: null,
        recentShared: [],
        relationshipDuration: null,
        retrospective: null,
        space: { partner: null, spaceId: SPACE_ID },
        thinkingOfYouAvailableAt: null,
        upcoming: [],
      });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/wishes`) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/plans`) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/places`) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    await fulfillJson(
      {
        code: 'E2E_UNEXPECTED_REQUEST',
        detail: `The browser test did not define this API request: ${method} ${pathname}.`,
        status: 500,
        title: 'Unexpected browser test request',
      },
      500,
    );
  });
}

async function signIn(page: Page): Promise<void> {
  await page.getByLabel(de.login.email).fill('anna@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
  await expect(page.getByLabel(de.login.email)).toHaveCount(0);
}

test('390x844: Quick Create -> Wunsch lands focused in the existing Wish composer, and Back returns to Today', async ({
  page,
}) => {
  await installPlanningMocks(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/today');
  await signIn(page);

  await page.getByRole('button', { name: navigation.newContent }).click();
  await expect(
    page.getByRole('dialog', { name: navigation.quickCreateTitle }),
  ).toBeVisible();

  await page.getByText(navigation.quickCreateWish, { exact: true }).click();

  await expect(page).toHaveURL(/\/plan#wish-title$/);
  await expect(page.getByRole('dialog')).toHaveCount(0);

  const titleInput = page.locator('#create-wish-title');
  await expect(titleInput).toBeVisible();
  await expect(titleInput).toBeFocused();

  // No extra tap needed: typing lands directly in the title field.
  await page.keyboard.type('Gemeinsamer Segeltörn');
  await expect(titleInput).toHaveValue('Gemeinsamer Segeltörn');

  // Browser Back returns to the originating context without an extra
  // history entry for the disclosure state itself.
  await page.goBack();
  await expect(page).toHaveURL(/\/today$/);
});

test('390x844: Quick Create -> Plan lands focused in the existing Plan composer', async ({
  page,
}) => {
  await installPlanningMocks(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/today');
  await signIn(page);

  await page.getByRole('button', { name: navigation.newContent }).click();
  await page.getByText(navigation.quickCreatePlan, { exact: true }).click();

  await expect(page).toHaveURL(/\/plan#plan-title$/);
  await expect(page.getByRole('dialog')).toHaveCount(0);

  const titleInput = page.locator('#create-plan-title');
  await expect(titleInput).toBeVisible();
  await expect(titleInput).toBeFocused();

  await page.keyboard.type('Herbstliches Date-Dinner');
  await expect(titleInput).toHaveValue('Herbstliches Date-Dinner');

  // No auto-focus on secondary fields such as the place picker.
  await expect(page.locator('#create-plan-place')).not.toBeFocused();
});

test('a normal /plan visit without Quick Create does not force focus into either composer', async ({
  page,
}) => {
  await installPlanningMocks(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/today');
  await signIn(page);

  await page.goto('/plan');
  await expect(
    page.getByRole('heading', { name: m5s3.overview.title }),
  ).toBeVisible();

  await expect(page.locator('#create-wish-title')).not.toBeFocused();
  await expect(page.locator('#create-plan-title')).not.toBeFocused();
});

test('320 CSS px reflow: the focused Wish composer stays reachable without horizontal overflow', async ({
  page,
}) => {
  await installPlanningMocks(page);
  await page.setViewportSize({ width: 320, height: 844 });
  await page.goto('/today');
  await signIn(page);

  await page.getByRole('button', { name: navigation.newContent }).click();
  await page.getByText(navigation.quickCreateWish, { exact: true }).click();

  const titleInput = page.locator('#create-wish-title');
  await expect(titleInput).toBeFocused();

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth + 1,
  );
  expect(hasHorizontalOverflow).toBe(false);
});

test('small-height viewport: the focused Plan composer input is not hidden by sticky chrome', async ({
  page,
}) => {
  await installPlanningMocks(page);
  await page.setViewportSize({ width: 390, height: 520 });
  await page.goto('/today');
  await signIn(page);

  await page.getByRole('button', { name: navigation.newContent }).click();
  await page.getByText(navigation.quickCreatePlan, { exact: true }).click();

  const titleInput = page.locator('#create-plan-title');
  await expect(titleInput).toBeFocused();
  await expect(titleInput).toBeInViewport();
});

test('1440 Expanded: Quick Create -> Wunsch opens the desktop popover variant and still focuses the composer title', async ({
  page,
}) => {
  await installPlanningMocks(page);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/today');
  await signIn(page);

  await page.getByRole('button', { name: navigation.newContent }).click();
  await expect(
    page.getByRole('menu', { name: navigation.quickCreateTitle }),
  ).toBeVisible();
  await page
    .getByRole('menuitem', { name: navigation.quickCreateWish })
    .click();

  await expect(page).toHaveURL(/\/plan#wish-title$/);
  const titleInput = page.locator('#create-wish-title');
  await expect(titleInput).toBeFocused();
});
