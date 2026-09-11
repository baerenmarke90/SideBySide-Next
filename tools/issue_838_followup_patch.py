#!/usr/bin/env python3
"""Temporary branch-only follow-up patcher for #838 Android acceptance coverage."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = ROOT / path
    content = target.read_text()
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one exact match, found {count}")
    target.write_text(content.replace(old, new, 1))


def sub_once(path: str, pattern: str, replacement: str, label: str) -> None:
    target = ROOT / path
    content = target.read_text()
    updated, count = re.subn(pattern, replacement, content, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"{label}: expected one regex match, found {count}")
    target.write_text(updated)


def patch_plan_presentation_surfaces() -> None:
    replace_once(
        "android/app/src/main/java/de/sidebyside/next/plan/PlanScreen.kt",
        "            plan.plannedStart?.let { start ->\n"
        "                Text(\n"
        "                    text = stringResource(R.string.plan_scheduled_for, formattedDateTime(start)),\n"
        "                    style = MaterialTheme.typography.bodyMedium,\n"
        "                    color = SideBySideTheme.colors.textSecondary,\n"
        "                )\n"
        "            }\n",
        "            planTimingLine(plan)?.let { line ->\n"
        "                Text(\n"
        "                    text = line,\n"
        "                    style = MaterialTheme.typography.bodyMedium,\n"
        "                    color = SideBySideTheme.colors.textSecondary,\n"
        "                )\n"
        "            }\n",
        "FocalPlanCard date-only timing",
    )
    replace_once(
        "android/app/src/main/java/de/sidebyside/next/plan/PlanningSheets.kt",
        "        plan.plannedStart?.let { start ->\n"
        "            Text(\n"
        "                text = stringResource(R.string.plan_scheduled_for, formattedDateTime(start)),\n"
        "                style = MaterialTheme.typography.bodySmall,\n"
        "                color = SideBySideTheme.colors.textSecondary,\n"
        "            )\n"
        "        }\n"
        "        plan.experiencedOn?.let { day ->\n"
        "            Text(\n"
        "                text = stringResource(R.string.plan_experienced_on, formattedDate(day)),\n"
        "                style = MaterialTheme.typography.bodySmall,\n"
        "                color = SideBySideTheme.colors.textSecondary,\n"
        "            )\n"
        "        }\n",
        "        planTimingLine(plan)?.let { line ->\n"
        "            Text(\n"
        "                text = line,\n"
        "                style = MaterialTheme.typography.bodySmall,\n"
        "                color = SideBySideTheme.colors.textSecondary,\n"
        "            )\n"
        "        }\n",
        "PlanSheet shared timing presentation",
    )


def patch_plan_screen_tests() -> None:
    path = "android/app/src/test/java/de/sidebyside/next/plan/PlanScreenTest.kt"
    sub_once(
        path,
        r"    @Test\n    fun wishToPlanCannotSubmitADayWithoutATimeToGoWithIt\(\) \{.*?\n    \}\n\n    @Test\n    fun newPlaceCanBeCreatedInlineDuringWishToPlanConversion",
        "    @Test\n"
        "    fun wishToPlanCanSubmitADayWithoutATime() {\n"
        "        val wish = aWish(\"A weekend by the sea\")\n"
        "        var planned: Pair<String?, String?>? = null\n"
        "        render(\n"
        "            wishes = listOf(wish),\n"
        "            onPlanWish = { _, _, _, _, startOn, startAt -> planned = startOn to startAt },\n"
        "        )\n\n"
        "        composeRule.onNodeWithText(\"A weekend by the sea\").performScrollTo().performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan)).performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_schedule))\n"
        "            .performScrollTo()\n"
        "            .performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_pick_day))\n"
        "            .performScrollTo()\n"
        "            .performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_picker_take)).performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_wish_make_plan_confirm))\n"
        "            .performScrollTo()\n"
        "            .assertIsEnabled()\n"
        "            .performClick()\n\n"
        "        assertEquals(LocalDate.now().toString() to null, planned)\n"
        "    }\n\n"
        "    @Test\n"
        "    fun newPlaceCanBeCreatedInlineDuringWishToPlanConversion",
        "Wish-to-Plan date-only acceptance test",
    )
    sub_once(
        path,
        r"    @Test\n    fun schedulingPicksADayAndATimeBeforeItCanBeConfirmed\(\) \{.*?\n    \}\n\n    @Test\n    fun scheduledPlanShowsThePersistedLocalDateAndTime",
        "    @Test\n"
        "    fun schedulingAcceptsADayWithoutRequiringATime() {\n"
        "        val plan = aPlan(PlanStatus.IDEA, title = \"A weekend away\")\n"
        "        var scheduled: Triple<UUID, String, String?>? = null\n"
        "        render(\n"
        "            plans = listOf(plan),\n"
        "            onSchedule = { id, startOn, startAt -> scheduled = Triple(id, startOn, startAt) },\n"
        "        )\n\n"
        "        composeRule.onNodeWithText(\"A weekend away\").performScrollTo().performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_schedule)).performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_confirm_optional))\n"
        "            .assertIsNotEnabled()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_pick_day))\n"
        "            .performScrollTo()\n"
        "            .performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_picker_take)).performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_confirm_optional))\n"
        "            .performScrollTo()\n"
        "            .assertIsEnabled()\n"
        "            .performClick()\n\n"
        "        assertEquals(Triple(plan.id, LocalDate.now().toString(), null), scheduled)\n"
        "    }\n\n"
        "    @Test\n"
        "    fun schedulingCanStillAddATime() {\n"
        "        val plan = aPlan(PlanStatus.IDEA, title = \"A weekend away\")\n"
        "        var scheduled: Triple<UUID, String, String?>? = null\n"
        "        render(\n"
        "            plans = listOf(plan),\n"
        "            onSchedule = { id, startOn, startAt -> scheduled = Triple(id, startOn, startAt) },\n"
        "        )\n\n"
        "        composeRule.onNodeWithText(\"A weekend away\").performScrollTo().performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_schedule)).performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_pick_day))\n"
        "            .performScrollTo()\n"
        "            .performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_picker_take)).performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_pick_time))\n"
        "            .performScrollTo()\n"
        "            .performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_picker_take)).performClick()\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_schedule_confirm_optional))\n"
        "            .performScrollTo()\n"
        "            .performClick()\n\n"
        "        assertEquals(Triple(plan.id, LocalDate.now().toString(), \"19:00\"), scheduled)\n"
        "    }\n\n"
        "    @Test\n"
        "    fun scheduledPlanShowsThePersistedLocalDateAndTime",
        "Dedicated schedule date-only/timed tests",
    )
    replace_once(
        path,
        "        onSchedule: (UUID, String, String) -> Unit = { _, _, _ -> },\n",
        "        onSchedule: (UUID, String, String?) -> Unit = { _, _, _ -> },\n",
        "PlanScreen test nullable schedule callback",
    )
    marker = "    @Test\n    fun completingOffersTheDayReadyMadeAndRecordsIt() {"
    insertion = (
        "    @Test\n"
        "    fun dateOnlyScheduledPlanShowsThePersistedCalendarDate() {\n"
        "        val day = LocalDate.parse(\"2026-12-20\")\n"
        "        val plan = aPlan(PlanStatus.PLANNED, title = \"A weekend away\").copy(plannedOn = day)\n"
        "        val locale = context.resources.configuration.locales[0]\n"
        "        val expected = day.format(\n"
        "            DateTimeFormatter.ofLocalizedDate(FormatStyle.LONG).withLocale(locale),\n"
        "        )\n\n"
        "        render(plans = listOf(plan))\n\n"
        "        composeRule.onNodeWithText(context.getString(R.string.plan_focus_next)).assertExists()\n"
        "        composeRule.onNodeWithText(\n"
        "            context.getString(R.string.plan_scheduled_for, expected),\n"
        "        ).assertExists()\n"
        "        composeRule.onNodeWithText(\"A weekend away\").performClick()\n"
        "        composeRule.onNodeWithText(\n"
        "            context.getString(R.string.plan_scheduled_for, expected),\n"
        "        ).assertExists()\n"
        "    }\n\n"
        + marker
    )
    replace_once(path, marker, insertion, "date-only presentation test")


def main() -> None:
    patch_plan_presentation_surfaces()
    patch_plan_screen_tests()
    print("#838 Android acceptance follow-up applied")


if __name__ == "__main__":
    main()
