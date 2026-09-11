import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import de from '../../src/i18n/locales/de';
import m5s3 from '../../src/i18n/locales/m5s3';

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const SPACE_ID = '22222222-2222-4222-8222-222222222222';
const PROFILE_ID = '33333333-3333-4333-8333-333333333333';
const PLAN_ID = '44444444-4444-4444-8444-444444444444';
const WISH_ID = '55555555-5555-4555-8555-555555555555';
const TEST_NOW = '2026-09-01T10:00:00Z';

const PLAN_TITLE = 'Picnic in the park';
const WISH_TITLE = 'Weekend trip to Lisbon';

type MockOptions = { plansFail?: boolean; plansDelayMs?: number };

async function installMocks(
  page: Page,
  options: MockOptions = {},
): Promise<void> {
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
          accessToken: 'planning-reference-access-token',
          refreshExpiresAt: new Date(Date.now() + 86_400_000).toISOString(),
          refreshToken: 'planning-reference-refresh-token',
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
      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard/preferences`
    ) {
      await fulfillJson({ items: [] });
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

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/wishes`) {
      await fulfillJson({
        hasMore: false,
        nextCursor: null,
        items: [
          {
            capabilities: { canComment: true, canDelete: true, canEdit: true },
            createdAt: TEST_NOW,
            createdBy: ACCOUNT_ID,
            creator: { id: ACCOUNT_ID, displayName: 'Lea' },
            id: WISH_ID,
            spaceId: SPACE_ID,
            status: 'OPEN',
            title: WISH_TITLE,
            updatedAt: TEST_NOW,
            version: 1,
          },
        ],
      });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/plans`) {
      if (options.plansDelayMs) {
        await new Promise((resolve) =>
          setTimeout(resolve, options.plansDelayMs),
        );
      }
      if (options.plansFail) {
        await fulfillJson(
          {
            code: 'E2E_FORCED_FAILURE',
            detail: 'Forced Plan listing failure for the loading/error test.',
            status: 500,
            title: 'Forced failure',
          },
          500,
        );
        return;
      }
      const requestedStatus = new URL(request.url()).searchParams.get('status');
      const items =
        requestedStatus === 'PLANNED'
          ? [
              {
                capabilities: {
                  canComment: true,
                  canDelete: true,
                  canEdit: true,
                },
                createdAt: TEST_NOW,
                createdBy: ACCOUNT_ID,
                creator: { id: ACCOUNT_ID, displayName: 'Ben' },
                description: 'Nice weather, remember the sunscreen.',
                experiencedOn: null,
                id: PLAN_ID,
                placeId: null,
                plannedEnd: null,
                plannedStart: '2026-09-14T14:00:00Z',
                sourceWishId: null,
                spaceId: SPACE_ID,
                status: 'PLANNED',
                title: PLAN_TITLE,
                updatedAt: TEST_NOW,
                version: 1,
              },
            ]
          : [];
      await fulfillJson({ hasMore: false, nextCursor: null, items });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/places`) {
      await fulfillJson({ hasMore: false, nextCursor: null, items: [] });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/plans/${PLAN_ID}`
    ) {
      await fulfillJson({
        capabilities: { canComment: true, canDelete: true, canEdit: true },
        createdAt: TEST_NOW,
        createdBy: ACCOUNT_ID,
        creator: { id: ACCOUNT_ID, displayName: 'Ben' },
        description: 'Nice weather, remember the sunscreen.',
        experiencedOn: null,
        id: PLAN_ID,
        placeId: null,
        plannedEnd: null,
        plannedStart: '2026-09-14T14:00:00Z',
        sourceWishId: null,
        spaceId: SPACE_ID,
        status: 'PLANNED',
        title: PLAN_TITLE,
        updatedAt: TEST_NOW,
        version: 1,
      });
      return;
    }

    await fulfillJson(
      {
        code: 'E2E_UNEXPECTED_REQUEST',
        detail: `planning-reference test does not define ${method} ${pathname}.`,
        status: 500,
        title: 'Unexpected browser test request',
      },
      500,
    );
  });
}

async function signIn(page: Page): Promise<void> {
  await page.goto('/today');
  await page.getByLabel(de.login.email).fill('anna@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
  await expect(page.getByLabel(de.login.email)).toHaveCount(0);
}

test('ArrowLeft/ArrowRight moves focus and selection between the Wünsche and Pläne tabs', async ({
  page,
}) => {
  await installMocks(page);
  await signIn(page);
  await page.goto('/plan');

  const wishesTab = page.getByRole('tab', {
    name: m5s3.overview.segmentWishes,
  });
  const plansTab = page.getByRole('tab', { name: m5s3.overview.segmentPlans });
  await wishesTab.focus();
  await expect(wishesTab).toHaveAttribute('aria-selected', 'true');

  await page.keyboard.press('ArrowRight');
  await expect(plansTab).toHaveAttribute('aria-selected', 'true');
  await expect(plansTab).toBeFocused();
  await expect(page.getByText(PLAN_TITLE)).toBeVisible();

  await page.keyboard.press('ArrowLeft');
  await expect(wishesTab).toHaveAttribute('aria-selected', 'true');
  await expect(wishesTab).toBeFocused();
  await expect(page.getByText(WISH_TITLE)).toBeVisible();
});

test('clicking a Plan card navigates from the Planen overview to the Plan detail page', async ({
  page,
}) => {
  await installMocks(page);
  await signIn(page);
  await page.goto('/plan');

  await page.getByRole('tab', { name: m5s3.overview.segmentPlans }).click();
  await page.getByRole('heading', { name: PLAN_TITLE, level: 2 }).click();

  await expect(page).toHaveURL(new RegExp(`/plan/plans/${PLAN_ID}$`));
  await expect(
    page.getByRole('heading', { name: PLAN_TITLE, level: 1 }),
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: m5s3.common.back }),
  ).toBeVisible();
});

test('shows the loading state while Plans are in flight, then the error state on failure, with a working retry', async ({
  page,
}) => {
  let plansCallCount = 0;
  await installMocks(page, { plansFail: true, plansDelayMs: 2000 });
  // Registered after installMocks, so this handler runs first (Playwright
  // checks the most-recently-registered route handler first) and can count
  // the request before falling back to the mock above for the actual response.
  await page.route('**/api/v1/**', async (route, request) => {
    const pathname = new URL(request.url()).pathname;
    if (
      request.method() === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/plans`
    ) {
      plansCallCount += 1;
    }
    await route.fallback();
  });
  await signIn(page);
  await page.goto('/plan');
  await page.getByRole('tab', { name: m5s3.overview.segmentPlans }).click();

  await expect(page.getByText(de.states.loading.title)).toBeVisible();
  await expect(page.getByRole('button', { name: /erneut/i })).toBeVisible({
    timeout: 10_000,
  });
  expect(plansCallCount).toBeGreaterThan(0);
});

for (const colorScheme of ['light', 'dark'] as const) {
  test(`Plan detail is axe-clean at 390x844 in ${colorScheme} mode`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme });
    await page.addInitScript(() =>
      window.localStorage.setItem('sidebyside.theme', 'system'),
    );
    await page.setViewportSize({ width: 390, height: 844 });
    await installMocks(page);
    await signIn(page);
    await page.goto(`/plan/plans/${PLAN_ID}`);

    await expect(page.locator('html')).toHaveAttribute(
      'data-theme',
      colorScheme,
    );
    await expect(
      page.getByRole('heading', { name: PLAN_TITLE, level: 1 }),
    ).toBeVisible();

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
    expect(result.violations).toEqual([]);
  });
}
