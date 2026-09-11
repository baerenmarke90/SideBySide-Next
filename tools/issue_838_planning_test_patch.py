#!/usr/bin/env python3
"""Temporary branch-only patcher for #838 PlanningTest contract expectations."""

from pathlib import Path

PATH = Path("android/app/src/test/java/de/sidebyside/next/plan/PlanningTest.kt")


def replace_once(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return content.replace(old, new, 1)


def main() -> None:
    content = PATH.read_text()

    content = replace_once(
        content,
        '''        // Scheduled against the *plan* the conversion just returned, not the
        // wish's own version.
        assertEquals(listOf(1), api.scheduleVersions)
        val scheduledStart = api.schedules.single().plannedStart
        assertEquals(LocalDate.of(2026, 9, 20), scheduledStart.toLocalDate())
        assertEquals(LocalTime.of(18, 30), scheduledStart.toLocalTime())
    }

    @Test
    fun turningAWishIntoAPlanWithoutADateSchedulesNothing() = runTest(dispatcher) {
''',
        '''        // #838: the schedule is part of the conversion request itself. There
        // must be no follow-up schedule call that could leave a partial state.
        val schedule = requireNotNull(api.conversions.single().schedule)
        assertTrue(api.schedules.isEmpty())
        assertEquals(null, schedule.plannedOn)
        val scheduledStart = requireNotNull(schedule.plannedStart)
        assertEquals(LocalDate.of(2026, 9, 20), scheduledStart.toLocalDate())
        assertEquals(LocalTime.of(18, 30), scheduledStart.toLocalTime())
    }

    @Test
    fun turningAWishIntoAPlanCanCarryOnlyACalendarDay() = runTest(dispatcher) {
        val api = PlanningApi(wishes = listOf(aWish(OPEN_WISH, WishStatus.OPEN, version = 4)))
        val model = signedIn(api)

        model.loadPlanning()
        advanceUntilIdle()
        model.planWish(OPEN_WISH, "", "", null, "2026-09-20", null)
        advanceUntilIdle()

        val schedule = requireNotNull(api.conversions.single().schedule)
        assertEquals(LocalDate.of(2026, 9, 20), schedule.plannedOn)
        assertEquals(null, schedule.plannedStart)
        assertTrue(api.schedules.isEmpty())
    }

    @Test
    fun turningAWishIntoAPlanWithoutADateSchedulesNothing() = runTest(dispatcher) {
''',
        "wish conversion schedule contract",
    )

    content = replace_once(
        content,
        '''        assertTrue(api.schedules.isEmpty())
    }

    @Test
    fun editingAWishTitleUsesTheExistingUpdateCallAndVersion() = runTest(dispatcher) {
''',
        '''        assertEquals(null, api.conversions.single().schedule)
        assertTrue(api.schedules.isEmpty())
    }

    @Test
    fun editingAWishTitleUsesTheExistingUpdateCallAndVersion() = runTest(dispatcher) {
''',
        "unscheduled wish conversion contract",
    )

    content = replace_once(
        content,
        '''        assertEquals(listOf(1), api.scheduleVersions)
        val scheduledStart = api.schedules.single().plannedStart
        assertEquals(LocalDate.of(2026, 9, 20), scheduledStart.toLocalDate())
        assertEquals(LocalTime.of(18, 30), scheduledStart.toLocalTime())
    }

    @Test
    fun creatingAPlanDirectlyWithOnlyADayDoesNotScheduleAnything() = runTest(dispatcher) {
        // A day without a time is never sent — `PlanSchedule.plannedStart` is a
        // moment, not a date — so this must not schedule anything on its own,
        // even though the plan is still created.
        val api = PlanningApi()
        val model = signedIn(api)

        model.createPlan("A weekend away", "", null, "2026-09-20", null)
        advanceUntilIdle()

        assertEquals(1, api.directlyCreated.size)
        assertTrue(api.schedules.isEmpty())
    }
''',
        '''        val schedule = requireNotNull(api.directlyCreated.single().schedule)
        assertTrue(api.schedules.isEmpty())
        assertEquals(null, schedule.plannedOn)
        val scheduledStart = requireNotNull(schedule.plannedStart)
        assertEquals(LocalDate.of(2026, 9, 20), scheduledStart.toLocalDate())
        assertEquals(LocalTime.of(18, 30), scheduledStart.toLocalTime())
    }

    @Test
    fun creatingAPlanDirectlyWithOnlyADayCreatesADateOnlySchedule() = runTest(dispatcher) {
        val api = PlanningApi()
        val model = signedIn(api)

        model.createPlan("A weekend away", "", null, "2026-09-20", null)
        advanceUntilIdle()

        val schedule = requireNotNull(api.directlyCreated.single().schedule)
        assertEquals(LocalDate.of(2026, 9, 20), schedule.plannedOn)
        assertEquals(null, schedule.plannedStart)
        assertTrue(api.schedules.isEmpty())
    }
''',
        "direct create atomic/date-only schedule contract",
    )

    content = replace_once(
        content,
        '''        val scheduledStart = api.schedules.single().plannedStart
        assertEquals(LocalDate.of(2026, 9, 20), scheduledStart.toLocalDate())
        assertEquals(LocalTime.of(18, 30), scheduledStart.toLocalTime())
        assertTrue(api.completions.isEmpty())
''',
        '''        val schedule = api.schedules.single()
        assertEquals(null, schedule.plannedOn)
        val scheduledStart = requireNotNull(schedule.plannedStart)
        assertEquals(LocalDate.of(2026, 9, 20), scheduledStart.toLocalDate())
        assertEquals(LocalTime.of(18, 30), scheduledStart.toLocalTime())
        assertTrue(api.completions.isEmpty())
''',
        "dedicated timed schedule contract",
    )

    marker = '''    @Test
    fun schedulingAnUnparseableDateSendsNothing() = runTest(dispatcher) {
'''
    addition = '''    @Test
    fun schedulingWithOnlyADayUsesPlannedOn() = runTest(dispatcher) {
        val api = PlanningApi(plans = listOf(aPlan(PlanStatus.IDEA, version = 7)))
        val model = signedIn(api)

        model.loadPlanning()
        advanceUntilIdle()
        model.schedulePlan(PLAN, "2026-09-20", null)
        advanceUntilIdle()

        assertEquals(listOf(7), api.scheduleVersions)
        val schedule = api.schedules.single()
        assertEquals(LocalDate.of(2026, 9, 20), schedule.plannedOn)
        assertEquals(null, schedule.plannedStart)
    }

'''
    content = replace_once(content, marker, addition + marker, "date-only dedicated schedule test")

    PATH.write_text(content)
    print("#838 PlanningTest contract patch applied")


if __name__ == "__main__":
    main()
