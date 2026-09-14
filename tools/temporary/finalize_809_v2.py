from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one anchor, found {count}: {old[:100]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# Keep the existing #817 catalog acceptance tests exhaustive now that #809 is
# the seventh registered Dashboard module.
replace_once(
    "backend/tests/integration/test_dashboard_preferences.py",
    '''        "monthly_highlights",\n        "recent_shared",\n    ]\n''',
    '''        "monthly_highlights",\n        "recent_shared",\n        "shared_story_summary",\n    ]\n''',
)
replace_once(
    "backend/tests/integration/test_dashboard_preferences.py",
    '''            {"moduleKey": "monthly_highlights", "visible": True},\n            {"moduleKey": "recent_shared", "visible": True},\n        ],\n''',
    '''            {"moduleKey": "monthly_highlights", "visible": True},\n            {"moduleKey": "recent_shared", "visible": True},\n            {"moduleKey": "shared_story_summary", "visible": True},\n        ],\n''',
)
replace_once(
    "backend/tests/integration/test_dashboard_preferences.py",
    '''        "monthly_highlights",\n        "recent_shared",\n    ],\n)\ndef test_item_limit_is_rejected_on_modules_that_do_not_support_it(\n''',
    '''        "monthly_highlights",\n        "recent_shared",\n        "shared_story_summary",\n    ],\n)\ndef test_item_limit_is_rejected_on_modules_that_do_not_support_it(\n''',
)

# The canonical Dashboard response contract test should assert the new
# authoritative aggregate and exact top-level response shape.
replace_once(
    "backend/tests/integration/test_dashboard.py",
    '''    assert body["retrospective"]["id"] == str(shared_heart.id)\n\n    visible_ids = {\n''',
    '''    assert body["retrospective"]["id"] == str(shared_heart.id)\n    assert body["sharedStorySummary"] == {\n        "memories": 0,\n        "heartMoments": 1,\n        "milestones": 0,\n    }\n\n    visible_ids = {\n''',
)
replace_once(
    "backend/tests/integration/test_dashboard.py",
    '''        "upcoming",\n        "recentShared",\n        "thinkingOfYouAvailableAt",\n''',
    '''        "upcoming",\n        "recentShared",\n        "sharedStorySummary",\n        "thinkingOfYouAvailableAt",\n''',
)

# Make the accepted placement a direct regression assertion: #809 is a quiet
# closing epilogue and must remain after the existing #850 recent trace.
replace_once(
    "web/src/components/TodayPage.test.tsx",
    '''      for (const [, sectionClass] of MODULE_SECTIONS) {\n        expect(html).toContain(sectionClass);\n      }\n    });\n''',
    '''      for (const [, sectionClass] of MODULE_SECTIONS) {\n        expect(html).toContain(sectionClass);\n      }\n      expect(html.indexOf('today-section-recent')).toBeLessThan(\n        html.indexOf('shared-story-summary'),\n      );\n    });\n''',
)

# Keep every Dashboard module label on the existing m5s5 registry path. This
# preserves the generic Settings test/helper and avoids a one-off #809 label
# resolver while still using the shorter accepted Settings copy.
replace_once(
    "web/src/client/dashboardModules.ts",
    "{ key: 'shared_story_summary', labelKey: 'profileIdentity.dashboardStorySummaryTitle' },",
    "{ key: 'shared_story_summary', labelKey: 'm5s5.dashboard.storySummarySettingsTitle' },",
)
replace_once(
    "web/src/i18n/locales/m5s5.ts",
    """    storySummaryTitle: 'Eure Geschichte in Zahlen',
    storySummaryMemories: 'Momente',
""",
    """    storySummaryTitle: 'Eure Geschichte in Zahlen',
    storySummarySettingsTitle: 'Geschichte in Zahlen',
    storySummaryMemories: 'Momente',
""",
)
replace_once(
    "web/src/i18n/locales/profileIdentity.ts",
    "  dashboardStorySummaryTitle: 'Geschichte in Zahlen',\n",
    "",
)
