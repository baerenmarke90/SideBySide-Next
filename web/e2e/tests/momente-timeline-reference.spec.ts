import fs from 'node:fs';
import path from 'node:path';
import AxeBuilder from '@axe-core/playwright';
import { expect, type Page, test } from '@playwright/test';
import de from '../../src/i18n/locales/de';

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const PARTNER_ID = '99999999-9999-4999-8999-999999999999';
const SPACE_ID = '22222222-2222-4222-8222-222222222222';
const PROFILE_ID = '33333333-3333-4333-8333-333333333333';

const ME = { id: ACCOUNT_ID, displayName: 'Lea Sommer' };
const PARTNER = { id: PARTNER_ID, displayName: 'Alex' };
const CAPABILITIES = { canEdit: true, canDelete: true, canComment: true };

const TINY_PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64',
);

const SCREENSHOT_DIR =
  '/home/philipp/.gemini/antigravity/brain/78749ac7-9133-4ade-9dc8-a205fb78d42f/screenshots';

function getTimelineItems(isOwner: boolean) {
  const items = [];

  // 1. Image-bearing memory (OWNER_ONLY: only visible to owner)
  if (isOwner) {
    items.push({
      kind: 'MEMORY',
      effectiveDate: '2026-05-12T08:30:00Z',
      memory: {
        id: 'mem-canal',
        title: 'Frühstück am Kanal',
        happenedOn: '2026-05-12',
        createdAt: '2026-05-12T08:30:00Z',
        author: ME,
        capabilities: CAPABILITIES,
        visibility: 'OWNER_ONLY',
        attachments: [
          {
            id: 'att-canal-1',
            position: 0,
            status: 'READY',
            mediaType: 'IMAGE',
            mimeType: 'image/jpeg',
            hasThumbnail: true,
            width: 800,
            height: 800,
            size: 1024,
          },
        ],
      },
    });
  }

  // 2. Image-bearing shared memory
  items.push({
    kind: 'MEMORY',
    effectiveDate: '2026-04-03T10:00:00Z',
    memory: {
      id: 'mem-coffee',
      title: 'Unser erster Kaffee im neuen Zuhause',
      happenedOn: '2026-04-03',
      createdAt: '2026-04-03T10:00:00Z',
      author: ME,
      capabilities: CAPABILITIES,
      visibility: 'SHARED',
      attachments: [
        {
          id: 'att-coffee-1',
          position: 0,
          status: 'READY',
          mediaType: 'IMAGE',
          mimeType: 'image/jpeg',
          hasThumbnail: true,
          width: 800,
          height: 800,
          size: 1024,
        },
      ],
    },
  });

  // 3. No-image memory
  items.push({
    kind: 'MEMORY',
    effectiveDate: '2026-03-28T14:00:00Z',
    memory: {
      id: 'mem-hike',
      title: 'Gemeinsame Wanderung',
      happenedOn: '2026-03-28',
      createdAt: '2026-03-28T14:00:00Z',
      author: ME,
      capabilities: CAPABILITIES,
      visibility: 'SHARED',
      attachments: [],
    },
  });

  // 4. Milestone
  items.push({
    kind: 'MILESTONE',
    effectiveDate: '2026-02-14T00:00:00Z',
    milestone: {
      id: 'ms-2years',
      title: '2 Jahre',
      happenedOn: '2026-02-14',
      createdAt: '2026-02-14T00:00:00Z',
      author: ME,
      capabilities: CAPABILITIES,
    },
  });

  // 5. Heart Moment
  items.push({
    kind: 'HEART_MOMENT',
    effectiveDate: '2026-01-20T19:00:00Z',
    heartMoment: {
      id: 'hm-love',
      text: 'Kurz an dich gedacht.',
      emotion: 'LOVED',
      happenedOn: '2026-01-20',
      createdAt: '2026-01-20T19:00:00Z',
      author: ME,
      capabilities: CAPABILITIES,
      attachment: null,
    },
  });

  return items;
}

type MockOptions = {
  asPartner?: boolean;
};

