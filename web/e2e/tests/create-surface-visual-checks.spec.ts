import { expect, test, type Page } from '@playwright/test';
import de from '../../src/i18n/locales/de';
import storyProducts from '../../src/i18n/locales/storyProducts';

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const SPACE_ID = '22222222-2222-4222-8222-222222222222';
const PROFILE_ID = '33333333-3333-4333-8333-333333333333';
const MEMORY_ID = '44444444-4444-4444-8444-444444444444';
const TEST_NOW = '2026-09-01T10:00:00Z';
const MEMORY_TITLE = 'Ein ruhiger Sonntagmorgen';
const MEMORY_BODY =
  'Wir haben lange geschlafen und dann gemeinsam Pfannkuchen gemacht.';

// Covers the initials the drop cap must stay visually controlled for: a
// narrow letter (S), and the widest common German-copy letters (W, M) plus
// one more (A) — the width-consistency regression the real drop-cap element
// exists to fix.
const DROP_CAP_CASES = [
  {
    id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    title: 'S wie Anfang',
    body: 'Samstagmorgen war der Himmel klar und wir haben lange gefrühstückt, bevor wir losgezogen sind.',
  },
  {
    id: MEMORY_ID,
    title: MEMORY_TITLE,
    body: MEMORY_BODY,
  },
  {
    id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    title: 'A wie Anfang',
    body: 'Am Abend saßen wir noch lange draußen und haben über die letzten Monate gesprochen.',
  },
  {
    id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    title: 'M wie Anfang',
    body: 'Mitten in der Nacht sind wir aufgewacht, weil es draußen so heftig gewittert hat.',
  },
] as const;

function localToday(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
}

/**
 * A focused mock harness for the create-surface visual regression checks:
 * the shared-visibility heart glyph centering on Memory Create, the local
 * "today" date default on HeartMoment/Milestone Create, and the Memory
 * Detail drop cap.
 */
async function installApiMocks(page: Page): Promise<void> {
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
          accessExpiresAt: new Date(Date.now() + 3600_000).toISOString(),
          accessToken: 'browser-e2e-access-token',
          refreshExpiresAt: new Date(Date.now() + 86400_000).toISOString(),
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

    for (const memoryCase of DROP_CAP_CASES) {
      if (
        method === 'GET' &&
        pathname === `/api/v1/spaces/${SPACE_ID}/memories/${memoryCase.id}`
      ) {
        await fulfillJson({
          attachments: [],
          author: { accountId: ACCOUNT_ID, displayName: 'Anna' },
          authorId: ACCOUNT_ID,
          body: memoryCase.body,
          capabilities: { canEdit: true, canDelete: true },
          createdAt: TEST_NOW,
          happenedOn: TEST_NOW,
          id: memoryCase.id,
          spaceId: SPACE_ID,
          title: memoryCase.title,
          updatedAt: TEST_NOW,
          version: 1,
        });
        return;
      }

      if (
        method === 'GET' &&
        pathname ===
          `/api/v1/spaces/${SPACE_ID}/memories/${memoryCase.id}/comments`
      ) {
        await fulfillJson({ hasMore: false, items: [], nextCursor: null });
        return;
      }
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

async function expectSharingHeartCentered(page: Page): Promise<void> {
  const circle = page.locator('.immersive-sharing-note .sharing-icon');
  await expect(circle).toBeVisible();
  const svg = circle.locator('svg');
  const circleBox = await circle.boundingBox();
  const svgBox = await svg.boundingBox();
  if (!circleBox || !svgBox) throw new Error('Sharing icon did not render.');

  const circleCenterX = circleBox.x + circleBox.width / 2;
  const svgCenterX = svgBox.x + svgBox.width / 2;
  const circleCenterY = circleBox.y + circleBox.height / 2;
  const svgCenterY = svgBox.y + svgBox.height / 2;

  // A generous 1.5px tolerance absorbs sub-pixel layout rounding without
  // masking a real regression back to left/top-aligned content (which is
  // off by several pixels in a 32px circle holding a 16px glyph).
  expect(Math.abs(circleCenterX - svgCenterX)).toBeLessThanOrEqual(1.5);
  expect(Math.abs(circleCenterY - svgCenterY)).toBeLessThanOrEqual(1.5);
}

for (const colorScheme of ['light', 'dark'] as const) {
  test(`Memory Create centers the shared-visibility heart glyph in its circle (${colorScheme})`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme });
    await installApiMocks(page);
    await page.goto('/today');
    await signIn(page);

    await page.goto('/story/memories/new');
    await expect(
      page.getByRole('heading', { name: de.memory.heading }),
    ).toBeVisible();

    await expectSharingHeartCentered(page);

    await page.setViewportSize({ width: 390, height: 844 });
    await expectSharingHeartCentered(page);
    await expectNoHorizontalOverflow(page);
  });
}

test('HeartMoment Create defaults the date to local today and stays typeable', async ({
  page,
}) => {
  await installApiMocks(page);
  await page.goto('/today');
  await signIn(page);

  await page.goto('/story/heart-moments/new');
  const dateInput = page.getByLabel(
    storyProducts.heartMomentProduct.happenedOnLabel,
    { exact: true },
  );
  await expect(dateInput).toHaveValue(localToday());

  await dateInput.fill('2025-12-24');
  await expect(dateInput).toHaveValue('2025-12-24');
});

