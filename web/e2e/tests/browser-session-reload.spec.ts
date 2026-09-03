import { expect, test, type Page } from '@playwright/test';
import de from '../../src/i18n/locales/de';

const ACCOUNT_ID = '00000000-0000-0000-0000-000000000001';
const PARTNER_ID = '00000000-0000-0000-0000-000000000002';
const SPACE_ID = '00000000-0000-0000-0000-000000000010';
const PROFILE_ID = '00000000-0000-0000-0000-000000000020';
const COLLECTION_ID = '00000000-0000-0000-0000-000000000050';
const ITEM_ID = '00000000-0000-0000-0000-000000000051';
const TEST_NOW = '2026-09-01T10:00:00Z';

async function signIn(page: Page): Promise<void> {
  await page.getByLabel(de.login.email).fill('anna@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
}

test.describe('Browser Session Reload and Deep Route Restoration', () => {
  test('restores deep protected route on real page reload without login flash or session loss', async ({
    page,
  }) => {
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
            accessToken: 'session-access-token',
            refreshExpiresAt: '2026-09-08T10:00:00Z',
            refreshToken: 'session-refresh-token',
          },
        });
        return;
      }

      if (method === 'GET' && pathname === '/api/v1/auth/me') {
        await fulfillJson({
          id: ACCOUNT_ID,
          displayName: 'Anna',
        });
        return;
      }

      if (method === 'POST' && pathname === '/api/v1/auth/refresh') {
        await fulfillJson({
          accessExpiresAt: '2026-09-01T11:00:00Z',
          accessToken: 'session-access-token-refreshed',
          refreshExpiresAt: '2026-09-08T10:00:00Z',
          refreshToken: 'session-refresh-token-refreshed',
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
        pathname.startsWith(`/api/v1/spaces/${SPACE_ID}/profiles/`)
      ) {
        const isPartner = pathname.endsWith(PARTNER_ID);
        await fulfillJson({
          accountId: isPartner ? PARTNER_ID : ACCOUNT_ID,
          createdAt: TEST_NOW,
          displayName: isPartner ? 'Ben' : 'Anna',
          id: isPartner ? '00000000-0000-0000-0000-000000000022' : PROFILE_ID,
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
        await fulfillJson({
          space: {
            spaceId: SPACE_ID,
            partner: {
              id: '00000000-0000-0000-0000-000000000002',
              displayName: 'Ben',
            },
          },
          relationshipDuration: null,
          retrospective: null,
          recentShared: [],
          upcoming: [],
        });
        return;
      }

      if (
        method === 'GET' &&
        pathname ===
          `/api/v1/spaces/${SPACE_ID}/private/collections/${COLLECTION_ID}`
      ) {
        await fulfillJson({
          id: COLLECTION_ID,
          spaceId: SPACE_ID,
          title: 'Summer vacation checklist',
          icon: '🧳',
          version: 1,
          createdAt: TEST_NOW,
          updatedAt: TEST_NOW,
          capabilities: {
            canEdit: true,
            canDelete: true,
          },
          items: [
            {
              id: ITEM_ID,
              collectionId: COLLECTION_ID,
              title: 'Passport and boarding pass',
              completed: false,
              position: 0,
              version: 1,
              createdAt: TEST_NOW,
              updatedAt: TEST_NOW,
            },
          ],
        });
        return;
      }

      if (method === 'POST' && pathname === '/api/v1/auth/sign-out') {
        await fulfillJson({}, 204);
        return;
      }

      await route.fallback();
    });

    // 1. Initial sign-in via UI
    await page.goto('/');
    await signIn(page);

    // 2. Open protected deep route
    const deepPath = `/more/private/collections/${COLLECTION_ID}`;
    await page.goto(deepPath);

    // 3. Confirm protected content is visible
    await expect(
      page.getByRole('heading', { name: 'Summer vacation checklist' }),
    ).toBeVisible();
    await expect(
      page.locator('input.private-checklist-title-input'),
    ).toHaveValue('Passport and boarding pass');

    const currentUrl = page.url();
    expect(currentUrl).toContain(deepPath);

    // 4. Perform actual browser reload
    await page.reload();

    // 5. Verify exact route is preserved
    expect(page.url()).toBe(currentUrl);

    // 6. Verify protected content remains visible after reload
    await expect(
      page.getByRole('heading', { name: 'Summer vacation checklist' }),
    ).toBeVisible();
    await expect(
      page.locator('input.private-checklist-title-input'),
    ).toHaveValue('Passport and boarding pass');

    // 7. Verify login screen was never shown
    await expect(page.getByLabel(de.login.email)).not.toBeVisible();
  });

  test('stays logged out after user sign-out followed by real page reload', async ({
    page,
  }) => {
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
            accessToken: 'session-access-token',
            refreshExpiresAt: '2026-09-08T10:00:00Z',
            refreshToken: 'session-refresh-token',
          },
        });
        return;
      }

      if (method === 'GET' && pathname === '/api/v1/auth/me') {
        await fulfillJson({
          id: ACCOUNT_ID,
          displayName: 'Anna',
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
        pathname.startsWith(`/api/v1/spaces/${SPACE_ID}/profiles/`)
      ) {
        const isPartner = pathname.endsWith(PARTNER_ID);
        await fulfillJson({
          accountId: isPartner ? PARTNER_ID : ACCOUNT_ID,
          createdAt: TEST_NOW,
          displayName: isPartner ? 'Ben' : 'Anna',
          id: isPartner ? '00000000-0000-0000-0000-000000000022' : PROFILE_ID,
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
        await fulfillJson({
          space: {
            spaceId: SPACE_ID,
            partner: {
              id: '00000000-0000-0000-0000-000000000002',
              displayName: 'Ben',
            },
          },
          relationshipDuration: null,
          retrospective: null,
          recentShared: [],
          upcoming: [],
        });
        return;
      }

      if (method === 'POST' && pathname === '/api/v1/auth/sign-out') {
        await fulfillJson({}, 204);
        return;
      }

      await route.fallback();
    });

    // 1. Initial sign-in
    await page.goto('/');
    await signIn(page);

    // 2. Open header profile menu and click logout
    const menuButton = page.locator('summary.header-profile-trigger');
    await menuButton.click();
    const logoutButton = page.getByRole('button', { name: de.header.logout });
    await logoutButton.click();

    // 3. Confirm login screen is visible
    await expect(page.getByLabel(de.login.email)).toBeVisible({
      timeout: 10000,
    });

    // 4. Perform actual browser reload
    await page.reload();

    // 5. Confirm user remains logged out after reload
    await expect(page.getByLabel(de.login.email)).toBeVisible({
      timeout: 10000,
    });
    await expect(
      page.getByRole('heading', { name: 'Summer vacation checklist' }),
    ).not.toBeVisible();
  });
});
