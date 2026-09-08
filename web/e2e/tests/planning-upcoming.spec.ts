import { expect, test, type Page } from '@playwright/test';
import de from '../../src/i18n/locales/de';
import m5s3 from '../../src/i18n/locales/m5s3';

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const SPACE_ID = '22222222-2222-4222-8222-222222222222';
const PROFILE_ID = '33333333-3333-4333-8333-333333333333';
const EARLY_PLAN_ID = '44444444-4444-4444-8444-444444444444';
const LATE_PLAN_ID = '55555555-5555-4555-8555-555555555555';
const IDEA_PLAN_ID = '66666666-6666-4666-8666-666666666666';
const COMPLETED_PLAN_ID = '77777777-7777-4777-8777-777777777777';
const WISH_ID = '88888888-8888-4888-8888-888888888888';

const EARLY_TITLE = 'Autumn hike';
const LATE_TITLE = 'Concert in October';
const IDEA_TITLE = 'Try a new recipe';
const COMPLETED_TITLE = 'Day trip we already took';

function localFutureIso(days: number): string {
  const value = new Date();
  value.setDate(value.getDate() + days);
  value.setHours(18, 0, 0, 0);
  return value.toISOString();
}

const EARLY_DATE = localFutureIso(10);
const LATE_DATE = localFutureIso(17);
const TEST_NOW = new Date().toISOString();

function planDetail({
  id,
  title,
  status,
  plannedStart,
  experiencedOn = null,
  sourceWishId = null,
}: {
  id: string;
  title: string;
  status: 'IDEA' | 'PLANNED' | 'COMPLETED';
  plannedStart: string | null;
  experiencedOn?: string | null;
  sourceWishId?: string | null;
}) {
  return {
    capabilities: { canComment: true, canDelete: true, canEdit: true },
    createdAt: TEST_NOW,
    createdBy: ACCOUNT_ID,
    creator: { accountId: ACCOUNT_ID, displayName: 'Anna' },
    description: null,
    experiencedOn,
    id,
    placeId: null,
    plannedEnd: null,
    plannedStart,
    sourceWishId,
    spaceId: SPACE_ID,
    status,
    title,
    updatedAt: TEST_NOW,
    version: 1,
  };
}

const earlyPlan = planDetail({
  id: EARLY_PLAN_ID,
  title: EARLY_TITLE,
  status: 'PLANNED',
  plannedStart: EARLY_DATE,
  sourceWishId: WISH_ID,
});
const latePlan = planDetail({
  id: LATE_PLAN_ID,
  title: LATE_TITLE,
  status: 'PLANNED',
  plannedStart: LATE_DATE,
});
const ideaPlan = planDetail({
  id: IDEA_PLAN_ID,
  title: IDEA_TITLE,
  status: 'IDEA',
  plannedStart: null,
});
const completedPlan = planDetail({
  id: COMPLETED_PLAN_ID,
  title: COMPLETED_TITLE,
  status: 'COMPLETED',
  plannedStart: LATE_DATE,
  experiencedOn: '2026-07-26',
});

async function installPlanningMocks(
  page: Page,
  options: { empty?: boolean } = {},
): Promise<void> {
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());
    const pathname = url.pathname;

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

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/activity`) {
      await fulfillJson({ items: [], nextCursor: null });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard`
    ) {
      const upcoming = options.empty
        ? []
        : [
            {
              createdAt: TEST_NOW,
              id: EARLY_PLAN_ID,
              occurredOn: null,
              scheduledAt: EARLY_DATE,
              titleOrText: EARLY_TITLE,
              type: 'PLAN',
            },
            {
              createdAt: TEST_NOW,
              id: LATE_PLAN_ID,
              occurredOn: null,
              scheduledAt: LATE_DATE,
              titleOrText: LATE_TITLE,
              type: 'PLAN',
            },
          ];
      await fulfillJson({
        keepsake: null,
        recentShared: [],
        relationshipDuration: null,
        retrospective: null,
        space: { partner: null, spaceId: SPACE_ID },
        thinkingOfYouAvailableAt: null,
        upcoming,
      });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/wishes`) {
      await fulfillJson({
        hasMore: false,
        items: options.empty
          ? []
          : [
              {
                capabilities: {
                  canComment: true,
                  canDelete: true,
                  canEdit: true,
                },
                createdAt: TEST_NOW,
                createdBy: ACCOUNT_ID,
                creator: { accountId: ACCOUNT_ID, displayName: 'Anna' },
                id: WISH_ID,
                spaceId: SPACE_ID,
                status: 'PLANNED',
                title: EARLY_TITLE,
                updatedAt: TEST_NOW,
                version: 2,
              },
            ],
        nextCursor: null,
      });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/plans`) {
      const requestedStatus = url.searchParams.get('status');
      let items: unknown[] = [];
      if (!options.empty && requestedStatus === 'PLANNED') {
        // Deliberately not chronological, and includes a defensive rogue
        // completed row so the client selector proves the section contract.
        items = [latePlan, completedPlan, earlyPlan];
      } else if (!options.empty && requestedStatus === 'IDEA') {
        items = [ideaPlan];
      }
      await fulfillJson({ hasMore: false, items, nextCursor: null });
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

test('Bald & Geplant contains only dated upcoming Plans in Today order and shows Wish provenance', async ({
  page,
}) => {
  await installPlanningMocks(page);
  await page.goto('/today');
  await signIn(page);
  await page.goto('/plan');

  const soon = page.locator('.future-map-stop-soon');
  const soonTitles = soon.locator('.planning-card h3');
  await expect(soonTitles).toHaveText([EARLY_TITLE, LATE_TITLE]);
  await expect(soon.getByText(IDEA_TITLE)).toHaveCount(0);
  await expect(soon.getByText(COMPLETED_TITLE)).toHaveCount(0);

  const shortDate = (value: string) =>
    new Intl.DateTimeFormat('de-DE', {
      day: 'numeric',
      month: 'short',
    }).format(new Date(value));
  const meta = soon.locator('.planning-meta');
  await expect(meta).toHaveCount(2);
  await expect(meta.nth(0)).toContainText(shortDate(EARLY_DATE));
  await expect(meta.nth(1)).toContainText(shortDate(LATE_DATE));
  await expect(meta.nth(0)).toContainText(m5s3.wish.status.PLANNED);

  const someday = page.locator('.future-map-stop-someday');
  await expect(
    someday.getByRole('heading', { name: IDEA_TITLE, level: 3 }),
  ).toBeVisible();
  await expect(
    someday.getByRole('heading', { name: EARLY_TITLE, level: 3 }),
  ).toBeVisible();
  await expect(someday.getByText(m5s3.wish.status.PLANNED)).toBeVisible();

  expect(
    await soon.locator('.future-map-marker').evaluate((element) =>
      (element as HTMLElement).style.getPropertyValue('background'),
    ),
  ).toBe('var(--color-brand)');

  await page.goto('/today');
  const todayTitles = page.locator(
    '.today-planning-agenda .today-agenda-title',
  );
  await expect(todayTitles).toHaveText([EARLY_TITLE, LATE_TITLE]);
});

test('planning sections keep their relationship-native empty states', async ({
  page,
}) => {
  await installPlanningMocks(page, { empty: true });
  await page.goto('/today');
  await signIn(page);
  await page.goto('/plan');

  await expect(
    page.locator('.future-map-stop-soon').getByText(m5s3.overview.soonEmpty),
  ).toBeVisible();
  await expect(
    page
      .locator('.future-map-stop-someday')
      .getByText(m5s3.overview.somedayEmpty),
  ).toBeVisible();
});
