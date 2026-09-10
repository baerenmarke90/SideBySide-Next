import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page, type TestInfo } from '@playwright/test';
import de from '../../src/i18n/locales/de';
import m5s3 from '../../src/i18n/locales/m5s3';
import navigation from '../../src/i18n/locales/navigation';

const ACCOUNT_ID = '11111111-1111-4111-8111-111111111111';
const SPACE_ID = '22222222-2222-4222-8222-222222222222';
const PROFILE_ID = '33333333-3333-4333-8333-333333333333';
const TEST_NOW = '2026-09-01T10:00:00Z';

type MockCalls = {
  wishCreates: number;
  planCreates: number;
  lastPlanPlaceId?: string;
};

async function installPlanningMocks(page: Page): Promise<MockCalls> {
  const calls: MockCalls = { wishCreates: 0, planCreates: 0 };

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
          accessToken: 'planning-focused-create-access-token',
          refreshExpiresAt: new Date(Date.now() + 86_400_000).toISOString(),
          refreshToken: 'planning-focused-create-refresh-token',
        },
      });
      return;
    }

    if (method === 'POST' && pathname === '/api/v1/auth/refresh') {
      await fulfillJson({
        accessExpiresAt: new Date(Date.now() + 3_600_000).toISOString(),
        accessToken: 'planning-focused-create-access-token-refreshed',
        refreshExpiresAt: new Date(Date.now() + 86_400_000).toISOString(),
        refreshToken: 'planning-focused-create-refresh-token-refreshed',
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
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/plans`) {
      await fulfillJson({ hasMore: false, items: [], nextCursor: null });
      return;
    }

    if (method === 'GET' && pathname === `/api/v1/spaces/${SPACE_ID}/places`) {
      await fulfillJson({
        hasMore: false,
        nextCursor: null,
        items: [
          {
            address: null,
            capabilities: { canEdit: true, canDelete: true },
            createdAt: TEST_NOW,
            createdBy: ACCOUNT_ID,
            creator: { accountId: ACCOUNT_ID, displayName: 'Anna' },
            description: null,
            id: 'place-berlin',
            latitude: null,
            longitude: null,
            name: 'Berlin',
            spaceId: SPACE_ID,
            updatedAt: TEST_NOW,
            version: 1,
          },
        ],
      });
      return;
    }

    if (method === 'POST' && pathname === `/api/v1/spaces/${SPACE_ID}/wishes`) {
      calls.wishCreates += 1;
      const body = request.postDataJSON() as { title: string };
      await fulfillJson(
        {
          capabilities: { canDelete: true, canEdit: true },
          createdAt: TEST_NOW,
          createdBy: ACCOUNT_ID,
          creator: { accountId: ACCOUNT_ID, displayName: 'Anna' },
          id: 'wish-created',
          spaceId: SPACE_ID,
          status: 'IDEA',
          title: body.title,
          updatedAt: TEST_NOW,
          version: 1,
        },
        201,
      );
      return;
    }

    if (method === 'POST' && pathname === `/api/v1/spaces/${SPACE_ID}/plans`) {
      calls.planCreates += 1;
      const body = request.postDataJSON() as {
        title: string;
        description?: string;
        placeId?: string;
      };
      calls.lastPlanPlaceId = body.placeId;
      await fulfillJson(
        {
          capabilities: { canDelete: true, canEdit: true },
          createdAt: TEST_NOW,
          createdBy: ACCOUNT_ID,
          creator: { accountId: ACCOUNT_ID, displayName: 'Anna' },
          description: body.description ?? null,
          experiencedOn: null,
          id: 'plan-created',
          placeId: body.placeId ?? null,
          plannedEnd: null,
          plannedStart: null,
          sourceWishId: null,
          spaceId: SPACE_ID,
          status: 'IDEA',
          title: body.title,
          updatedAt: TEST_NOW,
          version: 1,
        },
        201,
      );
      return;
    }

    await fulfillJson(
      {
        code: 'E2E_UNEXPECTED_REQUEST',
        detail: `Planning focused-create test does not define ${method} ${pathname}.`,
        status: 500,
        title: 'Unexpected browser test request',
      },
      500,
    );
  });

  return calls;
}

async function signIn(page: Page): Promise<void> {
  await page.goto('/today');
  await page.getByLabel(de.login.email).fill('anna@example.org');
  await page.getByLabel(de.login.password).fill('a-long-enough-test-password');
  await page.getByRole('button', { name: de.login.submit }).click();
  await expect(page.getByLabel(de.login.email)).toHaveCount(0);
}

async function assertNoHorizontalOverflow(page: Page): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
}

async function assertNoWcagViolations(page: Page): Promise<void> {
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
  const summary = result.violations
    .map(
      (violation) =>
        `${violation.id} (${violation.impact ?? 'unknown'}): ${violation.nodes.length} node(s)`,
    )
    .join('\n');
  expect(result.violations, summary || 'No axe violations').toEqual([]);
}

type ComposerKind = 'wish' | 'plan';

type VisualScenario = {
  name: string;
  viewport: { width: number; height: number };
  theme: 'light' | 'dark';
};

const visualScenarios: VisualScenario[] = [
  { name: '390-light', viewport: { width: 390, height: 844 }, theme: 'light' },
  { name: '390-dark', viewport: { width: 390, height: 844 }, theme: 'dark' },
  { name: '320', viewport: { width: 320, height: 720 }, theme: 'light' },
  {
    name: 'small-height',
    viewport: { width: 390, height: 640 },
    theme: 'light',
  },
  {
    name: 'expanded',
    viewport: { width: 1280, height: 900 },
    theme: 'light',
  },
];

const composerContracts: Record<
  ComposerKind,
  { hash: string; titleId: string; formTitle: string }
> = {
  wish: {
    hash: 'wish-title',
    titleId: 'create-wish-title',
    formTitle: m5s3.wish.create,
  },
  plan: {
    hash: 'plan-title',
    titleId: 'create-plan-title',
    formTitle: m5s3.plan.create,
  },
};

async function prepareScenario(
  page: Page,
  kind: ComposerKind,
  scenario: VisualScenario,
): Promise<void> {
  await page.setViewportSize(scenario.viewport);
  await page.addInitScript((theme) => {
    window.localStorage.setItem('sidebyside.theme', theme);
  }, scenario.theme);
  await installPlanningMocks(page);
  await signIn(page);
  const contract = composerContracts[kind];
  await page.goto(`/plan#${contract.hash}`);

  const details = page.locator(`details:has(#${contract.hash})`);
  await expect(details).toHaveJSProperty('open', true);
  await expect(
    details.getByText(contract.formTitle, { exact: true }),
  ).toBeVisible();
  await expect(page.locator(`#${contract.titleId}`)).toBeVisible();
  expect(await page.evaluate(() => document.activeElement?.id ?? '')).not.toBe(
    contract.titleId,
  );
  await expect(page.locator('html')).toHaveAttribute(
    'data-theme',
    scenario.theme,
  );
  await assertNoHorizontalOverflow(page);

  const materiality = await details.evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      backgroundImage: style.backgroundImage,
      borderRadius: style.borderRadius,
      boxShadow: style.boxShadow,
    };
  });
  expect(materiality.backgroundImage).not.toBe('none');
  expect(materiality.borderRadius).not.toBe('0px');
  expect(materiality.boxShadow).not.toBe('none');
}

