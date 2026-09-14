from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one anchor, found {count}: {old[:100]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# #929's exhaustive Today visibility fixture must make the new #809 module
# eligible and give it a stable section marker.
replace_once(
    "web/src/components/TodayPage.test.tsx",
    """        retrospective: {
          id: 'heart-signal',
          type: 'HEART_MOMENT',
          titleOrText: 'Weisst du noch',
          occurredOn: new Date('2020-01-01T00:00:00Z'),
        },
      };
""",
    """        retrospective: {
          id: 'heart-signal',
          type: 'HEART_MOMENT',
          titleOrText: 'Weisst du noch',
          occurredOn: new Date('2020-01-01T00:00:00Z'),
        },
        sharedStorySummary: {
          memories: 4,
          heartMoments: 1,
          milestones: 0,
        },
      };
""",
)
replace_once(
    "web/src/components/TodayPage.test.tsx",
    """      monthly_highlights: 'today-section-monthly',
      recent_shared: 'today-section-recent',
    };
""",
    """      monthly_highlights: 'today-section-monthly',
      recent_shared: 'today-section-recent',
      shared_story_summary: 'shared-story-summary',
    };
""",
)

# The server always emits the new aggregate, but tolerate a missing field in
# stale in-memory data during a rolling deployment instead of crashing Today.
replace_once(
    "web/src/components/TodayPage.tsx",
    """              {sharedStorySummaryVisible ? (
                <SharedStorySummary
                  summary={dashboardQuery.data.sharedStorySummary}
                />
              ) : null}
""",
    """              {sharedStorySummaryVisible &&
              dashboardQuery.data.sharedStorySummary ? (
                <SharedStorySummary
                  summary={dashboardQuery.data.sharedStorySummary}
                />
              ) : null}
""",
)

# #809 is the seventh accepted module, appended after the #850 composition.
replace_once(
    "web/src/client/dashboardModules.test.ts",
    """      'monthly_highlights',
      'recent_shared',
    ]);
""",
    """      'monthly_highlights',
      'recent_shared',
      'shared_story_summary',
    ]);
""",
)
replace_once(
    "web/src/client/dashboardModules.test.ts",
    "registers the currently accepted #850 Today modules in deterministic order",
    "registers the accepted #850 Today modules plus the #809 epilogue in deterministic order",
)

# Today uses the exact product title; Settings uses the shorter accepted
# module label from #809's PO decision.
replace_once(
    "web/src/client/dashboardModules.ts",
    "{ key: 'shared_story_summary', labelKey: 'm5s5.dashboard.storySummaryTitle' },",
    "{ key: 'shared_story_summary', labelKey: 'profileIdentity.dashboardStorySummaryTitle' },",
)
replace_once(
    "web/src/i18n/locales/profileIdentity.ts",
    """  dashboardModuleSaving: 'Wird gespeichert …',
  dashboardModuleSaved: '✓ Gespeichert',
  dashboardUpcomingTitle: 'Demnächst',
""",
    """  dashboardModuleSaving: 'Wird gespeichert …',
  dashboardModuleSaved: '✓ Gespeichert',
  dashboardStorySummaryTitle: 'Geschichte in Zahlen',
  dashboardUpcomingTitle: 'Demnächst',
""",
)

# Generated DashboardView gains one required aggregate. Keep the existing
# Android test constructors/wire fixtures in sync without adding Android UI.
for path, old, new in [
    (
        "android/app/src/test/java/de/sidebyside/next/cache/ProductReadCacheViewModelTest.kt",
        """            retrospective = null,
            space = DashboardSpaceSummary(partner = null, spaceId = spaceId),
""",
        """            retrospective = null,
            sharedStorySummary = sidebyside.api.models.DashboardSharedStorySummary(heartMoments = 0, memories = 0, milestones = 0),
            space = DashboardSpaceSummary(partner = null, spaceId = spaceId),
""",
    ),
    (
        "android/app/src/test/java/de/sidebyside/next/reference/SpaceContextTest.kt",
        """            retrospective = null,
            space = DashboardSpaceSummary(partner = null, spaceId = spaceId),
""",
        """            retrospective = null,
            sharedStorySummary = sidebyside.api.models.DashboardSharedStorySummary(heartMoments = 0, memories = 0, milestones = 0),
            space = DashboardSpaceSummary(partner = null, spaceId = spaceId),
""",
    ),
    (
        "android/app/src/test/java/de/sidebyside/next/today/TodayScreenSemanticsTest.kt",
        """            retrospective = retrospective,
            space = DashboardSpaceSummary(partner = partner, spaceId = UUID.randomUUID()),
""",
        """            retrospective = retrospective,
            sharedStorySummary = sidebyside.api.models.DashboardSharedStorySummary(heartMoments = 0, memories = 0, milestones = 0),
            space = DashboardSpaceSummary(partner = partner, spaceId = UUID.randomUUID()),
""",
    ),
    (
        "android/app/src/test/java/de/sidebyside/next/today/TodayTest.kt",
        """    retrospective = null,
    space = DashboardSpaceSummary(partner = null, spaceId = SPACE),
""",
        """    retrospective = null,
    sharedStorySummary = sidebyside.api.models.DashboardSharedStorySummary(heartMoments = 0, memories = 0, milestones = 0),
    space = DashboardSpaceSummary(partner = null, spaceId = SPACE),
""",
    ),
]:
    replace_once(path, old, new)

wire_path = Path(
    "android/app/src/test/java/de/sidebyside/next/reference/DashboardViewWireCompatibilityTest.kt"
)
wire = wire_path.read_text(encoding="utf-8")
wire_anchor = '''              "retrospective": null,
              "space": {
'''
wire_replacement = '''              "retrospective": null,
              "sharedStorySummary": {
                "heartMoments": 0,
                "memories": 0,
                "milestones": 0
              },
              "space": {
'''
if wire.count(wire_anchor) != 2:
    raise RuntimeError(
        f"DashboardViewWireCompatibilityTest.kt: expected two payload anchors, found {wire.count(wire_anchor)}"
    )
wire_path.write_text(
    wire.replace(wire_anchor, wire_replacement), encoding="utf-8", newline="\n"
)
