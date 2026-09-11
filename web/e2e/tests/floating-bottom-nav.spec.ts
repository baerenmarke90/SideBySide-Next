import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import de from '../../src/i18n/locales/de';
import navigation from '../../src/i18n/locales/navigation';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const SPACE_ID = '22222222-2222-4222-8222-222222222222';
const PROFILE_ID = '33333333-3333-4333-8333-333333333333';
const TEST_NOW = '2026-09-01T10:00:00Z';

const EVIDENCE_DIR = path.resolve(
  __dirname,
  '../../../docs/design/eimir/screenshots/882-floating-nav',
);

async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(
    dimensions.clientWidth + 1,
  );
}

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
          accessToken: 'floating-nav-access-token',
          refreshExpiresAt: new Date(Date.now() + 86400_000).toISOString(),
          refreshToken: 'floating-nav-refresh-token',
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

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/story/timeline`
    ) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
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

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/chapters`
    ) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/collections`
    ) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/related-people`
    ) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    if (
      method === 'GET' &&
      pathname === `/api/v1/spaces/${SPACE_ID}/important-dates`
    ) {
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

test.describe('Floating Bottom Navigation (#882)', () => {
  test.beforeAll(() => {
    if (!fs.existsSync(EVIDENCE_DIR)) {
      fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
    }
  });

  test('shell composition: exactly four destinations + centered Quick Create action in one floating shell', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await installApiMocks(page);
    await page.goto('/login');
    await signIn(page);
    await page.waitForURL('**/today');

    const floatingShell = page.locator('.mobile-bottom-shell');
    await expect(floatingShell).toBeVisible();

    // 1. Navigation landmark has exactly four destination links
    const nav = floatingShell.locator('.mobile-bottom-nav');
    await expect(nav).toBeVisible();
    const links = nav.locator('a.shell-nav-link');
    await expect(links).toHaveCount(4);

    const labels = await links.allInnerTexts();
    expect(labels.map((l) => l.trim())).toEqual([
      navigation.today,
      navigation.story,
      navigation.plan,
      navigation.more,
    ]);

    // 2. Exactly one Quick Create trigger in compact shell, which is a button, not a link
    const trigger = floatingShell.locator(
      '.mobile-quick-create button.quick-create-trigger',
    );
    await expect(trigger).toBeVisible();
    await expect(trigger).toHaveAttribute('aria-label', navigation.newContent);
    await expect(trigger).toHaveAttribute('aria-haspopup', 'dialog');
    await expect(trigger).toHaveAttribute('type', 'button');

    // No old independent FAB outside the floating shell
    const oldFab = page.locator('body > .mobile-quick-create');
    await expect(oldFab).toHaveCount(0);

    // 3. Horizontal centering between Momente and Planen
    const momenteBox = await links.nth(1).boundingBox();
    const triggerBox = await trigger.boundingBox();
    const planenBox = await links.nth(2).boundingBox();
    expect(momenteBox).not.toBeNull();
    expect(triggerBox).not.toBeNull();
    expect(planenBox).not.toBeNull();

    if (momenteBox && triggerBox && planenBox) {
      expect(momenteBox.x + momenteBox.width).toBeLessThanOrEqual(
        triggerBox.x + 5,
      );
      expect(triggerBox.x + triggerBox.width).toBeLessThanOrEqual(
        planenBox.x + 5,
      );
    }

    // 4. Floating geometry: inset from viewport edges and elevated above bottom
    const shellBox = await floatingShell.boundingBox();
    expect(shellBox).not.toBeNull();
    if (shellBox) {
      expect(shellBox.x).toBeGreaterThan(0);
      expect(shellBox.x + shellBox.width).toBeLessThan(390);
      expect(844 - (shellBox.y + shellBox.height)).toBeGreaterThanOrEqual(8);
    }

    await expectNoHorizontalOverflow(page);
  });

  test('Quick Create mobile floating panel opens with fully rounded corners, clear nav separation and accessibility', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await installApiMocks(page);
    await page.goto('/login');
    await signIn(page);
    await page.waitForURL('**/today');

    const trigger = page.locator('.mobile-bottom-shell .quick-create-trigger');
    await trigger.click();

    // Sheet dialog opens
    const dialog = page.getByRole('dialog', {
      name: navigation.quickCreateTitle,
    });
    await expect(dialog).toBeVisible();

    // Sheet is above backdrop and floating nav
    const sheetZ = await dialog.evaluate((el) =>
      Number.parseInt(getComputedStyle(el).zIndex, 10),
    );
    const navZ = await page
      .locator('.mobile-bottom-shell')
      .evaluate((el) => Number.parseInt(getComputedStyle(el).zIndex, 10));
    expect(sheetZ).toBeGreaterThan(navZ);

    // Fully rounded floating panel geometry: both top and bottom corners are rounded
    const radii = await dialog.evaluate((el) => {
      const cs = getComputedStyle(el);
      return {
        topLeft: Number.parseFloat(cs.borderTopLeftRadius),
        topRight: Number.parseFloat(cs.borderTopRightRadius),
        bottomLeft: Number.parseFloat(cs.borderBottomLeftRadius),
        bottomRight: Number.parseFloat(cs.borderBottomRightRadius),
      };
    });
    expect(radii.topLeft).toBeGreaterThanOrEqual(16);
    expect(radii.topRight).toBeGreaterThanOrEqual(16);
    expect(radii.bottomLeft).toBeGreaterThanOrEqual(16);
    expect(radii.bottomRight).toBeGreaterThanOrEqual(16);

    // Horizontal insets: panel does not stretch to viewport edges
    const sheetBox = await dialog.boundingBox();
    const navBox = await page.locator('.mobile-bottom-shell').boundingBox();
    expect(sheetBox).not.toBeNull();
    expect(navBox).not.toBeNull();
    if (!sheetBox || !navBox) throw new Error('Missing bounding boxes');

    expect(sheetBox.x).toBeGreaterThan(0);
    expect(sheetBox.x + sheetBox.width).toBeLessThan(390);

    // Clear visual separation from floating bottom navigation (no clipping, no collision)
    expect(navBox.y - (sheetBox.y + sheetBox.height)).toBeGreaterThanOrEqual(8);

    // All 7 authoritative actions present inside dialog
    await expect(
      dialog.getByText(navigation.quickCreateMemory, { exact: true }),
    ).toBeVisible();
    await expect(
      dialog.getByText(navigation.quickCreateHeartMoment, { exact: true }),
    ).toBeVisible();
    await expect(
      dialog.getByText(navigation.quickCreateMilestone, { exact: true }),
    ).toBeVisible();
    await expect(
      dialog.getByText(navigation.quickCreateWish, { exact: true }),
    ).toBeVisible();
    await expect(
      dialog.getByText(navigation.quickCreatePlan, { exact: true }),
    ).toBeVisible();
    await expect(
      dialog.getByText(navigation.quickCreateForMe, { exact: true }),
    ).toBeVisible();
    await expect(
      dialog.getByText(navigation.quickCreatePrivateNote, { exact: true }),
    ).toBeVisible();
    await expect(
      dialog.getByText(navigation.quickCreateGiftIdea, { exact: true }),
    ).toBeVisible();

    // Accessibility: axe clean on open floating Quick Create panel in Light mode
    const axeResultsLight = await new AxeBuilder({ page })
      .include('.quick-create-mobile-sheet')
      .analyze();
    expect(axeResultsLight.violations).toEqual([]);

    // Capture sheet open evidence (Light mode)
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '00-quick-create-sheet-open-390.png'),
    });

    // Dark mode verification and evidence
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.style.colorScheme = 'dark';
    });
    // Allow CSS theme color transitions to settle before running axe
    await page.waitForTimeout(250);
    const axeResultsDark = await new AxeBuilder({ page })
      .include('.quick-create-mobile-sheet')
      .analyze();
    expect(axeResultsDark.violations).toEqual([]);

    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '00-quick-create-sheet-open-390-dark.png'),
    });

    // Restore Light mode for subsequent assertions
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'light');
      document.documentElement.style.colorScheme = 'light';
    });

    // Dismiss via Escape
    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
  });

  test('Quick Create floating panel in constrained height and 320px reflow maintains reachability and separation', async ({
    page,
  }) => {
    await installApiMocks(page);

    // 1. Constrained height (390x500)
    await page.setViewportSize({ width: 390, height: 500 });
    await page.goto('/login');
    await signIn(page);
    await page.waitForURL('**/today');

    const trigger = page.locator('.mobile-bottom-shell .quick-create-trigger');
    await trigger.click();

    const dialog = page.getByRole('dialog', {
      name: navigation.quickCreateTitle,
    });
    await expect(dialog).toBeVisible();

    // Verify dialog does not overflow top or bottom of viewport
    const smallSheetBox = await dialog.boundingBox();
    const smallNavBox = await page
      .locator('.mobile-bottom-shell')
      .boundingBox();
    expect(smallSheetBox).not.toBeNull();
    expect(smallNavBox).not.toBeNull();
    if (!smallSheetBox || !smallNavBox)
      throw new Error('Missing bounding boxes');

    expect(smallSheetBox.y).toBeGreaterThanOrEqual(0);
    expect(
      smallNavBox.y - (smallSheetBox.y + smallSheetBox.height),
    ).toBeGreaterThanOrEqual(8);

    // Verify reachability: scroll to the lowest item (Gift Idea) and verify it is visible and clickable
    const giftIdeaItem = dialog.getByText(navigation.quickCreateGiftIdea, {
      exact: true,
    });
    await giftIdeaItem.scrollIntoViewIfNeeded();
    await expect(giftIdeaItem).toBeVisible();

    // Close via close button
    const closeButton = dialog.getByRole('button', {
      name: navigation.closeMenu,
    });
    await closeButton.click();
    await expect(dialog).toHaveCount(0);

    // 2. 320px reflow
    await page.setViewportSize({ width: 320, height: 600 });
    await trigger.click();
    await expect(dialog).toBeVisible();

    await expectNoHorizontalOverflow(page);
    const reflowSheetBox = await dialog.boundingBox();
    expect(reflowSheetBox).not.toBeNull();
    if (!reflowSheetBox) throw new Error('Missing bounding boxes');
    expect(reflowSheetBox.x).toBeGreaterThan(0);
    expect(reflowSheetBox.x + reflowSheetBox.width).toBeLessThanOrEqual(320);

    // Dismiss via backdrop click
    const backdrop = page.locator('.quick-create-mobile-backdrop');
    await backdrop.click({ position: { x: 10, y: 10 } });
    await expect(dialog).toHaveCount(0);
  });

  test('navigation routing and active-state hierarchy', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await installApiMocks(page);
    await page.goto('/login');
    await signIn(page);
    await page.waitForURL('**/today');

    const links = page.locator('.mobile-bottom-nav a.shell-nav-link');

    // On /today, first link has active class and aria-current
    await expect(links.nth(0)).toHaveClass(/shell-nav-link-active/);
    await expect(links.nth(0)).toHaveAttribute('aria-current', 'page');
    await expect(links.nth(1)).not.toHaveClass(/shell-nav-link-active/);

    // Navigate to /story
    await links.nth(1).click();
    await page.waitForURL('**/story');
    await expect(links.nth(1)).toHaveClass(/shell-nav-link-active/);
    await expect(links.nth(1)).toHaveAttribute('aria-current', 'page');
    await expect(links.nth(0)).not.toHaveClass(/shell-nav-link-active/);

    // Navigate to /plan
    await links.nth(2).click();
    await page.waitForURL('**/plan');
    await expect(links.nth(2)).toHaveClass(/shell-nav-link-active/);
    await expect(links.nth(2)).toHaveAttribute('aria-current', 'page');

    // Navigate to /more
    await links.nth(3).click();
    await page.waitForURL('**/more');
    await expect(links.nth(3)).toHaveClass(/shell-nav-link-active/);
    await expect(links.nth(3)).toHaveAttribute('aria-current', 'page');
  });

  test('scroll clearance: Memory Create actions scroll fully clear of floating navigation', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await installApiMocks(page);
    await page.goto('/login');
    await signIn(page);
    await page.goto('/story/memories/new');

    const floatingShell = page.locator('.mobile-bottom-shell');
    await expect(floatingShell).toBeVisible();

    const saveButton = page.getByRole('button', { name: de.memory.save });
    const cancelButton = page.getByRole('link', { name: de.common.cancel });
    await expect(saveButton).toBeVisible();
    await expect(cancelButton).toBeVisible();

    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(100);

    const saveBox = await saveButton.boundingBox();
    const cancelBox = await cancelButton.boundingBox();
    const shellBox = await floatingShell.boundingBox();
    expect(saveBox).not.toBeNull();
    expect(cancelBox).not.toBeNull();
    expect(shellBox).not.toBeNull();

    if (saveBox && cancelBox && shellBox) {
      // Both the save button and bottom-most cancel link must be strictly above the floating bar top
      expect(saveBox.y + saveBox.height).toBeLessThan(shellBox.y);
      expect(cancelBox.y + cancelBox.height).toBeLessThan(shellBox.y);
      expect(
        shellBox.y - (cancelBox.y + cancelBox.height),
      ).toBeGreaterThanOrEqual(8);
    }
  });

  test('accessibility: axe clean on today and memory create', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await installApiMocks(page);
    await page.goto('/login');
    await signIn(page);
    await page.waitForURL('**/today');

    const todayAxe = await new AxeBuilder({ page })
      .disableRules(['color-contrast'])
      .analyze();
    expect(todayAxe.violations).toEqual([]);

    await page.goto('/story/memories/new');
    const memoryAxe = await new AxeBuilder({ page })
      .disableRules(['color-contrast'])
      .analyze();
    expect(memoryAxe.violations).toEqual([]);
  });

  test('200 percent zoom / large-text: floating navigation remains usable and collision-free', async ({
    page,
  }) => {
    // 780px viewport at 200% zoom represents the 390px mobile reference under 2x layout scale
    // following the established pattern in people-important-dates-mobile-first.spec.ts
    await page.setViewportSize({ width: 780, height: 844 });
    await installApiMocks(page);
    await page.goto('/login');
    await signIn(page);
    await page.waitForURL('**/today');

    // Apply established repository zoom methodology
    await page.locator('html').evaluate((element) => {
      element.style.zoom = '2';
    });
    await page.evaluate(
      () =>
        new Promise<void>((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
        ),
    );

    // 1. No horizontal overflow
    await expectNoHorizontalOverflow(page);

    // 2. Floating navigation remains visible and usable
    const floatingShell = page.locator('.mobile-bottom-shell');
    await expect(floatingShell).toBeVisible();

    // 3. Four destination labels remain understandable and present
    const links = floatingShell.locator('.mobile-bottom-nav a.shell-nav-link');
    await expect(links).toHaveCount(4);
    for (let i = 0; i < 4; i += 1) {
      await expect(links.nth(i)).toBeVisible();
    }
    const labels = await links.allInnerTexts();
    expect(labels.map((l) => l.trim())).toEqual([
      navigation.today,
      navigation.story,
      navigation.plan,
      navigation.more,
    ]);

    // 4. Center Quick Create action remains correctly positioned & visible
    const trigger = floatingShell.locator(
      '.mobile-quick-create button.quick-create-trigger',
    );
    await expect(trigger).toBeVisible();

    // 5. No collision between destinations and center action
    const momenteBox = await links.nth(1).boundingBox();
    const triggerBox = await trigger.boundingBox();
    const planenBox = await links.nth(2).boundingBox();
    expect(momenteBox).not.toBeNull();
    expect(triggerBox).not.toBeNull();
    expect(planenBox).not.toBeNull();
    if (momenteBox && triggerBox && planenBox) {
      expect(momenteBox.x + momenteBox.width).toBeLessThanOrEqual(
        triggerBox.x + 1,
      );
      expect(triggerBox.x + triggerBox.width).toBeLessThanOrEqual(
        planenBox.x + 1,
      );
    }

    // 6. Bottom content/actions on Memory Create remain scrollable clear of the shell under 200% zoom
    await page.goto('/story/memories/new');
    await page.locator('html').evaluate((element) => {
      element.style.zoom = '2';
    });
    await page.evaluate(
      () =>
        new Promise<void>((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
        ),
    );
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(100);

    const cancelBtn = page.getByRole('link', { name: de.common.cancel });
    const zoomShell = page.locator('.mobile-bottom-shell');
    await expect(cancelBtn).toBeVisible();
    await expect(zoomShell).toBeVisible();

    const cancelB = await cancelBtn.boundingBox();
    const shellB = await zoomShell.boundingBox();
    if (cancelB && shellB) {
      expect(cancelB.y + cancelB.height).toBeLessThanOrEqual(shellB.y + 1);
    }
  });

  test('captures required visual evidence matrix', async ({ page }) => {
    await installApiMocks(page);

    // 1. /today — 390x844 Light
    await page.setViewportSize({ width: 390, height: 844 });
    await page.emulateMedia({ colorScheme: 'light' });
    await page.goto('/login');
    await signIn(page);
    await page.waitForURL('**/today');
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '01-today-390-light.png'),
    });

    // 2. /today — 390x844 Dark
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.evaluate(() => {
      localStorage.setItem('sidebyside.theme', 'dark');
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.style.colorScheme = 'dark';
    });
    await page.reload();
    await page.waitForURL('**/today');
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '02-today-390-dark.png'),
    });

    // 3. Memory Create — 390x844 Light
    await page.emulateMedia({ colorScheme: 'light' });
    await page.evaluate(() => {
      localStorage.setItem('sidebyside.theme', 'light');
      document.documentElement.setAttribute('data-theme', 'light');
      document.documentElement.style.colorScheme = 'light';
    });
    await page.goto('/story/memories/new');
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '03-memory-create-390-light.png'),
    });

    // 4. Memory Create — 390x844 Dark
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.evaluate(() => {
      localStorage.setItem('sidebyside.theme', 'dark');
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.style.colorScheme = 'dark';
    });
    await page.reload();
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '04-memory-create-390-dark.png'),
    });

    // 5. Plan create state — 390x844 Light
    await page.emulateMedia({ colorScheme: 'light' });
    await page.evaluate(() => {
      localStorage.setItem('sidebyside.theme', 'light');
      document.documentElement.setAttribute('data-theme', 'light');
      document.documentElement.style.colorScheme = 'light';
    });
    await page.goto('/plan');
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '05-plan-390-light.png'),
    });

    // 6. Representative Momente surface — 390x844 Light
    await page.goto('/story');
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '06-momente-390-light.png'),
    });

    // 7. 320 CSS px reflow
    await page.setViewportSize({ width: 320, height: 600 });
    await page.goto('/today');
    await expectNoHorizontalOverflow(page);
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '07-reflow-320px.png'),
    });

    // 8. Representative small-height state (390x640)
    await page.setViewportSize({ width: 390, height: 640 });
    await page.goto('/today');
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '08-small-height-390x640.png'),
    });

    // 9. Constrained-height form focus state (390x500) representing software-keyboard occlusion
    await page.setViewportSize({ width: 390, height: 500 });
    await page.goto('/story/memories/new');
    const titleInput = page.getByLabel(de.memory.titleLabel);
    await titleInput.focus();
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '09-constrained-height-form-focus.png'),
    });

    // 10. Expanded desktop regression (1280x800)
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/today');
    await expect(page.locator('.mobile-bottom-shell')).toBeHidden();
    await expect(page.locator('.shell-nav')).toBeVisible();
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '10-expanded-desktop-1280x800.png'),
    });

    // 11. Large text / 200 percent layout zoom (780x844 representing 390px reference)
    await page.setViewportSize({ width: 780, height: 844 });
    await page.goto('/today');
    await page.locator('html').evaluate((element) => {
      element.style.zoom = '2';
    });
    await page.evaluate(
      () =>
        new Promise<void>((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
        ),
    );
    await page.screenshot({
      path: path.join(EVIDENCE_DIR, '11-zoom-200-percent.png'),
    });
  });
});
