"""One-shot bounded browser-evidence edits for #809; removed by its workflow."""

from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:120]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# Only request the private presentation preference when the shared summary is
# product-eligible. Sparse/new Spaces therefore pay no extra request and the
# UI stays graceful against an older Dashboard payload during rolling deploys.
replace_once(
    "web/src/components/TodayPage.tsx",
    "import { SharedStorySummary } from './SharedStorySummary';\n",
    "import {\n"
    "  SharedStorySummary,\n"
    "  sharedStorySummaryIsEligible,\n"
    "} from './SharedStorySummary';\n",
)
replace_once(
    "web/src/components/TodayPage.tsx",
    "  const dashboardPreferencesQuery = useQuery({\n"
    "    queryKey: dashboardPreferencesQueryKey(spaceId),\n"
    "    queryFn: () =>\n"
    "      apiCall(() => apis.dashboard.listDashboardModulePreferences({ spaceId })),\n"
    "    retry: false,\n"
    "  });\n",
    "  const sharedStorySummaryEligible = dashboardQuery.data?.sharedStorySummary\n"
    "    ? sharedStorySummaryIsEligible(dashboardQuery.data.sharedStorySummary)\n"
    "    : false;\n"
    "  const dashboardPreferencesQuery = useQuery({\n"
    "    queryKey: dashboardPreferencesQueryKey(spaceId),\n"
    "    queryFn: () =>\n"
    "      apiCall(() => apis.dashboard.listDashboardModulePreferences({ spaceId })),\n"
    "    enabled: sharedStorySummaryEligible,\n"
    "    retry: false,\n"
    "  });\n",
)
replace_once(
    "web/src/components/TodayPage.tsx",
    "  const sharedStorySummaryVisible =\n"
    "    dashboardPreferencesQuery.data?.items.some(\n"
    "      (item) =>\n"
    "        item.moduleKey === DashboardModuleKey.SHARED_STORY_SUMMARY &&\n"
    "        item.visible,\n"
    "    ) ?? false;\n",
    "  const sharedStorySummaryVisible =\n"
    "    sharedStorySummaryEligible &&\n"
    "    (dashboardPreferencesQuery.data?.items.some(\n"
    "      (item) =>\n"
    "        item.moduleKey === DashboardModuleKey.SHARED_STORY_SUMMARY &&\n"
    "        item.visible,\n"
    "    ) ??\n"
    "      false);\n",
)

# Give the Settings row the same editorial spacing rhythm as the existing
# settings sections without creating a separate card/widget visual language.
replace_once(
    "web/src/components/SettingsPage.css",
    ".anniversary-reminder-form {\n",
    ".dashboard-settings-list {\n"
    "  display: grid;\n"
    "  gap: var(--space-3);\n"
    "  max-width: 42rem;\n"
    "  margin-top: var(--space-5);\n"
    "}\n\n"
    ".dashboard-settings-list .form-checkbox-label {\n"
    "  min-height: 44px;\n"
    "}\n\n"
    ".dashboard-settings-list .form-checkbox-label > span {\n"
    "  display: grid;\n"
    "  min-width: 0;\n"
    "  gap: var(--space-1);\n"
    "}\n\n"
    ".dashboard-settings-list .form-checkbox-label small {\n"
    "  color: var(--color-text-secondary);\n"
    "  font-weight: 500;\n"
    "}\n\n"
    ".anniversary-reminder-form {\n",
)