async function captureEvidence(
  page: Page,
  testInfo: TestInfo,
  name: string,
): Promise<void> {
  await page.screenshot({
    path: testInfo.outputPath(`planning-856-${name}.png`),
    fullPage: false,
  });
}

for (const kind of ['wish', 'plan'] as const) {
  for (const scenario of visualScenarios) {
    test(`${kind} focused create surface: ${scenario.name}`, async ({
      page,
    }, testInfo) => {
      await prepareScenario(page, kind, scenario);
      if (scenario.name === '390-light') await assertNoWcagViolations(page);
      await captureEvidence(page, testInfo, `${kind}-${scenario.name}`);
    });
  }
}

test('closed Planning context stays quiet next to the focused open state', async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    window.localStorage.setItem('sidebyside.theme', 'light');
  });
  await installPlanningMocks(page);
  await signIn(page);
  await page.goto('/plan');

  await expect(page.locator('details:has(#wish-title)')).toHaveJSProperty(
    'open',
    false,
  );
  await expect(page.locator('details:has(#plan-title)')).toHaveJSProperty(
    'open',
    false,
  );
  await captureEvidence(page, testInfo, 'closed-390-light');
});

test('Quick Create preserves Wish/Plan hash handoff, no-focus behavior, and Browser Back', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await installPlanningMocks(page);
  await signIn(page);
  await page.goto('/today');

  const openQuickCreate = async () => {
    await page.getByRole('button', { name: navigation.newContent }).click();
  };

  await openQuickCreate();
  await page.getByText(navigation.quickCreateWish, { exact: true }).click();
  await expect(page).toHaveURL(/\/plan#wish-title$/);
  await expect(page.locator('details:has(#wish-title)')).toHaveJSProperty(
    'open',
    true,
  );
  expect(await page.evaluate(() => document.activeElement?.id ?? '')).not.toBe(
    'create-wish-title',
  );

  await page.goBack();
  await expect(page).toHaveURL(/\/today$/);

  await openQuickCreate();
  await page.getByText(navigation.quickCreatePlan, { exact: true }).click();
  await expect(page).toHaveURL(/\/plan#plan-title$/);
  await expect(page.locator('details:has(#plan-title)')).toHaveJSProperty(
    'open',
    true,
  );
  expect(await page.evaluate(() => document.activeElement?.id ?? '')).not.toBe(
    'create-plan-title',
  );

  await page.goBack();
  await expect(page).toHaveURL(/\/today$/);
});

test('Wish and Plan create semantics still submit through the existing inline forms', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const calls = await installPlanningMocks(page);
  await signIn(page);

  await page.goto('/plan#wish-title');
  const wish = page.locator('details:has(#wish-title)');
  await wish
    .getByLabel(m5s3.common.title, { exact: true })
    .fill('See the northern lights');
  await wish.getByRole('button', { name: m5s3.common.save }).click();
  await expect(wish.getByLabel(m5s3.common.title, { exact: true })).toHaveValue(
    '',
  );
  expect(calls.wishCreates).toBe(1);

  await page.goto('/plan#plan-title');
  const plan = page.locator('details:has(#plan-title)');
  await plan
    .getByLabel(m5s3.common.title, { exact: true })
    .fill('Weekend in Berlin');
  await plan
    .getByLabel(m5s3.common.description, { exact: true })
    .fill('A quiet weekend together');
  await plan.getByRole('button', { name: m5s3.common.place }).click();
  await page
    .getByRole('menu', { name: m5s3.common.place })
    .getByRole('menuitemradio', { name: 'Berlin' })
    .click();
  await plan.getByRole('button', { name: m5s3.common.save }).click();
  await expect(plan.getByLabel(m5s3.common.title, { exact: true })).toHaveValue(
    '',
  );
  expect(calls.planCreates).toBe(1);
  expect(calls.lastPlanPlaceId).toBe('place-berlin');
});