async function installMocks(
  page: Page,
  options: MockOptions = {},
): Promise<void> {
  const currentUserId = options.asPartner ? PARTNER_ID : ACCOUNT_ID;
  const currentUserName = options.asPartner ? 'Alex' : 'Lea Sommer';

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
        account: { displayName: currentUserName, id: currentUserId },
        tokens: {
          accessExpiresAt: new Date(Date.now() + 3_600_000).toISOString(),
          accessToken: 'timeline-ref-access-token',
          refreshExpiresAt: new Date(Date.now() + 86_400_000).toISOString(),
          refreshToken: 'timeline-ref-refresh-token',
        },
      });
      return;
    }

    if (method === 'GET' && pathname === '/api/v1/auth/me') {
      await fulfillJson({ displayName: currentUserName, id: currentUserId });
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
        partners: [ME, PARTNER],
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
      pathname === `/api/v1/spaces/${SPACE_ID}/profiles/${currentUserId}`
    ) {
      await fulfillJson({
        accountId: currentUserId,
        createdAt: '2023-06-17T00:00:00Z',
        displayName: currentUserName,
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

    // Attachment read access & file streaming
    if (
      method === 'POST' &&
      pathname.includes('/attachments/') &&
      pathname.endsWith('/read-access')
    ) {
      const match = pathname.match(/\/attachments\/([^/]+)\/read-access/);
      const attId = match ? match[1] : 'att';
      await fulfillJson({
        method: 'DIRECT',
        url: `/api/v1/spaces/${SPACE_ID}/attachments/${attId}/file`,
        expiresAt: new Date(Date.now() + 3600_000).toISOString(),
      });
      return;
    }

    if (
      method === 'GET' &&
      pathname.includes('/attachments/') &&
      (pathname.endsWith('/file') || pathname.endsWith('/thumbnail'))
    ) {
      await route.fulfill({
        status: 200,
        contentType: 'image/png',
        body: TINY_PNG,
      });
      return;
    }

    // Timeline endpoint
    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/timeline`
    ) {
      const url = new URL(request.url());
      const typeParam =
        url.searchParams.get('type') || url.searchParams.get('kind');
      let items = getTimelineItems(!options.asPartner);
      if (typeParam) {
        items = items.filter((item) => item.kind === typeParam);
      }
      await fulfillJson({
        items,
        hasMore: false,
        nextCursor: null,
      });
      return;
    }

    // Memory detail
    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/memories/mem-canal`
    ) {
      await fulfillJson({
        id: 'mem-canal',
        spaceId: SPACE_ID,
        title: 'Frühstück am Kanal',
        body: 'Ein wunderbarer Morgen am Wasser.',
        happenedOn: '2026-05-12',
        author: ME,
        authorId: ACCOUNT_ID,
        attachments: [],
        capabilities: CAPABILITIES,
        createdAt: '2026-05-12T08:30:00Z',
        updatedAt: '2026-05-12T08:30:00Z',
        version: 1,
      });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/memories/mem-canal/comments`
    ) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    // Chapters list endpoint
    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/chapters`
    ) {
      await fulfillJson({
        items: [],
        hasMore: false,
        nextCursor: null,
      });
      return;
    }

    await fulfillJson({}, 200);
  });
}

async function signIn(page: Page, email = 'lea@example.org'): Promise<void> {
  await page.goto('/story?tab=timeline');
  await page.getByLabel(de.login.email).fill(email);
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
  await expect(page.getByLabel(de.login.email)).toHaveCount(0);
}

