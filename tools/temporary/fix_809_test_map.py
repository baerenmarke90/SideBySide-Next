from pathlib import Path

path = Path("web/src/components/TodayPage.test.tsx")
text = path.read_text(encoding="utf-8")

old_dashboard = """        retrospective: {
          id: 'heart-signal',
          type: 'HEART_MOMENT',
          titleOrText: 'Weisst du noch',
          occurredOn: new Date('2020-01-01T00:00:00Z'),
        },
      };
"""
new_dashboard = """        retrospective: {
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
"""
if text.count(old_dashboard) != 1:
    raise RuntimeError("Expected one allModulesEligibleDashboard anchor")
text = text.replace(old_dashboard, new_dashboard, 1)

old_map = """      monthly_highlights: 'today-section-monthly',
      recent_shared: 'today-section-recent',
    };
"""
new_map = """      monthly_highlights: 'today-section-monthly',
      recent_shared: 'today-section-recent',
      shared_story_summary: 'shared-story-summary',
    };
"""
if text.count(old_map) != 1:
    raise RuntimeError("Expected one MODULE_SECTION_MARKER anchor")
path.write_text(text.replace(old_map, new_map, 1), encoding="utf-8", newline="\n")
