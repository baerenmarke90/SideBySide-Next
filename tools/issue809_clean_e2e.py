"""Restore the canonical E2E file and apply only #809 semantic edits."""

from __future__ import annotations

import subprocess
from pathlib import Path

PATH = Path("web/e2e/tests/product-reflow.spec.ts")


def replace_once(old: str, new: str) -> None:
    text = PATH.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one match, found {count}: {old[:120]!r}")
    PATH.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


base = subprocess.run(
    ["git", "show", "origin/main:web/e2e/tests/product-reflow.spec.ts"],
    check=True,
    capture_output=True,
    text=True,
).stdout
PATH.write_text(base, encoding="utf-8", newline="\n")

replace_once(
    "import { expect, test, type Page } from '@playwright/test';\n"
    "import de from '../../src/i18n/locales/de';\n",
    "import AxeBuilder from '@axe-core/playwright';\n"
    "import { expect, test, type Page } from '@playwright/test';\n"
    "import de from '../../src/i18n/locales/de';\n"
    "import m5s5 from '../../src/i18n/locales/m5s5';\n",
)
replace_once(
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
    "      return;\n    }\n\n    if (\n      method === 'GET' &&\n      pathname === `/api/v1/spaces/${SPACE_ID}/timeline`\n",
    "      return;\n    }\n\n"
    "    if (\n"
    "      method === 'GET' &&\n"
    "      pathname === `/api/v1/spaces/${SPACE_ID}/dashboard/preferences`\n"
    "    ) {\n"
    "      await fulfillJson({\n"
    "        items: [{ moduleKey: 'SHARED_STORY_SUMMARY', visible: true }],\n"
    "      });\n"
    "      return;\n"
    "    }\n\n"
    "    if (\n      method === 'GET' &&\n      pathname === `/api/v1/spaces/${SPACE_ID}/timeline`\n",
)
replace_once(
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
    "    .analyze();\n\n"
    "  const summary = result.violations\n"
    "    .map(\n"
    "      (violation) =>\n"
    "        `${violation.id} (${violation.impact ?? 'unknown'}): ${violation.nodes.length} node(s)`,\n"
    "    )\n"
    "    .join('\\n');\n\n"
    "  expect(result.violations, summary || 'No axe violations').toEqual([]);\n"
    "}\n\n"
    "async function expectHorizontalReflow(page: Page): Promise<void> {\n",
)
replace_once(
    "test('representative layout families keep their accepted normal viewport reflow', async ({\n"
    "  page,\n"
    "}) => {\n",
    "test('representative layout families keep their accepted normal viewport reflow', async ({\n"
    "  page,\n"
    "}, testInfo) => {\n",
)
replace_once(
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