test.describe('Momente > Zeitleiste Product Reference (#860)', () => {
  test('renders 390x844 reference layout, spine, markers, cards, and captures screenshots', async ({
    page,
  }) => {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

    await page.setViewportSize({ width: 390, height: 844 });
    await installMocks(page);
    await signIn(page);
    await page.goto('/story?tab=timeline');
    await page.waitForSelector('.story-timeline');

    // 1. Editorial Header
    await expect(
      page.getByRole('heading', { name: 'Momente', level: 1 }),
    ).toBeVisible();
    await expect(page.getByText(de.story.timelineIntro)).toBeVisible();

    // 2. Filter chips
    const filterNav = page.locator('.momente-filter-chips');
    await expect(filterNav).toBeVisible();
    await expect(filterNav.getByText('Alle')).toBeVisible();
    await expect(filterNav.getByText('Erinnerungen')).toBeVisible();
    await expect(filterNav.getByText('Herzmomente')).toBeVisible();
    await expect(filterNav.getByText('Meilensteine')).toBeVisible();
    await expect(filterNav.getByText('Kapitel')).toBeVisible();

    // 3. Continuous spine & markers
    const markers = page.locator('.story-timeline-marker');
    await expect(markers).toHaveCount(5);

    // Mixed markers: some berry, some teal
    await expect(
      page.locator('.story-timeline-marker.marker-berry'),
    ).toHaveCount(3);
    await expect(
      page.locator('.story-timeline-marker.marker-teal'),
    ).toHaveCount(2);

    // 4. Two-column cards
    const cards = page.locator('.story-card-reference');
    await expect(cards).toHaveCount(5);

    // 5. Memory card with semantic kind chip
    const firstCard = page.locator('.story-card-reference').first();
    await expect(firstCard.getByText('Frühstück am Kanal')).toBeVisible();
    await expect(firstCard.getByText('Erinnerung')).toBeVisible();

    // 6. Screenshot 1: 390 Light
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '01-momente-timeline-390-light.png'),
      fullPage: true,
    });

    // 7. Screenshot 5: Image-bearing Memory card close-up
    await firstCard.screenshot({
      path: path.join(SCREENSHOT_DIR, '05-momente-timeline-image-memory.png'),
    });

    // 8. Screenshot 6: No-image Memory card close-up (with kind fallback icon)
    const noImageCard = page
      .locator('.story-card-reference')
      .filter({ hasText: 'Gemeinsame Wanderung' });
    await expect(noImageCard).toBeVisible();
    await expect(
      noImageCard.locator('.story-card-thumb-fallback'),
    ).toBeVisible();
    await noImageCard.screenshot({
      path: path.join(
        SCREENSHOT_DIR,
        '06-momente-timeline-no-image-memory.png',
      ),
    });

    // 9. Screenshot 7: Mixed timeline showing spine & markers
    await page.locator('.story-timeline').screenshot({
      path: path.join(SCREENSHOT_DIR, '07-momente-timeline-mixed-markers.png'),
    });

    // 10. Screenshot 9: Legitimate owner view (confirming no fake OWNER_ONLY items)
    await firstCard.screenshot({
      path: path.join(SCREENSHOT_DIR, '09-momente-timeline-owner-only.png'),
    });
  });

  test('dark mode at 390x844 captures 02-momente-timeline-390-dark.png', async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.addInitScript(() =>
      window.localStorage.setItem('sidebyside.theme', 'system'),
    );
    await page.setViewportSize({ width: 390, height: 844 });
    await installMocks(page);
    await signIn(page);
    await page.goto('/story?tab=timeline');
    await page.waitForSelector('.story-timeline');

    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '02-momente-timeline-390-dark.png'),
      fullPage: true,
    });
  });

  test('320px reflow produces no horizontal overflow and captures 03-momente-timeline-320-reflow.png', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 320, height: 640 });
    await installMocks(page);
    await signIn(page);
    await page.goto('/story?tab=timeline');
    await page.waitForSelector('.story-timeline');

    const hasHorizontalOverflow = await page.evaluate(() => {
      return (
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth
      );
    });
    expect(hasHorizontalOverflow).toBe(false);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '03-momente-timeline-320-reflow.png'),
      fullPage: true,
    });
  });

  test('1440 Expanded desktop view captures 04-momente-timeline-1440-expanded.png', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await installMocks(page);
    await signIn(page);
    await page.goto('/story?tab=timeline');
    await page.waitForSelector('.story-timeline');

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '04-momente-timeline-1440-expanded.png'),
      fullPage: true,
    });
  });

  test('Filter chips filter items and capture 08-momente-timeline-filter-active.png', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await installMocks(page);
    await signIn(page);
    await page.goto('/story?tab=timeline');
    await page.waitForSelector('.story-timeline');

    // Click "Erinnerungen" filter chip
    await page
      .locator('.momente-filter-chip', { hasText: 'Erinnerungen' })
      .click();

    // Verify only memories are shown (3 memories: 2 image + 1 no-image)
    const cards = page.locator('.story-card-reference');
    await expect(cards).toHaveCount(3);
    await expect(page.getByText('Frühstück am Kanal')).toBeVisible();
    await expect(
      page.getByText('Unser erster Kaffee im neuen Zuhause'),
    ).toBeVisible();
    await expect(page.getByText('Gemeinsame Wanderung')).toBeVisible();
    await expect(page.getByText('2 Jahre')).toHaveCount(0);
    await expect(page.getByText('Kurz an dich gedacht.')).toHaveCount(0);

    // Active pill state screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '08-momente-timeline-filter-active.png'),
      fullPage: true,
    });

    // Click "Herzmomente"
    await page
      .locator('.momente-filter-chip', { hasText: 'Herzmomente' })
      .click();
    await expect(page.locator('.story-card-reference')).toHaveCount(1);
    await expect(page.getByText('Kurz an dich gedacht.')).toBeVisible();

    // Click "Meilensteine"
    await page
      .locator('.momente-filter-chip', { hasText: 'Meilensteine' })
      .click();
    await expect(page.locator('.story-card-reference')).toHaveCount(1);
    await expect(page.getByText('2 Jahre')).toBeVisible();

    // Reset to "Alle"
    await page.locator('.momente-filter-chip', { hasText: 'Alle' }).click();
    await expect(page.locator('.story-card-reference')).toHaveCount(5);
  });

  test('Kapitel chip acts as explicit navigation affordance to /story/chapters', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await installMocks(page);
    await signIn(page);
    await page.goto('/story?tab=timeline');
    await page.waitForSelector('.story-timeline');

    const kapitelLink = page.locator('.momente-filter-chip', {
      hasText: 'Kapitel',
    });
    await expect(kapitelLink).toHaveAttribute('href', '/story/chapters');
    await kapitelLink.click();
    await expect(page).toHaveURL(/\/story\/chapters$/);
  });

  test('clicking a card navigates to detail page and captures 10-momente-timeline-detail-nav.png', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await installMocks(page);
    await signIn(page);
    await page.goto('/story?tab=timeline');
    await page.waitForSelector('.story-timeline');

    // Click memory card
    await page.getByRole('heading', { name: 'Frühstück am Kanal' }).click();

    await expect(page).toHaveURL(/\/story\/memories\/mem-canal$/);
    await expect(
      page.getByRole('heading', { name: 'Frühstück am Kanal', level: 1 }),
    ).toBeVisible();

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '10-momente-timeline-detail-nav.png'),
      fullPage: true,
    });
  });

  test('Privacy negative test: partner does NOT see OWNER_ONLY memory', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await installMocks(page, { asPartner: true });
    await signIn(page, 'alex@example.org');
    await page.goto('/story?tab=timeline');
    await page.waitForSelector('.story-timeline');

    // Owner-only item must not exist for partner
    await expect(page.getByText('Frühstück am Kanal')).toHaveCount(0);
    await expect(page.getByText(de.story.visibilityPrivate)).toHaveCount(0);

    // Shared items must exist (4 items)
    await expect(page.locator('.story-card-reference')).toHaveCount(4);
    await expect(
      page.getByText('Unser erster Kaffee im neuen Zuhause'),
    ).toBeVisible();
  });

  test('Entdecken view remains visually and structurally unchanged', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await installMocks(page);
    await signIn(page);
    await page.goto('/story?tab=discover');
    await page.waitForSelector('.momente-discover-page');

    // Discover view has the standard heading and intro (not the timeline editorial text)
    await expect(page.getByText(de.story.title)).toBeVisible();
    await expect(page.getByText(de.story.intro)).toBeVisible();
    // Timeline filter chips must NOT be present on discover
    await expect(page.locator('.momente-filter-chips')).toHaveCount(0);
  });

  for (const colorScheme of ['light', 'dark'] as const) {
    test(`Timeline is axe-clean at 390x844 in ${colorScheme} mode`, async ({
      page,
    }) => {
      await page.emulateMedia({ colorScheme });
      await page.addInitScript(() =>
        window.localStorage.setItem('sidebyside.theme', 'system'),
      );
      await page.setViewportSize({ width: 390, height: 844 });
      await installMocks(page);
      await signIn(page);
      await page.goto('/story?tab=timeline');
      await page.waitForSelector('.story-timeline');

      await expect(page.locator('html')).toHaveAttribute(
        'data-theme',
        colorScheme,
      );

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
});