test('Milestone Create defaults the date to local today and stays typeable', async ({
  page,
}) => {
  await installApiMocks(page);
  await page.goto('/today');
  await signIn(page);

  await page.goto('/story/milestones/new');
  const dateInput = page.getByLabel(
    storyProducts.milestoneProduct.happenedOnLabel,
    { exact: true },
  );
  await expect(dateInput).toHaveValue(localToday());

  await dateInput.fill('2025-12-24');
  await expect(dateInput).toHaveValue('2025-12-24');
});

for (const colorScheme of ['light', 'dark'] as const) {
  test(`Memory Detail keeps an inline, enlarged drop cap on the body paragraph (${colorScheme})`, async ({
    page,
  }, testInfo) => {
    await page.emulateMedia({ colorScheme });
    await installApiMocks(page);
    await page.goto('/today');
    await signIn(page);

    await page.goto(`/story/memories/${MEMORY_ID}`);
    await expect(
      page.getByRole('heading', { name: MEMORY_TITLE }),
    ).toBeVisible();

    const body = page.locator('.memory-detail-body');
    const letter = body.locator('.drop-cap-letter');
    await expect(body).toBeVisible();
    await expect(letter).toBeVisible();
    await expect(letter).toHaveText('W');
    // The rest of the paragraph's real text must be unaffected — the split
    // is purely visual, not a rewording or duplication of the content.
    await expect(body).toHaveText(MEMORY_BODY);

    const [bodyFontSize, letterStyle] = await Promise.all([
      body.evaluate((el) => Number.parseFloat(getComputedStyle(el).fontSize)),
      letter.evaluate((el) => {
        const style = getComputedStyle(el);
        return {
          float: style.float,
          display: style.display,
          fontSize: Number.parseFloat(style.fontSize),
        };
      }),
    ]);
    // Deliberately not a classic floated drop cap: it stays part of the
    // normal inline text flow (no reserved column, no text wrapping around
    // it) so the word it starts always reads as one unit.
    expect(letterStyle.float).toBe('none');
    expect(letterStyle.display).toBe('inline');
    expect(letterStyle.fontSize).toBeGreaterThan(bodyFontSize * 1.2);
    expect(letterStyle.fontSize).toBeLessThan(bodyFontSize * 2);

    await page.screenshot({
      path: testInfo.outputPath(`memory-detail-drop-cap-${colorScheme}.png`),
    });

    await page.setViewportSize({ width: 390, height: 844 });
    await expectNoHorizontalOverflow(page);

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.locator('html').evaluate((element) => {
      element.style.zoom = '2';
    });
    await expectNoHorizontalOverflow(page);
  });
}

/**
 * Measures the drop-cap letter's box and the immediately following text's
 * position for one memory, at whatever viewport is currently set.
 */
async function measureDropCapGap(
  page: Page,
  memoryCase: (typeof DROP_CAP_CASES)[number],
): Promise<{ letterBox: { x: number; width: number }; restX: number }> {
  await page.goto(`/story/memories/${memoryCase.id}`);
  await expect(
    page.getByRole('heading', { name: memoryCase.title }),
  ).toBeVisible();

  const letter = page.locator('.drop-cap-letter');
  await expect(letter).toHaveText(memoryCase.body[0]);

  const [letterBox, restRect] = await Promise.all([
    letter.boundingBox(),
    page.locator('.memory-detail-body').evaluate((el) => {
      // The rest of the text is a plain text node right after the letter
      // span; measure its first character via a Range so we can compare
      // its left edge against the drop cap's right edge.
      const range = document.createRange();
      const textNode = Array.from(el.childNodes).find(
        (node) => node.nodeType === Node.TEXT_NODE,
      );
      if (!textNode) return null;
      range.setStart(textNode, 0);
      range.setEnd(textNode, 1);
      const rect = range.getBoundingClientRect();
      return { x: rect.x };
    }),
  ]);
  if (!letterBox || !restRect) {
    throw new Error(
      `Drop cap or body text did not render for ${memoryCase.title}.`,
    );
  }
  return { letterBox, restX: restRect.x };
}

// Desktop and mobile deliberately share the same inline drop-cap logic (see
// MemoryProductPage.css) — only the font-size scales between them — so one
// parametrized check covers both: the letter must stay flush against the
// rest of its word ("Mitten", not "M itten") at every breakpoint.
for (const viewport of [
  { name: 'desktop 1440px', width: 1440, height: 900 },
  { name: 'desktop 1920px', width: 1920, height: 1080 },
  { name: 'mobile 390px', width: 390, height: 844 },
] as const) {
  test(`Memory Detail drop cap stays flush against the rest of its word for S/W/A/M initials (${viewport.name})`, async ({
    page,
  }) => {
    await installApiMocks(page);
    await page.goto('/today');
    await signIn(page);
    await page.setViewportSize(viewport);

    for (const memoryCase of DROP_CAP_CASES) {
      const { letterBox, restX } = await measureDropCapGap(page, memoryCase);
      // The following text must start at or after the drop cap's right
      // edge (never underneath/overlapping it), and the gap itself must
      // read as normal inline text spacing, not the initial standing apart
      // from the rest of its own word as a separate character.
      const gap = restX - (letterBox.x + letterBox.width);
      expect(gap).toBeGreaterThanOrEqual(-1);
      expect(gap).toBeLessThanOrEqual(3);
      await expectNoHorizontalOverflow(page);
    }
  });
}
