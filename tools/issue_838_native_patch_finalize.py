#!/usr/bin/env python3
"""Temporary count-checked ReferenceViewModel patch stages for #838."""

from __future__ import annotations

from issue_838_native_patch import read, replace_once, sub_once, write

PATH = "android/app/src/main/java/de/sidebyside/next/reference/ReferenceViewModel.kt"


def _apply(transform) -> None:
    content = read(PATH)
    content = transform(content)
    write(PATH, content)


def patch_vm_wish_schedule_field() -> None:
    def transform(content: str) -> str:
        return replace_once(
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
    _apply(transform)


def patch_vm_remove_wish_followup() -> None:
    def transform(content: str) -> str:
        return replace_once(
            content,
            "            scheduleNewPlan(api, spaceId, token, response.plan, startOn, startAt)\n",
            "",
            label="remove Wish follow-up schedule",
        )
    _apply(transform)


def patch_vm_plan_schedule_field() -> None:
    def transform(content: str) -> str:
        return replace_once(
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
    _apply(transform)


def patch_vm_remove_plan_followup() -> None:
    def transform(content: str) -> str:
        return replace_once(
            content,
            "            scheduleNewPlan(api, spaceId, token, plan, startOn, startAt)\n",
            "",
            label="remove direct Plan follow-up schedule",
        )
    _apply(transform)


def patch_vm_schedule_helper() -> None:
    def transform(content: str) -> str:
        return sub_once(
            content,
            r"    private suspend fun scheduleNewPlan\(\n.*?"
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
    _apply(transform)


def patch_vm_public_schedule() -> None:
    def transform(content: str) -> str:
        return sub_once(
            content,
            r"    fun schedulePlan\(planId: java\.util\.UUID, startOn: String, startAt: String\) \{.*?"
            r"\n    \}\n\n    fun unschedulePlan",
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
    _apply(transform)


def patch_reference_view_model() -> None:
    patch_vm_wish_schedule_field()
    patch_vm_remove_wish_followup()
    patch_vm_plan_schedule_field()
    patch_vm_remove_plan_followup()
    patch_vm_schedule_helper()
    patch_vm_public_schedule()


if __name__ == "__main__":
    patch_reference_view_model()
