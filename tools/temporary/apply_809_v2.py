from __future__ import annotations

import json
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one replacement anchor, found {count}: {old[:120]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def write(path: str, content: str) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Backend: authoritative shared Story aggregate, consumed by Dashboard.
# ---------------------------------------------------------------------------
replace_once(
    "backend/src/sidebyside/story/service.py",
    '''@dataclass(frozen=True)\nclass StoryPageResult:\n    items: list[StoryRow]\n    next_cursor: str | None\n    has_more: bool\n\n\n''',
    '''@dataclass(frozen=True)\nclass StoryPageResult:\n    items: list[StoryRow]\n    next_cursor: str | None\n    has_more: bool\n\n\n@dataclass(frozen=True)\nclass SharedStoryCounts:\n    """All-time counts for the relationship-shared Story projection (#809)."""\n\n    memories: int\n    heart_moments: int\n    milestones: int\n\n\n''',
)
replace_once(
    "backend/src/sidebyside/story/service.py",
    '''    return statement\n\n\ndef _cursor_binding(\n''',
    '''    return statement\n\n\ndef read_shared_story_counts(\n    session: Session,\n    context: AuthorizationContext,\n) -> SharedStoryCounts:\n    """Count the shared Story without materializing Story rows.\n\n    The aggregation reuses the exact authorized Timeline legs. In particular,\n    OWNER_ONLY HeartMoments are excluded by ``_leg`` before counting, so they\n    cannot influence either a value or #809's presentation eligibility.\n    """\n    combined = union_all(*(_leg(kind, context, year=None) for kind in StoryKind)).subquery(\n        "shared_story_counts"\n    )\n    rows = session.execute(\n        select(combined.c.kind_rank, func.count())\n        .group_by(combined.c.kind_rank)\n        .order_by(combined.c.kind_rank)\n    ).all()\n    counts = {int(kind_rank): int(count) for kind_rank, count in rows}\n    return SharedStoryCounts(\n        memories=counts.get(_KIND_RANK[StoryKind.MEMORY], 0),\n        heart_moments=counts.get(_KIND_RANK[StoryKind.HEART_MOMENT], 0),\n        milestones=counts.get(_KIND_RANK[StoryKind.MILESTONE], 0),\n    )\n\n\ndef _cursor_binding(\n''',
)

replace_once(
    "backend/src/sidebyside/api/v1/dashboard.py",
    "from sidebyside.relationship.models import DurationDisplayMode\n",
    "from sidebyside.relationship.models import DurationDisplayMode\nfrom sidebyside.story import service as story_service\n",
)
replace_once(
    "backend/src/sidebyside/api/v1/dashboard.py",
    '''class DashboardView(ApiModel):\n''',
    '''class DashboardSharedStorySummary(ApiModel):\n    memories: int\n    heart_moments: int\n    milestones: int\n\n\nclass DashboardView(ApiModel):\n''',
)
replace_once(
    "backend/src/sidebyside/api/v1/dashboard.py",
    '''    recent_shared: list[DashboardItem]\n    thinking_of_you_available_at: datetime | None\n''',
    '''    recent_shared: list[DashboardItem]\n    shared_story_summary: DashboardSharedStorySummary\n    thinking_of_you_available_at: datetime | None\n''',
)
replace_once(
    "backend/src/sidebyside/api/v1/dashboard.py",
    '''    view = service.read_dashboard(session, authorization)\n    response.headers["Cache-Control"] = "private, no-store"\n''',
    '''    view = service.read_dashboard(session, authorization)\n    shared_story_counts = story_service.read_shared_story_counts(session, authorization)\n    response.headers["Cache-Control"] = "private, no-store"\n''',
)
replace_once(
    "backend/src/sidebyside/api/v1/dashboard.py",
    '''        recent_shared=[_project_item(item) for item in view.recent_shared],\n        thinking_of_you_available_at=view.thinking_of_you_available_at,\n''',
    '''        recent_shared=[_project_item(item) for item in view.recent_shared],\n        shared_story_summary=DashboardSharedStorySummary(\n            memories=shared_story_counts.memories,\n            heart_moments=shared_story_counts.heart_moments,\n            milestones=shared_story_counts.milestones,\n        ),\n        thinking_of_you_available_at=view.thinking_of_you_available_at,\n''',
)

# ---------------------------------------------------------------------------
# Existing #817/#929 Dashboard module registry: register #809, nothing more.
# ---------------------------------------------------------------------------
replace_once(
    "backend/src/sidebyside/dashboard/preferences.py",
    '''    MONTHLY_HIGHLIGHTS = "monthly_highlights"\n    RECENT_SHARED = "recent_shared"\n''',
    '''    MONTHLY_HIGHLIGHTS = "monthly_highlights"\n    RECENT_SHARED = "recent_shared"\n    SHARED_STORY_SUMMARY = "shared_story_summary"\n''',
)
replace_once(
    "backend/src/sidebyside/dashboard/preferences.py",
    '''# `SHARED_STORY_SUMMARY` (#809) is deliberately absent: it is not merged to\n# `main`, and #817 does not implement #809 on its behalf. Once #809 lands, its\n# module registers here the same way every other module did and automatically\n# participates in this mechanism.\n''',
    '''# #809 appends the quiet shared-story epilogue after the existing Today\n# composition. It is a normal registered module and therefore inherits the\n# same per-Account+Space visibility behavior as every other Dashboard module.\n''',
)
replace_once(
    "backend/src/sidebyside/dashboard/preferences.py",
    '''    DashboardModuleDefinition(key=DashboardModuleKey.MONTHLY_HIGHLIGHTS, default_visible=True),\n    DashboardModuleDefinition(key=DashboardModuleKey.RECENT_SHARED, default_visible=True),\n)\n''',
    '''    DashboardModuleDefinition(key=DashboardModuleKey.MONTHLY_HIGHLIGHTS, default_visible=True),\n    DashboardModuleDefinition(key=DashboardModuleKey.RECENT_SHARED, default_visible=True),\n    DashboardModuleDefinition(key=DashboardModuleKey.SHARED_STORY_SUMMARY, default_visible=True),\n)\n''',
)

contract_path = Path("web/src/client/dashboardModuleCatalog.contract.json")
contract = json.loads(contract_path.read_text(encoding="utf-8"))
keys = contract["moduleKeys"]
if keys[-1] != "recent_shared" or "shared_story_summary" in keys:
    raise RuntimeError(f"Unexpected Dashboard contract before #809 update: {keys}")
keys.append("shared_story_summary")
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

replace_once(
    "web/src/client/dashboardModules.ts",
    '''  | 'monthly_highlights'\n  | 'recent_shared';\n''',
    '''  | 'monthly_highlights'\n  | 'recent_shared'\n  | 'shared_story_summary';\n''',
)
replace_once(
    "web/src/client/dashboardModules.ts",
    ''' * `SHARED_STORY_SUMMARY` (#809) is deliberately absent: it is not merged to\n * `main`, and #817 does not implement #809 on its behalf.\n''',
    ''' * #809 appends `shared_story_summary` as the quiet final Today epilogue.\n''',
)
replace_once(
    "web/src/client/dashboardModules.ts",
    '''    { key: 'monthly_highlights', labelKey: 'm5s5.today.monthly.title' },\n    { key: 'recent_shared', labelKey: 'm5s5.dashboard.recentTitle' },\n  ];\n''',
    '''    { key: 'monthly_highlights', labelKey: 'm5s5.today.monthly.title' },\n    { key: 'recent_shared', labelKey: 'm5s5.dashboard.recentTitle' },\n    { key: 'shared_story_summary', labelKey: 'm5s5.dashboard.storySummaryTitle' },\n  ];\n''',
)

# ---------------------------------------------------------------------------
# Web: quiet editorial epilogue + sparse eligibility.
# ---------------------------------------------------------------------------
replace_once(
    "web/src/i18n/locales/m5s5.ts",
    '''    recentEmpty: 'Noch keine gemeinsamen Einträge vorhanden.',\n    itemFallback: 'Gemeinsamer Eintrag',\n''',
    '''    recentEmpty: 'Noch keine gemeinsamen Einträge vorhanden.',\n    storySummaryTitle: 'Eure Geschichte in Zahlen',\n    storySummaryMemories: 'Momente',\n    storySummaryHeartMoments: 'Herzmomente',\n    storySummaryMilestones: 'Meilensteine',\n    itemFallback: 'Gemeinsamer Eintrag',\n''',
)

write(
    "web/src/components/SharedStorySummary.tsx",
    '''import type { DashboardSharedStorySummary } from '../api/generated/models/DashboardSharedStorySummary';\nimport { resolvedLocale, useTranslation } from '../i18n';\nimport './SharedStorySummary.css';\n\ninterface SharedStorySummaryProps {\n  summary: DashboardSharedStorySummary;\n}\n\nexport function sharedStorySummaryIsEligible(\n  summary: DashboardSharedStorySummary,\n): boolean {\n  const values = [\n    summary.memories,\n    summary.heartMoments,\n    summary.milestones,\n  ].filter((value) => value > 0);\n  return (\n    values.length >= 2 &&\n    values.reduce((total, value) => total + value, 0) >= 5\n  );\n}\n\nexport function SharedStorySummary({ summary }: SharedStorySummaryProps) {\n  const { t } = useTranslation();\n  if (!sharedStorySummaryIsEligible(summary)) return null;\n\n  const numberFormat = new Intl.NumberFormat(resolvedLocale());\n  const metrics = [\n    {\n      key: 'memories',\n      label: t('m5s5.dashboard.storySummaryMemories'),\n      value: summary.memories,\n    },\n    {\n      key: 'heartMoments',\n      label: t('m5s5.dashboard.storySummaryHeartMoments'),\n      value: summary.heartMoments,\n    },\n    {\n      key: 'milestones',\n      label: t('m5s5.dashboard.storySummaryMilestones'),\n      value: summary.milestones,\n    },\n  ].filter((metric) => metric.value > 0);\n\n  return (\n    <section\n      className="shared-story-summary"\n      aria-labelledby="shared-story-summary-heading"\n    >\n      <h2 id="shared-story-summary-heading">\n        {t('m5s5.dashboard.storySummaryTitle')}\n      </h2>\n      <dl className="shared-story-summary-values">\n        {metrics.map((metric) => (\n          <div className="shared-story-summary-metric" key={metric.key}>\n            <dd>{numberFormat.format(metric.value)}</dd>\n            <dt>{metric.label}</dt>\n          </div>\n        ))}\n      </dl>\n    </section>\n  );\n}\n''',
)
write(
    "web/src/components/SharedStorySummary.css",
    '''.shared-story-summary {\n  margin: var(--space-2) 0 var(--space-8);\n  border-top: 1px solid var(--color-border-subtle);\n  padding: var(--space-6) 0 0;\n}\n\n.shared-story-summary h2 {\n  margin: 0 0 var(--space-5);\n  color: var(--color-text);\n  font-family: var(--font-display);\n  font-size: clamp(1.45rem, 3vw, 2rem);\n  font-weight: 750;\n  letter-spacing: -0.02em;\n}\n\n.shared-story-summary-values {\n  display: grid;\n  grid-template-columns: repeat(2, minmax(0, 1fr));\n  margin: 0;\n  gap: var(--space-5) var(--space-4);\n}\n\n.shared-story-summary-metric {\n  min-width: 0;\n}\n\n.shared-story-summary-metric dd,\n.shared-story-summary-metric dt {\n  margin: 0;\n}\n\n.shared-story-summary-metric dd {\n  color: var(--color-text);\n  font-family: var(--font-display);\n  font-size: clamp(2rem, 11vw, 3.25rem);\n  font-weight: 760;\n  line-height: 1;\n  letter-spacing: -0.04em;\n  overflow-wrap: anywhere;\n}\n\n.shared-story-summary-metric dt {\n  margin-top: var(--space-2);\n  color: var(--color-text-secondary);\n  font-size: 0.9rem;\n  font-weight: 650;\n  line-height: 1.35;\n}\n\n@media (min-width: 640px) {\n  .shared-story-summary-values {\n    grid-template-columns: repeat(3, minmax(0, 1fr));\n  }\n}\n''',
)
write(
    "web/src/components/SharedStorySummary.test.tsx",
    '''import { renderToStaticMarkup } from 'react-dom/server';\nimport m5s5 from '../i18n/locales/m5s5';\nimport {\n  SharedStorySummary,\n  sharedStorySummaryIsEligible,\n} from './SharedStorySummary';\n\ndescribe('SharedStorySummary', () => {\n  it('uses the ratified sparse threshold', () => {\n    expect(\n      sharedStorySummaryIsEligible({\n        memories: 4,\n        heartMoments: 1,\n        milestones: 0,\n      }),\n    ).toBe(true);\n    expect(\n      sharedStorySummaryIsEligible({\n        memories: 3,\n        heartMoments: 1,\n        milestones: 0,\n      }),\n    ).toBe(false);\n    expect(\n      sharedStorySummaryIsEligible({\n        memories: 20,\n        heartMoments: 0,\n        milestones: 0,\n      }),\n    ).toBe(false);\n  });\n\n  it('renders one editorial surface, omits zero metrics, and preserves metric order', () => {\n    const html = renderToStaticMarkup(\n      <SharedStorySummary\n        summary={{ memories: 4, heartMoments: 1, milestones: 0 }}\n      />,\n    );\n\n    expect(html).toContain(m5s5.dashboard.storySummaryTitle);\n    expect(html).toContain(m5s5.dashboard.storySummaryMemories);\n    expect(html).toContain(m5s5.dashboard.storySummaryHeartMoments);\n    expect(html).not.toContain(m5s5.dashboard.storySummaryMilestones);\n    expect(html.indexOf(m5s5.dashboard.storySummaryMemories)).toBeLessThan(\n      html.indexOf(m5s5.dashboard.storySummaryHeartMoments),\n    );\n    expect(html).toContain('<dl');\n    expect(html).not.toContain('button');\n  });\n});\n''',
)

replace_once(
    "web/src/components/TodayPage.tsx",
    "import { ProblemState } from './ProblemState';\n",
    "import { ProblemState } from './ProblemState';\nimport { SharedStorySummary } from './SharedStorySummary';\n",
)
replace_once(
    "web/src/components/TodayPage.tsx",
    '''  const recentSharedVisible = isDashboardModuleVisible(\n    dashboardPreferencesQuery.data,\n    'recent_shared',\n  );\n\n  const isSparse = Boolean(\n''',
    '''  const recentSharedVisible = isDashboardModuleVisible(\n    dashboardPreferencesQuery.data,\n    'recent_shared',\n  );\n  const sharedStorySummaryVisible = isDashboardModuleVisible(\n    dashboardPreferencesQuery.data,\n    'shared_story_summary',\n  );\n\n  const isSparse = Boolean(\n''',
)
replace_once(
    "web/src/components/TodayPage.tsx",
    '''            </>\n          )}\n        </div>\n''',
    '''              {sharedStorySummaryVisible ? (\n                <SharedStorySummary\n                  summary={dashboardQuery.data.sharedStorySummary}\n                />\n              ) : null}\n            </>\n          )}\n        </div>\n''',
)

# Browser/reflow fixture: ensure the new surface is genuinely exercised at 320 CSS px.
replace_once(
    "web/e2e/tests/product-reflow.spec.ts",
    "import de from '../../src/i18n/locales/de';\n",
    "import de from '../../src/i18n/locales/de';\nimport m5s5 from '../../src/i18n/locales/m5s5';\n",
)
replace_once(
    "web/e2e/tests/product-reflow.spec.ts",
    '''      await fulfillJson({\n        items: [{ moduleKey: 'upcoming', itemLimit: 2 }],\n      });\n''',
    '''      await fulfillJson({\n        items: [\n          { moduleKey: 'upcoming', visible: true, itemLimit: 2 },\n          { moduleKey: 'shared_story_summary', visible: true },\n        ],\n      });\n''',
)
replace_once(
    "web/e2e/tests/product-reflow.spec.ts",
    '''        retrospective: null,\n        recentShared: [],\n        upcoming: [\n''',
    '''        retrospective: null,\n        recentShared: [],\n        sharedStorySummary: {\n          memories: 4,\n          heartMoments: 1,\n          milestones: 0,\n        },\n        upcoming: [\n''',
)
replace_once(
    "web/e2e/tests/product-reflow.spec.ts",
    '''      await page.goto(path);\n      await expect(page.locator('#main-content')).toBeVisible();\n      await expectHorizontalReflow(page);\n    }\n''',
    '''      await page.goto(path);\n      await expect(page.locator('#main-content')).toBeVisible();\n      await expectHorizontalReflow(page);\n      if (path === '/today') {\n        await expect(\n          page.getByRole('heading', {\n            name: m5s5.dashboard.storySummaryTitle,\n            level: 2,\n          }),\n        ).toBeVisible();\n      }\n    }\n''',
)

# ---------------------------------------------------------------------------
# Backend acceptance coverage from the original #809 implementation, rebased
# onto the current Dashboard infrastructure.
# ---------------------------------------------------------------------------
write(
    "backend/tests/integration/test_dashboard_story_summary.py",
    '''"""Acceptance tests for #809 shared Story totals on the Dashboard."""\n\nfrom __future__ import annotations\n\nfrom datetime import date\n\nimport pytest\nfrom sqlalchemy.orm import Session\n\nfrom sidebyside.authorization import PrivacyClass\nfrom sidebyside.dashboard import service as dashboard_service\nfrom sidebyside.heart_moments.models import HeartEmotion, HeartMoment, HeartMomentPayload\nfrom sidebyside.memories.models import Memory, MemoryPayload\nfrom sidebyside.milestones.models import Milestone, MilestonePayload\nfrom sidebyside.relationship import service as relationship_service\nfrom tests.conftest import auth, make_account, make_space, requires_database, sign_in\n\npytestmark = [pytest.mark.integration, requires_database]\n\n\n@pytest.fixture\ndef couple(session: Session):  # type: ignore[no-untyped-def]\n    anna = make_account(session, "Anna")\n    ben = make_account(session, "Ben")\n    outsider = make_account(session, "Outsider")\n    space = make_space(session, anna)\n    relationship_service.add_member(session, space.id, ben)\n    foreign_space = make_space(session, outsider)\n    session.flush()\n    return {\n        "anna": anna,\n        "ben": ben,\n        "outsider": outsider,\n        "space": space,\n        "foreign_space": foreign_space,\n        "token_a": sign_in(session, anna),\n        "token_b": sign_in(session, ben),\n    }\n\n\ndef _get_dashboard(client, *, space_id, token):  # type: ignore[no-untyped-def]\n    return client.get(\n        f"/api/v1/spaces/{space_id}/dashboard",\n        headers=auth(token),\n    )\n\n\ndef test_shared_story_summary_is_identical_for_partners_and_excludes_private_and_foreign(\n    client,\n    session: Session,\n    couple,\n) -> None:  # type: ignore[no-untyped-def]\n    memories = [\n        Memory(\n            space_id=couple["space"].id,\n            owner_id=couple["anna"].id,\n            privacy_class=PrivacyClass.SPACE_SHARED.value,\n            happened_on=date(2026, 1, day),\n            payload=MemoryPayload(title=f"Memory {day}", body=""),\n        )\n        for day in (1, 2)\n    ]\n    shared_heart = HeartMoment(\n        space_id=couple["space"].id,\n        owner_id=couple["anna"].id,\n        privacy_class=PrivacyClass.SPACE_SHARED.value,\n        happened_on=date(2026, 2, 1),\n        payload=HeartMomentPayload(text="Shared", emotion=HeartEmotion.LOVED),\n    )\n    private_heart = HeartMoment(\n        space_id=couple["space"].id,\n        owner_id=couple["anna"].id,\n        privacy_class=PrivacyClass.OWNER_ONLY.value,\n        happened_on=date(2026, 2, 2),\n        payload=HeartMomentPayload(text="Private", emotion=HeartEmotion.GRATEFUL),\n    )\n    milestone = Milestone(\n        space_id=couple["space"].id,\n        owner_id=couple["ben"].id,\n        privacy_class=PrivacyClass.SPACE_SHARED.value,\n        happened_on=date(2026, 3, 1),\n        payload=MilestonePayload(title="Milestone"),\n    )\n    foreign_memory = Memory(\n        space_id=couple["foreign_space"].id,\n        owner_id=couple["outsider"].id,\n        privacy_class=PrivacyClass.SPACE_SHARED.value,\n        happened_on=date(2026, 4, 1),\n        payload=MemoryPayload(title="Foreign", body=""),\n    )\n    session.add_all([*memories, shared_heart, private_heart, milestone, foreign_memory])\n    session.flush()\n\n    expected = {"memories": 2, "heartMoments": 1, "milestones": 1}\n    anna = _get_dashboard(client, space_id=couple["space"].id, token=couple["token_a"])\n    ben = _get_dashboard(client, space_id=couple["space"].id, token=couple["token_b"])\n\n    assert anna.status_code == 200, anna.text\n    assert ben.status_code == 200, ben.text\n    assert anna.json()["sharedStorySummary"] == expected\n    assert ben.json()["sharedStorySummary"] == expected\n\n    shared_heart.privacy_class = PrivacyClass.OWNER_ONLY.value\n    session.flush()\n    after_private = _get_dashboard(\n        client,\n        space_id=couple["space"].id,\n        token=couple["token_a"],\n    )\n    assert after_private.status_code == 200\n    assert after_private.json()["sharedStorySummary"]["heartMoments"] == 0\n\n    shared_heart.privacy_class = PrivacyClass.SPACE_SHARED.value\n    session.delete(memories[0])\n    session.flush()\n    after_delete = _get_dashboard(client, space_id=couple["space"].id, token=couple["token_b"])\n    assert after_delete.status_code == 200\n    assert after_delete.json()["sharedStorySummary"] == {\n        "memories": 1,\n        "heartMoments": 1,\n        "milestones": 1,\n    }\n\n\ndef test_shared_story_summary_is_not_bounded_by_dashboard_section_limit(\n    client,\n    session: Session,\n    couple,\n) -> None:  # type: ignore[no-untyped-def]\n    total = dashboard_service.SECTION_LIMIT + 5\n    for index in range(total):\n        session.add(\n            Memory(\n                space_id=couple["space"].id,\n                owner_id=couple["anna"].id,\n                privacy_class=PrivacyClass.SPACE_SHARED.value,\n                happened_on=date(2026, 5, 1),\n                payload=MemoryPayload(title=f"Memory {index}", body=""),\n            )\n        )\n    session.flush()\n\n    response = _get_dashboard(client, space_id=couple["space"].id, token=couple["token_a"])\n    assert response.status_code == 200, response.text\n    body = response.json()\n    assert body["sharedStorySummary"] == {\n        "memories": total,\n        "heartMoments": 0,\n        "milestones": 0,\n    }\n    assert len(body["recentShared"]) <= dashboard_service.SECTION_LIMIT\n''',
)
