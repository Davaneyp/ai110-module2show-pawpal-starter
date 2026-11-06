"""Tests for the PawPal+ core classes and scheduler."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

# A fixed day so results never depend on when the tests run.
TODAY = date(2026, 3, 2)


def make_owner(minutes=240, *pets):
    """Return an owner with the given time budget and pets."""
    owner = Owner(name="Jordan", available_minutes=minutes)
    for pet in pets:
        owner.add_pet(pet)
    return owner


# --- Basics ---------------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, priority="high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Breakfast", 10, priority="high"))

    assert len(pet.get_tasks()) == 1


# --- Sorting --------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    tasks = [
        Task("Dinner", 10, time="18:00"),
        Task("Breakfast", 10, time="07:30"),
        Task("Lunch", 10, time="12:15"),
    ]
    scheduler = Scheduler(make_owner())

    result = scheduler.sort_by_time(tasks)

    assert [t.time for t in result] == ["07:30", "12:15", "18:00"]


def test_sort_by_time_puts_untimed_last_and_keeps_input_unchanged():
    untimed = Task("Brush", 5)
    late = Task("Meds", 5, time="20:00")
    early = Task("Walk", 30, time="06:00")
    tasks = [untimed, late, early]
    scheduler = Scheduler(make_owner())

    result = scheduler.sort_by_time(tasks)

    assert result == [early, late, untimed]
    assert tasks == [untimed, late, early]


def test_sort_by_time_keeps_original_order_on_ties():
    first = Task("Feed Mochi", 10, time="08:00")
    second = Task("Feed Rex", 10, time="08:00")
    scheduler = Scheduler(make_owner())

    assert scheduler.sort_by_time([first, second]) == [first, second]


def test_sort_tasks_orders_by_priority_then_shortest():
    low = Task("Play", 5, priority="low")
    high_long = Task("Walk", 30, priority="high")
    high_short = Task("Meds", 5, priority="high")
    medium = Task("Brush", 10, priority="medium")
    scheduler = Scheduler(make_owner())

    result = scheduler.sort_tasks([low, high_long, medium, high_short])

    assert result == [high_short, high_long, medium, low]


def test_sort_handles_empty_list():
    scheduler = Scheduler(make_owner())
    assert scheduler.sort_by_time([]) == []
    assert scheduler.sort_tasks([]) == []


def test_generate_plan_is_in_start_time_order():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Dinner", 10, time="18:00", due_date=TODAY))
    pet.add_task(Task("Walk", 30, priority="high", due_date=TODAY))
    pet.add_task(Task("Meds", 5, time="08:10", due_date=TODAY))
    scheduler = Scheduler(make_owner(240, pet), day_start="08:00", plan_date=TODAY)

    plan = scheduler.generate_plan()

    starts = [start for start, _ in plan]
    assert starts == sorted(starts)


# --- Recurrence -----------------------------------------------------------

def test_completing_daily_task_creates_task_for_next_day():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, frequency="daily", due_date=TODAY))

    next_task = pet.complete_task("Walk", today=TODAY)

    assert next_task is not None
    assert next_task.due_date == TODAY + timedelta(days=1)
    assert next_task.completed is False
    assert next_task.description == "Walk"
    # The finished task stays as history alongside the new one.
    assert len(pet.tasks) == 2
    assert pet.tasks[0].completed is True


def test_completing_weekly_task_creates_task_one_week_later():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Bath", 20, frequency="weekly", due_date=TODAY))

    next_task = pet.complete_task("Bath", today=TODAY)

    assert next_task.due_date == TODAY + timedelta(weeks=1)


def test_completing_one_time_task_adds_nothing():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Vet visit", 60, frequency="once", due_date=TODAY))

    assert pet.complete_task("Vet visit", today=TODAY) is None
    assert len(pet.tasks) == 1


def test_task_finished_early_counts_from_its_due_date():
    future = TODAY + timedelta(days=3)
    task = Task("Walk", 30, frequency="daily", due_date=future)

    assert task.next_occurrence(today=TODAY).due_date == future + timedelta(days=1)


def test_overdue_task_counts_from_today():
    task = Task("Walk", 30, frequency="daily", due_date=TODAY - timedelta(days=3))

    assert task.next_occurrence(today=TODAY).due_date == TODAY + timedelta(days=1)


def test_complete_task_matches_case_insensitively():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Morning Walk", 30, due_date=TODAY))

    pet.complete_task("morning walk", today=TODAY)

    assert pet.tasks[0].completed is True


def test_complete_unknown_task_raises():
    pet = Pet("Mochi", "dog")
    with pytest.raises(ValueError):
        pet.complete_task("Nope", today=TODAY)


def test_scheduler_complete_task_uses_plan_date():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, due_date=TODAY))
    scheduler = Scheduler(make_owner(240, pet), plan_date=TODAY)

    next_task = scheduler.complete_task("mochi", "Walk")

    assert next_task.due_date == TODAY + timedelta(days=1)


def test_next_occurrence_is_not_in_todays_plan():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, due_date=TODAY))
    scheduler = Scheduler(make_owner(240, pet), plan_date=TODAY)

    scheduler.complete_task("Mochi", "Walk")

    assert scheduler.generate_plan() == []


# --- Conflict detection ---------------------------------------------------

def test_duplicate_times_are_flagged():
    mochi = Pet("Mochi", "dog")
    rex = Pet("Rex", "dog")
    mochi.add_task(Task("Feed Mochi", 10, time="08:00", due_date=TODAY))
    rex.add_task(Task("Feed Rex", 10, time="08:00", due_date=TODAY))
    scheduler = Scheduler(make_owner(240, mochi, rex), plan_date=TODAY)

    scheduler.generate_plan()

    assert len(scheduler.conflicts) == 1
    assert "Feed Mochi" in scheduler.conflicts[0]
    assert "Feed Rex" in scheduler.conflicts[0]
    assert "Mochi and Rex" in scheduler.conflicts[0]


def test_same_pet_conflict_says_both_for_pet():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, time="09:00", due_date=TODAY))
    pet.add_task(Task("Meds", 5, time="09:00", due_date=TODAY))
    scheduler = Scheduler(make_owner(240, pet), plan_date=TODAY)

    scheduler.generate_plan()

    assert len(scheduler.conflicts) == 1
    assert "both for Mochi" in scheduler.conflicts[0]


def test_partial_overlap_is_flagged():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, time="09:00", due_date=TODAY))
    pet.add_task(Task("Training", 30, time="09:15", due_date=TODAY))
    scheduler = Scheduler(make_owner(240, pet), plan_date=TODAY)

    scheduler.generate_plan()

    assert len(scheduler.conflicts) == 1


def test_back_to_back_tasks_do_not_conflict():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, time="09:00", due_date=TODAY))
    pet.add_task(Task("Training", 30, time="09:30", due_date=TODAY))
    scheduler = Scheduler(make_owner(240, pet), plan_date=TODAY)

    scheduler.generate_plan()

    assert scheduler.conflicts == []


def test_flexible_task_slides_past_fixed_task():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Vet call", 30, time="08:00", due_date=TODAY))
    pet.add_task(Task("Walk", 20, due_date=TODAY))
    scheduler = Scheduler(make_owner(240, pet), day_start="08:00", plan_date=TODAY)

    plan = scheduler.generate_plan()

    assert ("08:30", pet.tasks[1]) in plan
    assert scheduler.conflicts == []


# --- Time budget ----------------------------------------------------------

def test_task_that_exactly_fills_budget_is_kept():
    scheduler = Scheduler(make_owner(30))
    task = Task("Walk", 30)

    assert scheduler.fit_to_budget([task]) == [task]
    assert scheduler.skipped == []


def test_greedy_budget_skips_long_task_but_fits_shorter_one():
    long_task = Task("Hike", 40, priority="high")
    short_task = Task("Play", 20, priority="low")
    scheduler = Scheduler(make_owner(30))

    kept = scheduler.fit_to_budget([long_task, short_task])

    assert kept == [short_task]
    assert scheduler.skipped == [long_task]


def test_zero_budget_skips_everything():
    scheduler = Scheduler(make_owner(0))
    tasks = [Task("Walk", 30), Task("Meds", 5)]

    assert scheduler.fit_to_budget(tasks) == []
    assert scheduler.skipped == tasks


def test_collect_tasks_skips_completed_and_future_but_keeps_overdue():
    pet = Pet("Mochi", "dog")
    overdue = Task("Overdue", 10, due_date=TODAY - timedelta(days=1))
    done = Task("Done", 10, due_date=TODAY, completed=True)
    future = Task("Future", 10, due_date=TODAY + timedelta(days=1))
    for task in (overdue, done, future):
        pet.add_task(task)
    scheduler = Scheduler(make_owner(240, pet), plan_date=TODAY)

    assert scheduler.collect_tasks() == [overdue]


def test_explain_plan_with_no_tasks():
    scheduler = Scheduler(make_owner(), plan_date=TODAY)
    scheduler.generate_plan()

    assert scheduler.explain_plan() == "No tasks to schedule."


# --- Validation -----------------------------------------------------------

@pytest.mark.parametrize("kwargs", [
    {"duration_minutes": 0},
    {"priority": "urgent"},
    {"frequency": "monthly"},
    {"time": "8:05"},
    {"time": "25:00"},
])
def test_invalid_task_fields_raise(kwargs):
    fields = {"description": "Walk", "duration_minutes": 30, **kwargs}
    with pytest.raises(ValueError):
        Task(**fields)


def test_failed_edit_restores_old_values():
    task = Task("Walk", 30, priority="high")

    with pytest.raises(ValueError):
        task.edit(description="Long walk", priority="urgent")

    assert task.description == "Walk"
    assert task.priority == "high"


def test_duplicate_pet_name_raises():
    owner = make_owner(240, Pet("Mochi", "dog"))
    with pytest.raises(ValueError):
        owner.add_pet(Pet("mochi", "cat"))


# --- Known bug ------------------------------------------------------------

@pytest.mark.xfail(reason="flexible tasks past midnight wrap to '00:xx' and sort to the top")
def test_plan_past_midnight_stays_in_order():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 60, priority="high", due_date=TODAY))
    pet.add_task(Task("Play", 60, priority="low", due_date=TODAY))
    scheduler = Scheduler(make_owner(240, pet), day_start="23:00", plan_date=TODAY)

    plan = scheduler.generate_plan()

    assert [task.description for _, task in plan] == ["Walk", "Play"]
