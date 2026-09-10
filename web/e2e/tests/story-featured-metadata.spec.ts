import { expect, type Page, test } from '@playwright/test';
import de from '../../src/i18n/locales/de';

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const SPACE_ID = '22222222-2222-4222-8222-222222222222';
const PROFILE_ID = '33333333-3333-4333-8333-333333333333';
const PARTNER_ID = '44444444-4444-4444-8444-444444444444';
const LONG_AUTHOR_NAME =
  'AlexandraMargaretheVonWinterbergMitAussergewoehnlichLangemProfilnamen';

const AUTHOR = { id: ACCOUNT_ID, displayName: LONG_AUTHOR_NAME };
const PARTNER = { id: PARTNER_ID, displayName: 'Alex Winter' };
const CAPABILITIES = { canEdit: true, canDelete: true, canComment: true };

const FEATURED_ITEM = {
  kind: 'HEART_MOMENT',
  effectiveDate: '2026-09-05',
  heartMoment: {
    id: 'hm-featured',
    text: 'Danke, dass du heute einfach da warst.',
    emotion: 'LOVED',
    happenedOn: '2026-09-05',
    createdAt: '2026-09-05T12:00:00Z',
    author: AUTHOR,
    capabilities: CAPABILITIES,
    attachment: null,
  },
};

async function installApiMocks(page: Page): Promise<string[]> {
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
        account: AUTHOR,
        tokens: {
          accessExpiresAt: new Date(Date.now() + 3600_000).toISOString(),
          accessToken: 'browser-e2e-access-token',
          refreshExpiresAt: new Date(Date.now() + 86400_000).toISOString(),
          refreshToken: 'browser-e2e-refresh-token',
        },
      });
      return;
    }

    if (method === 'GET' && pathname === '/api/v1/auth/me') {
      await fulfillJson(AUTHOR);
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
        partners: [AUTHOR, PARTNER],
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
        displayName: LONG_AUTHOR_NAME,
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
      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard`
    ) {
      await fulfillJson({
        recentShared: [],
        relationshipDuration: null,
        retrospective: null,
        space: { partner: PARTNER, spaceId: SPACE_ID },
        upcoming: [],
      });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/timeline`
    ) {
      await fulfillJson({
        items: [FEATURED_ITEM],
        hasMore: false,
        nextCursor: null,
      });
      return;
    }

    unexpectedRequests.push(`${method} ${pathname}`);
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

  return unexpectedRequests;
}

async function signIn(page: Page): Promise<void> {
  await page.getByLabel(de.login.email).fill('lea@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
  await expect(page.getByLabel(de.login.email)).toHaveCount(0);
}

async function expectMetadataContract(
  page: Page,
  selector: string,
): Promise<void> {
  const metadata = page.locator(selector).first();
  await expect(metadata).toBeVisible();

  const geometry = await metadata.evaluate((node) => {
    const row = node as HTMLElement;
    const date = row.querySelector(':scope > time') as HTMLElement | null;
    const author = row.querySelector(
      ':scope > .momente-author-meta',
    ) as HTMLElement | null;
    if (!date || !author) {
      throw new Error('Expected date and author metadata');
    }

    const dateRect = date.getBoundingClientRect();
    const authorRect = author.getBoundingClientRect();
    const rowRect = row.getBoundingClientRect();
    const authorLabel = author.querySelector('span:last-child') as HTMLElement;

    return {
      justifyContent: getComputedStyle(row).justifyContent,
      rowLeft: rowRect.left,
      rowRight: rowRect.right,
      dateLeft: dateRect.left,
      dateRight: dateRect.right,
      authorLeft: authorRect.left,
      authorRight: authorRect.right,
      rowClientWidth: row.clientWidth,
      rowScrollWidth: row.scrollWidth,
      authorClientWidth: author.clientWidth,
      authorScrollWidth: author.scrollWidth,
      authorLabelClientWidth: authorLabel.clientWidth,
      authorLabelScrollWidth: authorLabel.scrollWidth,
    };
  });

  expect(geometry.justifyContent).toBe('space-between');
  expect(geometry.dateLeft).toBeGreaterThanOrEqual(geometry.rowLeft - 1);
  expect(geometry.authorRight).toBeLessThanOrEqual(geometry.rowRight + 1);
  expect(geometry.authorLeft).toBeGreaterThanOrEqual(geometry.dateRight);
  expect(geometry.rowScrollWidth).toBeLessThanOrEqual(
    geometry.rowClientWidth + 1,
  );
  expect(geometry.authorScrollWidth).toBeLessThanOrEqual(
    geometry.authorClientWidth + 1,
  );
  expect(geometry.authorLabelScrollWidth).toBeLessThanOrEqual(
    geometry.authorLabelClientWidth + 1,
  );
}

async function expectNoHorizontalPageOverflow(page: Page): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
}

test('Featured Moment metadata keeps date left and long author right at Compact and reflow widths', async ({
  page,
}) => {
  const unexpectedRequests = await installApiMocks(page);
  await page.setViewportSize({ width: 390, height: 1400 });
  await page.goto('/story?tab=discover');
  await signIn(page);
  await page.goto('/story?tab=discover');

  await expect(
    page.getByRole('heading', { name: 'Unsere Momente', level: 1 }),
  ).toBeVisible();

  const heroMetadata = page.locator('.momente-hero-meta');
  await expect(heroMetadata).toContainText(LONG_AUTHOR_NAME);
  expect(
    await heroMetadata.locator(':scope > *').evaluateAll((nodes) =>
      nodes.map((node) => node.tagName.toLowerCase()),
    ),
  ).toEqual(['time', 'span']);

  await expectMetadataContract(page, '.momente-hero-meta');
  await expectMetadataContract(page, '.momente-tapestry-meta');
  await expectNoHorizontalPageOverflow(page);

  await page.setViewportSize({ width: 320, height: 1400 });
  await expectMetadataContract(page, '.momente-hero-meta');
  await expectMetadataContract(page, '.momente-tapestry-meta');
  await expectNoHorizontalPageOverflow(page);

  await page.emulateMedia({ colorScheme: 'dark' });
  await expectMetadataContract(page, '.momente-hero-meta');
  await expectMetadataContract(page, '.momente-tapestry-meta');
  await expectNoHorizontalPageOverflow(page);

  expect(unexpectedRequests).toEqual([]);
});
