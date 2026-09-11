#!/usr/bin/env python3
from pathlib import Path

path = Path("android/app/src/test/java/de/sidebyside/next/plan/PlanScreenTest.kt")
content = path.read_text()
old = '''        composeRule.onNodeWithText("A weekend away").performClick()
        composeRule.onNodeWithText(
            context.getString(R.string.plan_scheduled_for, expected),
        ).assertExists()
'''
new = '''        composeRule.onNodeWithText("A weekend away").performClick()
        composeRule.onAllNodesWithText(
            context.getString(R.string.plan_scheduled_for, expected),
        ).assertCountEquals(2)
'''
count = content.count(old)
if count != 1:
    raise RuntimeError(f"date-only opened-plan assertion: expected one match, found {count}")
path.write_text(content.replace(old, new, 1))