test('PlacePicker remains portalled, opens below/above its trigger, stays viewport-bound, and restores focus', async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ width: 390, height: 640 });
  await installPlanningMocks(page);
  await signIn(page);
  await page.goto('/plan#plan-title');

  const plan = page.locator('details:has(#plan-title)');
  const trigger = plan.getByRole('button', {
    name: m5s3.common.place,
    exact: true,
  });

  await trigger.evaluate((element) =>
    element.scrollIntoView({ block: 'start' }),
  );
  await trigger.press('ArrowDown');

  const menu = page.getByRole('menu', { name: m5s3.common.place });
  await expect(menu).toBeVisible();
  await expect(
    menu.getByRole('menuitemradio', { name: m5s3.common.noPlace }),
  ).toBeFocused();
  expect(
    await menu.evaluate((element) => element.parentElement === document.body),
  ).toBe(true);

  const belowBox = await menu.boundingBox();
  const belowTriggerBox = await trigger.boundingBox();
  expect(belowBox).not.toBeNull();
  expect(belowTriggerBox).not.toBeNull();
  if (!belowBox || !belowTriggerBox) {
    throw new Error('PlacePicker below-placement geometry is unavailable');
  }
  expect(belowBox.y).toBeGreaterThanOrEqual(
    belowTriggerBox.y + belowTriggerBox.height,
  );
  expect(belowBox.y).toBeGreaterThanOrEqual(0);
  expect(belowBox.y + belowBox.height).toBeLessThanOrEqual(640);

  await captureEvidence(page, testInfo, 'plan-small-height-place-picker-below');
  await page.keyboard.press('End');
  await expect(
    menu.getByRole('menuitem', { name: m5s3.plan.addNewPlace }),
  ).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(menu).toBeHidden();
  await expect(trigger).toBeFocused();

  await trigger.evaluate((element) => element.scrollIntoView({ block: 'end' }));
  await trigger.press('ArrowDown');
  await expect(menu).toBeVisible();
  await expect(
    menu.getByRole('menuitemradio', { name: m5s3.common.noPlace }),
  ).toBeFocused();

  const aboveBox = await menu.boundingBox();
  const aboveTriggerBox = await trigger.boundingBox();
  expect(aboveBox).not.toBeNull();
  expect(aboveTriggerBox).not.toBeNull();
  if (!aboveBox || !aboveTriggerBox) {
    throw new Error('PlacePicker above-placement geometry is unavailable');
  }
  expect(aboveBox.y + aboveBox.height).toBeLessThanOrEqual(aboveTriggerBox.y);
  expect(aboveBox.y).toBeGreaterThanOrEqual(0);
  expect(aboveBox.y + aboveBox.height).toBeLessThanOrEqual(640);

  await captureEvidence(page, testInfo, 'plan-small-height-place-picker-above');
  await page.keyboard.press('Escape');
  await expect(menu).toBeHidden();
  await expect(trigger).toBeFocused();
});

test('Planning composers reflow at 200% layout zoom without horizontal overflow', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await installPlanningMocks(page);
  await signIn(page);
  await page.goto('/plan#plan-title');
  await assertNoHorizontalOverflow(page);

  await page.locator('html').evaluate((element) => {
    element.style.zoom = '2';
  });

  const dimensions = await page.evaluate(() => ({
    bodyScrollWidth: document.body.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.clientWidth).toBe(390);
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
  expect(dimensions.bodyScrollWidth).toBeLessThan(320);
  await expect(page.locator('#create-plan-title')).toBeVisible();
  await expect(
    page.locator('details:has(#plan-title)').getByRole('button', {
      name: m5s3.common.save,
    }),
  ).toBeVisible();
});
