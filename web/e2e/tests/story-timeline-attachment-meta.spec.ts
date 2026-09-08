import { expect, type Page, test } from '@playwright/test';
import de from '../../src/i18n/locales/de';

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const SPACE_ID = '22222222-2222-4222-8222-222222222222';
const PROFILE_ID = '33333333-3333-4333-8333-333333333333';

const LEA = { id: ACCOUNT_ID, displayName: 'Lea Sommer' };
const CAPABILITIES = { canEdit: true, canDelete: true, canComment: true };

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
        account: { displayName: 'Lea Sommer', id: ACCOUNT_ID },
        tokens: {
          accessExpiresAt: new Date(Date.now() + 3600_000).toISOString(),
          accessToken: 'timeline-meta-access-token',
          refreshExpiresAt: new Date(Date.now() + 86400_000).toISOString(),
          refreshToken: 'timeline-meta-refresh-token',
        },
      });
      return;
    }
    if (method === 'GET' && pathname === '/api/v1/auth/me') {
      await fulfillJson({ displayName: 'Lea Sommer', id: ACCOUNT_ID });
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
        createdAt: '2023-06-17T00:00:00Z',
        partners: [LEA],
      });
      return;
    }
    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/profile`) {
      await fulfillJson({
        spaceId: SPACE_ID,
        version: 1,
        relationshipStartedOn: '2023-06-17',
        showRelationshipDuration: true,
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
        createdAt: '2023-06-17T00:00:00Z',
        displayName: 'Lea Sommer',
        id: PROFILE_ID,
        preferences: [],
        profileAttachmentId: null,
        updatedAt: '2023-06-17T00:00:00Z',
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
      pathname === `/api/v1/spaces/${SPACE_ID}/timeline`
    ) {
      await fulfillJson({
        items: [
          {
            kind: 'MEMORY',
            effectiveDate: '2026-08-24',
            memory: {
              id: 'mem-1',
              title: 'Ein Wochenende am Wasser',
              happenedOn: '2026-08-24',
              createdAt: '2026-08-24',
              author: LEA,
              capabilities: CAPABILITIES,
              attachments: [
                {
                  id: 'a1',
                  position: 0,
                  status: 'READY',
                  mediaType: 'IMAGE',
                  mimeType: 'image/jpeg',
                  hasThumbnail: true,
                  width: 800,
                  height: 800,
                  size: 1,
                },
                {
                  id: 'a2',
                  position: 1,
                  status: 'READY',
                  mediaType: 'IMAGE',
                  mimeType: 'image/jpeg',
                  hasThumbnail: true,
                  width: 800,
                  height: 800,
                  size: 1,
                },
              ],
            },
          },
        ],
        hasMore: false,
        nextCursor: null,
      });
      return;
    }
    await fulfillJson({}, 200);
  });
}

async function signIn(page: Page): Promise<void> {
  await page.getByLabel(de.login.email).fill('lea@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
  await expect(page.getByLabel(de.login.email)).toHaveCount(0);
}

/**
 * "2 Fotos" previously rendered bold and in the brand "shared" accent
 * color, making the attachment count look like an emphasized display
 * number rather than quiet secondary metadata next to the date/author
 * (#791 second follow-up). It must now match the muted, regular-weight
 * treatment of the neighboring date and author text.
 */
test('Timeline attachment-count meta ("2 Fotos") matches the surrounding secondary metadata typography', async ({
  page,
}) => {
  await installMocks(page);
  await page.setViewportSize({ width: 1440, height: 1200 });
  await page.goto('/story?tab=timeline');
  await signIn(page);
  await page.goto('/story?tab=timeline');
  await page.waitForSelector('.media-label');

  const [mediaLabelStyle, dateStyle] = await Promise.all([
    page
      .locator('.media-label')
      .first()
      .evaluate((el) => {
        const cs = getComputedStyle(el);
        return {
          color: cs.color,
          fontWeight: cs.fontWeight,
          fontSize: cs.fontSize,
        };
      }),
    page
      .locator('.story-card-footer time')
      .first()
      .evaluate((el) => {
        const cs = getComputedStyle(el);
        return {
          color: cs.color,
          fontWeight: cs.fontWeight,
          fontSize: cs.fontSize,
        };
      }),
  ]);

  expect(mediaLabelStyle).toEqual(dateStyle);
});