# Extend the repository's canonical product reflow suite so the new module is
# actually rendered at both normal 320px and 1280@400% (= 320 CSS px), axe is
# run against it, and Compact/Expanded screenshots become normal shell evidence.
replace_once(
    "web/e2e/tests/product-reflow.spec.ts",
    "import { expect, test, type Page } from '@playwright/test';\n"
    "import de from '../../src/i18n/locales/de';\n",
    "import AxeBuilder from '@axe-core/playwright';\n"
    "import { expect, test, type Page } from '@playwright/test';\n"
    "import de from '../../src/i18n/locales/de';\n"
    "import m5s5 from '../../src/i18n/locales/m5s5';\n",
)
replace_once(
    "web/e2e/tests/product-reflow.spec.ts",
    "        relationshipDuration: {\n"
    "          daysTogether: 1174,\n"
    "          startedOn: '2023-06-17',\n"
    "        },\n"
    "        retrospective: null,\n"
    "        recentShared: [],\n",
    "        relationshipDuration: {\n"
    "          daysTogether: 1174,\n"
    "          displayMode: 'DAYS',\n"
    "          startedOn: '2023-06-17',\n"
    "        },\n"
    "        retrospective: null,\n"
    "        keepsake: null,\n"
    "        recentShared: [],\n"
    "        sharedStorySummary: {\n"
    "          memories: 4,\n"
    "          heartMoments: 1,\n"
    "          milestones: 0,\n"
    "        },\n"
    "        thinkingOfYouAvailableAt: null,\n",
)
replace_once(
    "web/e2e/tests/product-reflow.spec.ts",
    "      return;\n    }\n\n    if (\n      method === 'GET' &&\n      pathname === `/api/v1/spaces/${SPACE_ID}/timeline`\n",
    "      return;\n    }\n\n"
    "    if (\n"
    "      method === 'GET' &&\n"
    "      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard/preferences`\n"
    "    ) {\n"
    "      await fulfillJson({\n"
    "        items: [\n"
    "          { moduleKey: 'SHARED_STORY_SUMMARY', visible: true },\n"
    "        ],\n"
    "      });\n"
    "      return;\n"
    "    }\n\n"
    "    if (\n      method === 'GET' &&\n      pathname === `/api/v1/spaces/${SPACE_ID}/timeline`\n",
)
replace_once(
    "web/e2e/tests/product-reflow.spec.ts",
    "async function expectHorizontalReflow(page: Page): Promise<void> {\n",
    "async function expectNoWcagViolations(page: Page): Promise<void> {\n"
    "  const result = await new AxeBuilder({ page })\n"
    "    .withTags([\n"
    "      'wcag2a',\n"
    "      'wcag2aa',\n"
    "      'wcag21a',\n"
    "      'wcag21aa',\n"
    "      'wcag22a',\n"
    "      'wcag22aa',\n"
    "    ])\n"
    "    .analyze();\n"
    "  expect(\n"
    "    result.violations,\n"
    "    result.violations\n"
    "      .map(\n"
    "        (violation) =>\n"
    "          `${violation.id} (${violation.impact ?? 'unknown'}): ${violation.nodes.length} node(s)`,\n"
    "      )\n"
    "      .join('\\n') || 'No axe violations',\n"
    "  ).toEqual([]);\n"
    "}\n\n"
    "async function expectHorizontalReflow(page: Page): Promise<void> {\n",
)
replace_once(
    "web/e2e/tests/product-reflow.spec.ts",
    "test('representative layout families keep their accepted normal viewport reflow', async ({\n"
    "  page,\n"
    "}) => {\n",
    "test('representative layout families keep their accepted normal viewport reflow', async ({\n"
    "  page,\n"
    "}, testInfo) => {\n",
)
replace_once(
    "web/e2e/tests/product-reflow.spec.ts",
    "      await page.goto(path);\n"
    "      await expect(page.locator('#main-content')).toBeVisible();\n"
    "      await expectHorizontalReflow(page);\n"
    "    }\n"
    "  }\n\n"
    "  expect(unexpectedRequests).toEqual([]);\n"
    "});\n\n"
    "test('400 percent reflow keeps keyboard-reachable controls inside the viewport'",
    "      await page.goto(path);\n"
    "      await expect(page.locator('#main-content')).toBeVisible();\n"
    "      await expectHorizontalReflow(page);\n"
    "      if (path === '/today') {\n"
    "        await expect(\n"
    "          page.getByRole('heading', {\n"
    "            name: m5s5.dashboard.storySummaryTitle,\n"
    "            level: 2,\n"
    "          }),\n"
    "        ).toBeVisible();\n"
    "        if (width === 320 || width === 1440) {\n"
    "          await expectNoWcagViolations(page);\n"
    "          await page.screenshot({\n"
    "            path: testInfo.outputPath(\n"
    "              `shell-today-story-summary-${width}.png`,\n"
    "            ),\n"
    "            fullPage: true,\n"
    "          });\n"
    "        }\n"
    "      }\n"
    "    }\n"
    "  }\n\n"
    "  expect(unexpectedRequests).toEqual([]);\n"
    "});\n\n"
    "test('400 percent reflow keeps keyboard-reachable controls inside the viewport'",
)
