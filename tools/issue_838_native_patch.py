#!/usr/bin/env python3
"""Temporary branch-only patcher for #838 large native/Web files.

The GitHub connector can safely replace small files, but replacing the complete
large Kotlin view model/sheet sources by hand is unnecessarily risky. This
script applies count-checked textual transformations in the repository runner.
It is removed again before #838 leaves draft state.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def write(path: str, content: str) -> None:
    (ROOT / path).write_text(content)


def replace_once(content: str, old: str, new: str, *, label: str) -> str:
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one exact match, found {count}")
    return content.replace(old, new, 1)


def replace_all_exact(content: str, old: str, new: str, *, count: int, label: str) -> str:
    actual = content.count(old)
    if actual != count:
        raise RuntimeError(f"{label}: expected {count} matches, found {actual}")
    return content.replace(old, new)


def sub_once(content: str, pattern: str, replacement: str, *, label: str) -> str:
    result, count = re.subn(pattern, replacement, content, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"{label}: expected one regex match, found {count}")
    return result


def patch_web_today() -> None:
    path = "web/src/components/TodayPage.tsx"
    content = read(path)
    content = replace_once(
        content,
        "import { formatRecency, formatUpcomingRelative } from '../client/formatRecency';",
        "import {\n  formatRecency,\n  formatUpcomingCalendarDate,\n  formatUpcomingRelative,\n} from '../client/formatRecency';",
        label="TodayPage import",
    )
    content = replace_once(
        content,
        "  const rawDate = item.occurredOn ?? item.scheduledAt ?? item.createdAt;\n"
        "  const date = rawDate ? formatUpcomingRelative(rawDate, t) : null;\n",
        "  const rawDate = item.occurredOn ?? item.scheduledAt ?? item.createdAt;\n"
        "  const date = item.scheduledOn\n"
        "    ? formatUpcomingCalendarDate(item.scheduledOn, t)\n"
        "    : rawDate\n"
        "      ? formatUpcomingRelative(rawDate, t)\n"
        "      : null;\n",
        label="TodayAgendaRow date selection",
    )
    write(path, content)


def patch_android_today() -> None:
    path = "android/app/src/main/java/de/sidebyside/next/today/TodayScreen.kt"
    content = read(path)
    old = (
        "    val day = item.scheduledAt?.atZoneSameInstant(ZoneId.systemDefault())?.toLocalDate()\n"
        "        ?: item.occurredOn\n"
    )
    new = (
        "    val day = item.scheduledOn\n"
        "        ?: item.scheduledAt?.atZoneSameInstant(ZoneId.systemDefault())?.toLocalDate()\n"
        "        ?: item.occurredOn\n"
    )
    content = replace_all_exact(
        content,
        old,
        new,
        count=2,
        label="Android Today calendar day",
    )
    write(path, content)


def patch_plan_screen() -> None:
    path = "android/app/src/main/java/de/sidebyside/next/plan/PlanScreen.kt"
    content = read(path)
    content = replace_once(
        content,
        "import java.util.UUID\n",
        "import java.time.Instant\nimport java.time.LocalDate\nimport java.time.ZoneId\nimport java.util.UUID\n",
        label="PlanScreen time imports",
    )
    content = replace_all_exact(
        content,
        "    onSchedule: (id: UUID, startOn: String, startAt: String) -> Unit,\n",
        "    onSchedule: (id: UUID, startOn: String, startAt: String?) -> Unit,\n",
        count=2,
        label="PlanScreen nullable schedule time",
    )
    content = replace_once(
        content,
        "    // The one plan that is actually coming up. It leads the screen and is not\n"
        "    // repeated in the stack below.\n"
        "    val focal = plans\n"
        "        .filter { it.status == PlanStatus.PLANNED && it.plannedStart != null }\n"
        "        .minByOrNull { it.plannedStart!! }\n"
        "    val remainingPlans = plans.filter { it.id != focal?.id }\n",
        "    // The one plan that is actually coming up. Date-only schedules compare as\n"
        "    // calendar days; timed schedules retain real instant ordering. No synthetic\n"
        "    // wall-clock value is created for a date-only Plan.\n"
        "    val today = LocalDate.now()\n"
        "    val now = Instant.now()\n"
        "    val focal = plans\n"
        "        .filter { plan ->\n"
        "            plan.status == PlanStatus.PLANNED && when {\n"
        "                plan.plannedOn != null -> !plan.plannedOn!!.isBefore(today)\n"
        "                plan.plannedStart != null -> !plan.plannedStart!!.toInstant().isBefore(now)\n"
        "                else -> false\n"
        "            }\n"
        "        }\n"
        "        .minWithOrNull(\n"
        "            Comparator { left, right ->\n"
        "                val leftDay = left.plannedOn\n"
        "                    ?: left.plannedStart!!.atZoneSameInstant(ZoneId.systemDefault()).toLocalDate()\n"
        "                val rightDay = right.plannedOn\n"
        "                    ?: right.plannedStart!!.atZoneSameInstant(ZoneId.systemDefault()).toLocalDate()\n"
        "                val dayOrder = leftDay.compareTo(rightDay)\n"
        "                if (dayOrder != 0) {\n"
        "                    dayOrder\n"
        "                } else if ((left.plannedOn != null) != (right.plannedOn != null)) {\n"
        "                    if (left.plannedOn != null) -1 else 1\n"
        "                } else if (left.plannedStart != null && right.plannedStart != null) {\n"
        "                    left.plannedStart!!.toInstant().compareTo(right.plannedStart!!.toInstant())\n"
        "                } else {\n"
        "                    left.id.toString().compareTo(right.id.toString())\n"
        "                }\n"
        "            },\n"
        "        )\n"
        "    val remainingPlans = plans.filter { it.id != focal?.id }\n",
        label="PlanScreen focal scheduling",
    )
    write(path, content)


def patch_planning_sheets() -> None:
    path = "android/app/src/main/java/de/sidebyside/next/plan/PlanningSheets.kt"
    content = read(path)

    content = replace_once(
        content,
        " * [allowSchedule] adds a day/time section next to `Mehr dazu`, so a couple\n"
        " * who already knows when never has to leave this sheet, reopen the new plan\n"
        " * and find the schedule action a second time. A day alone does not schedule\n"
        " * anything — [SheetPrimaryAction] below only turns on time picking once a day\n"
        " * is chosen, and submitting still works with neither set.\n",
        " * [allowSchedule] adds a date-first scheduling section next to `Mehr dazu`, so\n"
        " * a couple who already knows the day never has to reopen the new plan. Time is\n"
        " * deliberately optional: a selected day is a complete date-only schedule, and\n"
        " * no wall-clock value is invented when the time remains absent.\n",
        label="PlanFields documentation",
    )

    content = replace_once(
        content,
        "    // A day the couple picked is never sent on its own — `PlanSchedule` needs\n"
        "    // a time to go with it — so submit stays off between choosing the day and\n"
        "    // confirming a time rather than quietly dropping the day they already\n"
        "    // chose.\n"
        "    val scheduleReady = day == null || time != null\n"
        "    SheetPrimaryAction(submitLabelRes, enabled = !busy && title.isNotBlank() && scheduleReady) {\n"
        "        onSubmit(title, description, placeId, day, time)\n"
        "    }\n",
        "    SheetPrimaryAction(submitLabelRes, enabled = !busy && title.isNotBlank()) {\n"
        "        onSubmit(title, description, placeId, day, time)\n"
        "    }\n",
        label="PlanFields date-only submit",
    )

    # Add explicit clearing semantics to the create/conversion scheduling block.
    content = replace_once(
        content,
        "            PickerRow(\n"
        "                labelRes = R.string.plan_schedule_day,\n"
        "                value = day?.let { formattedDate(LocalDate.parse(it)) },\n"
        "                placeholderRes = R.string.plan_schedule_pick_day,\n"
        "                enabled = !busy,\n"
        "                onClick = { dayPickerOpen = true },\n"
        "            )\n"
        "            if (day != null) {\n"
        "                PickerRow(\n"
        "                    labelRes = R.string.plan_schedule_time,\n"
        "                    value = time,\n"
        "                    placeholderRes = R.string.plan_schedule_pick_time,\n"
        "                    enabled = !busy,\n"
        "                    onClick = { timePickerOpen = true },\n"
        "                )\n"
        "            }\n",
        "            PickerRow(\n"
        "                labelRes = R.string.plan_schedule_day,\n"
        "                value = day?.let { formattedDate(LocalDate.parse(it)) },\n"
        "                placeholderRes = R.string.plan_schedule_pick_day,\n"
        "                enabled = !busy,\n"
        "                onClick = { dayPickerOpen = true },\n"
        "            )\n"
        "            if (day != null) {\n"
        "                SheetSecondaryAction(R.string.plan_schedule_clear_date, enabled = !busy) {\n"
        "                    day = null\n"
        "                    time = null\n"
        "                }\n"
        "                PickerRow(\n"
        "                    labelRes = R.string.plan_schedule_time_optional,\n"
        "                    value = time,\n"
        "                    placeholderRes = R.string.plan_schedule_pick_time,\n"
        "                    enabled = !busy,\n"
        "                    onClick = { timePickerOpen = true },\n"
        "                )\n"
        "                if (time != null) {\n"
        "                    SheetSecondaryAction(R.string.plan_schedule_clear_time, enabled = !busy) {\n"
        "                        time = null\n"
        "                    }\n"
        "                }\n"
        "            }\n",
        label="PlanFields clear schedule controls",
    )

    content = replace_once(
        content,
        "    onSubmit: (startOn: String, startAt: String) -> Unit,\n",
        "    onSubmit: (startOn: String, startAt: String?) -> Unit,\n",
        label="PlanScheduleSheet nullable time",
    )
    content = replace_once(
        content,
        "    val existing = plan.plannedStart?.atZoneSameInstant(ZoneId.systemDefault())\n"
        "    val suggestedDay = existing?.toLocalDate() ?: LocalDate.now()\n"
        "    val suggestedTime = existing?.toLocalTime()?.withSecond(0)?.withNano(0)\n"
        "        ?: LocalTime.of(19, 0)\n\n"
        "    var day by rememberSaveable(plan.id) { mutableStateOf<String?>(null) }\n"
        "    var time by rememberSaveable(plan.id) { mutableStateOf<String?>(null) }\n",
        "    val existing = plan.plannedStart?.atZoneSameInstant(ZoneId.systemDefault())\n"
        "    val suggestedDay = plan.plannedOn ?: existing?.toLocalDate() ?: LocalDate.now()\n"
        "    val suggestedTime = existing?.toLocalTime()?.withSecond(0)?.withNano(0)\n"
        "        ?: LocalTime.of(19, 0)\n\n"
        "    var day by rememberSaveable(plan.id) {\n"
        "        mutableStateOf((plan.plannedOn ?: existing?.toLocalDate())?.toString())\n"
        "    }\n"
        "    var time by rememberSaveable(plan.id) {\n"
        "        mutableStateOf(existing?.toLocalTime()?.withSecond(0)?.withNano(0)?.toString())\n"
        "    }\n",
        label="PlanScheduleSheet initial semantic state",
    )
    content = replace_once(
        content,
        "        PickerRow(\n"
        "            labelRes = R.string.plan_schedule_day,\n"
        "            value = day?.let { formattedDate(LocalDate.parse(it)) },\n"
        "            placeholderRes = R.string.plan_schedule_pick_day,\n"
        "            enabled = !busy,\n"
        "            onClick = { dayPickerOpen = true },\n"
        "        )\n"
        "        PickerRow(\n"
        "            labelRes = R.string.plan_schedule_time,\n"
        "            value = time,\n"
        "            placeholderRes = R.string.plan_schedule_pick_time,\n"
        "            enabled = !busy,\n"
        "            onClick = { timePickerOpen = true },\n"
        "        )\n"
        "        SheetPrimaryAction(\n"
        "            R.string.plan_schedule_confirm,\n"
        "            enabled = !busy && day != null && time != null,\n"
        "        ) {\n"
        "            onSubmit(day!!, time!!)\n"
        "        }\n",
        "        PickerRow(\n"
        "            labelRes = R.string.plan_schedule_day,\n"
        "            value = day?.let { formattedDate(LocalDate.parse(it)) },\n"
        "            placeholderRes = R.string.plan_schedule_pick_day,\n"
        "            enabled = !busy,\n"
        "            onClick = { dayPickerOpen = true },\n"
        "        )\n"
        "        if (day != null) {\n"
        "            SheetSecondaryAction(R.string.plan_schedule_clear_date, enabled = !busy) {\n"
        "                day = null\n"
        "                time = null\n"
        "            }\n"
        "        }\n"
        "        PickerRow(\n"
        "            labelRes = R.string.plan_schedule_time_optional,\n"
        "            value = time,\n"
        "            placeholderRes = R.string.plan_schedule_pick_time,\n"
        "            enabled = !busy && day != null,\n"
        "            onClick = { timePickerOpen = true },\n"
        "        )\n"
        "        if (time != null) {\n"
        "            SheetSecondaryAction(R.string.plan_schedule_clear_time, enabled = !busy) {\n"
        "                time = null\n"
        "            }\n"
        "        }\n"
        "        SheetPrimaryAction(\n"
        "            R.string.plan_schedule_confirm_optional,\n"
        "            enabled = !busy && day != null,\n"
        "        ) {\n"
        "            onSubmit(day!!, time)\n"
        "        }\n",
        label="PlanScheduleSheet optional time controls",
    )
    content = replace_once(
        content,
        "    val suggested = plan.plannedStart\n"
        "        ?.atZoneSameInstant(ZoneId.systemDefault())\n"
        "        ?.toLocalDate()\n"
        "        ?.takeIf { !it.isAfter(today) }\n"
        "        ?: today\n",
        "    val suggested = (plan.plannedOn\n"
        "        ?: plan.plannedStart\n"
        "            ?.atZoneSameInstant(ZoneId.systemDefault())\n"
        "            ?.toLocalDate())\n"
        "        ?.takeIf { !it.isAfter(today) }\n"
        "        ?: today\n",
        label="PlanComplete date-only suggestion",
    )
    write(path, content)


def patch_reference_view_model() -> None:
    path = "android/app/src/main/java/de/sidebyside/next/reference/ReferenceViewModel.kt"
    content = read(path)

    # Both create flows already carry date/time state. Make that schedule part
    # of the create/convert DTO itself, then delete the follow-up schedule call.
    content = replace_once(
        content,
        "                WishToPlan(\n"
        "                    description = description.takeIf { it.isNotBlank() },\n"
        "                    placeId = placeId,\n"
        "                    title = title.ifBlank { wish.title },\n"
        "                ),\n",
        "                WishToPlan(\n"
        "                    description = description.takeIf { it.isNotBlank() },\n"
        "                    placeId = placeId,\n"
        "                    schedule = planSchedule(startOn, startAt),\n"
        "                    title = title.ifBlank { wish.title },\n"
        "                ),\n",
        label="WishToPlan atomic schedule",
    )
    content = replace_once(
        content,
        "            scheduleNewPlan(api, spaceId, token, response.plan, startOn, startAt)\n",
        "",
        label="remove Wish follow-up schedule",
    )
    content = replace_once(
        content,
        "                PlanCreate(\n"
        "                    title = title,\n"
        "                    description = description.trim().takeIf { it.isNotBlank() },\n"
        "                    placeId = placeId,\n"
        "                ),\n",
        "                PlanCreate(\n"
        "                    title = title,\n"
        "                    description = description.trim().takeIf { it.isNotBlank() },\n"
        "                    placeId = placeId,\n"
        "                    schedule = planSchedule(startOn, startAt),\n"
        "                ),\n",
        label="PlanCreate atomic schedule",
    )
    content = replace_once(
        content,
        "            scheduleNewPlan(api, spaceId, token, plan, startOn, startAt)\n",
        "",
        label="remove direct Plan follow-up schedule",
    )

    content = sub_once(
        content,
        r"    /\*\*\n     \* `PlanSchedule\.plannedStart` is a moment, not a date,.*?"
        r"    private suspend fun scheduleNewPlan\(.*?"
        r"        api\.schedulePlan\(spaceId, token, plan\.id, plan\.version, PlanSchedule\(plannedStart = start\)\)\n"
        r"    \}\n",
        "    /** Build a schedule without inventing a wall-clock value for a lone day. */\n"
        "    private fun planSchedule(startOn: String?, startAt: String?): PlanSchedule? {\n"
        "        val day = startOn?.let { parseHappenedOn(it) } ?: return null\n"
        "        if (startAt.isNullOrBlank()) return PlanSchedule(plannedOn = day)\n"
        "        val time = runCatching { java.time.LocalTime.parse(startAt) }.getOrNull() ?: return null\n"
        "        return PlanSchedule(\n"
        "            plannedStart = planScheduleStart(day, time, java.time.ZoneId.systemDefault()),\n"
        "        )\n"
        "    }\n",
        label="replace scheduleNewPlan helper",
    )

    content = sub_once(
        content,
        r"    /\*\*\n     \* `IDEA -> PLANNED`\. \[startOn\].*?"
        r"    fun schedulePlan\(planId: java\.util\.UUID, startOn: String, startAt: String\) \{.*?"
        r"    \}\n\n    fun unschedulePlan",
        "    /** Schedule by calendar day, optionally refined by a real local time. */\n"
        "    fun schedulePlan(planId: java.util.UUID, startOn: String, startAt: String?) {\n"
        "        val schedule = planSchedule(startOn, startAt) ?: return\n"
        "        val plan = _uiState.value.plans.firstOrNull { it.id == planId } ?: return\n"
        "        planningCall { api, spaceId, token ->\n"
        "            api.schedulePlan(spaceId, token, plan.id, plan.version, schedule)\n"
        "        }\n"
        "    }\n\n"
        "    fun unschedulePlan",
        label="ViewModel nullable schedule time",
    )
    write(path, content)


def main() -> None:
    patch_web_today()
    patch_android_today()
    patch_plan_screen()
    patch_planning_sheets()
    patch_reference_view_model()
    print("#838 native/Web parity patch applied")


if __name__ == "__main__":
    main()
