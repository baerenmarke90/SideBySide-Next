import { expect, test, type Page } from '@playwright/test';
import de from '../../src/i18n/locales/de';
import m5s3 from '../../src/i18n/locales/m5s3';
import m5s5 from '../../src/i18n/locales/m5s5';
import navigation from '../../src/i18n/locales/navigation';

const ACCOUNT_ID = '00000000-0000-0000-0000-000000000001';
const PARTNER_ID = '00000000-0000-0000-0000-000000000002';
const SPACE_ID = '00000000-0000-0000-0000-000000000010';
const PROFILE_ID = '00000000-0000-0000-0000-000000000020';
const PLAN_ID = '00000000-0000-0000-0000-000000000030';
const TEST_NOW = '2026-09-01T10:00:00Z';

async function signIn(page: Page): Promise<void> {
  await page.getByLabel(de.login.email).fill('anna@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
}

test('Today dashboard reflects updated primary context after plan rescheduling without full page reload', async ({
  page,
}) => {
  const unexpectedRequests: string[] = [];
  let dashboardRequestCount = 0;
  let isRescheduled = false;

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
        account: { displayName: 'Anna', id: ACCOUNT_ID },
        tokens: {
          accessExpiresAt: '2026-09-01T11:00:00Z',
          accessToken: 'freshness-access-token',
          refreshExpiresAt: '2026-09-08T10:00:00Z',
          refreshToken: 'freshness-refresh-token',
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
      pathname === `/api/v1/spaces/${SPACE_ID}/activity`
    ) {
      await fulfillJson({
        hasMore: false,
        items: [],
        nextCursor: null,
      });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard`
    ) {
      dashboardRequestCount++;
      if (!isRescheduled) {
        // Initial state: Plan is scheduled later in October
        await fulfillJson({
          space: {
            spaceId: SPACE_ID,
            partner: { id: PARTNER_ID, displayName: 'Ben' },
          },
          relationshipDuration: {
            daysTogether: 250,
            startedOn: '2026-01-01',
          },
          retrospective: null,
          recentShared: [],
          upcoming: [
            {
              id: PLAN_ID,
              type: 'PLAN',
              titleOrText: 'Späterer Herbsturlaub im Oktober',
              scheduledAt: '2026-10-20T10:00:00Z',
              presentationRole: 'context',
            },
          ],
        });
      } else {
        // Updated state after rescheduling: Plan is scheduled earlier in September
        await fulfillJson({
          space: {
            spaceId: SPACE_ID,
            partner: { id: PARTNER_ID, displayName: 'Ben' },
          },
          relationshipDuration: {
            daysTogether: 250,
            startedOn: '2026-01-01',
          },
          retrospective: null,
          recentShared: [],
          upcoming: [
            {
              id: PLAN_ID,
              type: 'PLAN',
              titleOrText: 'Früherer Ausflug im September',
              scheduledAt: '2026-09-05T10:00:00Z',
              presentationRole: 'context',
            },
          ],
        });
      }
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/plans/${PLAN_ID}`
    ) {
      await fulfillJson({
        id: PLAN_ID,
        spaceId: SPACE_ID,
        title: isRescheduled
          ? 'Früherer Ausflug im September'
          : 'Späterer Herbsturlaub im Oktober',
        description: 'Gemeinsame Planung',
        status: 'PLANNED',
        plannedStart: isRescheduled
          ? '2026-09-05T10:00:00Z'
          : '2026-10-20T10:00:00Z',
        plannedEnd: null,
        placeId: null,
        experiencedOn: null,
        version: isRescheduled ? 2 : 1,
        createdAt: TEST_NOW,
        updatedAt: TEST_NOW,
        capabilities: {
          canEdit: true,
          canDelete: true,
        },
      });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/places`) {
      await fulfillJson([]);
      return;
    }

    if (
      method === 'POST' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/plans/${PLAN_ID}/schedule`
    ) {
      isRescheduled = true;
      await fulfillJson({
        id: PLAN_ID,
        spaceId: SPACE_ID,
        title: 'Früherer Ausflug im September',
        description: 'Gemeinsame Planung',
        status: 'PLANNED',
        plannedStart: '2026-09-05T10:00:00Z',
        plannedEnd: null,
        placeId: null,
        experiencedOn: null,
        version: 2,
        createdAt: TEST_NOW,
        updatedAt: TEST_NOW,
        capabilities: {
          canEdit: true,
          canDelete: true,
        },
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

  // Step 1: Open /today and sign in
  await page.goto('/today');
  await signIn(page);

  // Assert initial dashboard renders later upcoming plan as primary context
  await expect(page).toHaveURL(/\/today$/);
  await expect(
    page.getByRole('heading', {
      name: m5s5.dashboard.partner.replace('{{name}}', 'Ben'),
      level: 1,
    }),
  ).toBeVisible();
  await expect(
    page.getByText('Späterer Herbsturlaub im Oktober'),
  ).toBeVisible();
  expect(dashboardRequestCount).toBe(1);

  // Step 2: Navigate to plan details via in-app UI click (NO page.reload())
  await page.locator('a.today-context-link').click();
  await expect(page).toHaveURL(new RegExp(`/plan/plans/${PLAN_ID}$`));
  await expect(
    page.getByRole('heading', {
      name: 'Späterer Herbsturlaub im Oktober',
      level: 1,
    }),
  ).toBeVisible();

  // Reschedule to an earlier date
  const startInput = page.locator('#plan-schedule-start');
  await expect(startInput).toBeVisible();
  await startInput.fill('2026-09-05T10:00');

  // Submit the reschedule form and wait for the response
  const rescheduleButton = page.getByRole('button', {
    name: m5s3.plan.reschedule,
  });
  await rescheduleButton.click();
  await expect(rescheduleButton).toBeEnabled();

  // Step 3: Navigate back to Wir via client-side link (NO page.reload())
  await page.getByRole('link', { name: navigation.today }).click();
  await expect(page).toHaveURL(/\/today$/);

  // Step 4: Verify Dashboard query was automatically refetched (poll until React Query refetch completes)
  await expect.poll(() => dashboardRequestCount).toBeGreaterThanOrEqual(2);

  // Step 5: Verify earlier item is now visible in the primary context slot
  await expect(
    page.getByRole('heading', {
      name: 'Früherer Ausflug im September',
      level: 3,
    }),
  ).toBeVisible();
  await expect(page.getByText('Späterer Herbsturlaub im Oktober')).toHaveCount(
    0,
  );

  // Step 6: Verify no unexpected network requests occurred
  expect(unexpectedRequests).toEqual([]);
});
