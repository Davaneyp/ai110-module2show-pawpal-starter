# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

`python main.py` builds one owner (Jordan, with 120 minutes available) and two pets (Mochi the dog and Luna the cat). It adds their care tasks out of time order, including two that clash on purpose. It then completes a daily, a weekly, and a one-time task, prints sorted and filtered task lists, and finishes with the conflict check and today's plan. An excerpt (the dates depend on the day you run it):

```
==================================================
Recurring Tasks
==================================================
  Completed 'Clean litter box' (Luna); next daily copy due 2026-11-07.
  Completed 'Brush coat' (Mochi); next weekly copy due 2026-11-13.
  Completed 'Vet checkup' (Luna); it does not repeat.

...

==================================================
Conflict Check
==================================================
  WARNING: Conflict: 'Breakfast' (07:30-07:40) overlaps 'Puzzle feeder' (07:35-07:50), both for Mochi.
  WARNING: Conflict: 'Give medication' (08:00-08:05) overlaps 'Morning walk' (08:00-08:30), Luna and Mochi.

==================================================
Today's Schedule
==================================================
Daily plan for Jordan (115 of 120 minutes used):
  07:30 - Breakfast for Mochi (10 min) [priority: high]
  07:35 - Puzzle feeder for Mochi (15 min) [priority: medium]
  08:00 - Give medication for Luna (5 min) [priority: high]
  08:00 - Morning walk for Mochi (30 min) [priority: high]
  08:30 - Feather toy play for Luna (20 min) [priority: medium]
  17:30 - Dinner for Luna (5 min) [priority: high]
  18:00 - Evening walk for Mochi (30 min) [priority: high]
Tasks with a set time keep it; the rest fill the open gaps by priority (high first), then shorter tasks first.
Skipped (not enough time left):
  Nail trim for Luna (25 min) [priority: low]
...
```

## 🧪 Testing PawPal+

Run the full test suite from the project folder:

```bash
python -m pytest
```

The tests live in [`tests/test_pawpal.py`](tests/test_pawpal.py). Every test uses a fixed date, so results don't depend on the day you run them. They cover:

- **Sorting:** `sort_by_time()` returns tasks in clock order, puts untimed tasks last, keeps ties in their original order, and leaves the input list unchanged. `sort_tasks()` orders by priority, then shortest first. The finished plan is in start-time order.
- **Recurring tasks:** completing a daily task adds a copy due the next day, a weekly task adds one due 7 days later, and a one-time task adds nothing. Tasks finished early count from their due date and overdue tasks count from today. The finished task stays as history, and the next copy doesn't show up in today's plan.
- **Conflict detection:** two tasks at the same time are flagged, for the same pet ("both for Mochi") or different pets ("Mochi and Rex"). Partial overlaps are flagged, back-to-back tasks are not, and flexible tasks move to just after a fixed task instead of clashing with it.
- **Time budget and planning:** a task that exactly fills the remaining time is kept, a zero budget skips everything, and a long task that doesn't fit doesn't block shorter tasks after it. Completed and future tasks are left out of the plan; overdue tasks are included.
- **Input checks:** bad durations, priorities, frequencies, and times raise `ValueError`. A failed `edit()` puts the old values back, and duplicate pet names are rejected.

Sample test output:

```
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Light\OneDrive\Documents\GitHub\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 35 items

tests\test_pawpal.py ..................................x                 [100%]

======================== 34 passed, 1 xfailed in 0.08s ========================
```

The one `x` is an expected failure (`xfail`) that records a known bug. If a plan runs past midnight, a flexible task's start time wraps to `"00:xx"` and sorts to the top of the plan. The test will start passing once `generate_plan()` handles that case.

**Confidence Level: ★★★★☆ (4/5)**

All the core behaviors (sorting, recurring tasks, conflict detection, and the time budget) pass, including their edge cases. I'm holding back one star for the known midnight bug, and because the Streamlit UI in `app.py` isn't covered by automated tests.

## 📐 Smarter Scheduling

All of the scheduling logic lives in [`pawpal_system.py`](pawpal_system.py).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_tasks()` | By clock time (untimed tasks last); by priority, then shortest first |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.fit_to_budget()` | By pet and/or completion status; drops tasks that don't fit the owner's time |
| Conflict handling | `Scheduler.detect_conflicts()` | Warns about overlapping time slots, for the same pet or different pets |
| Recurring tasks | `Task.next_occurrence()`, `Pet.complete_task()`, `Scheduler.complete_task()` | Completing a daily or weekly task adds the next copy with a new due date |

### Sorting by time: `Scheduler.sort_by_time(tasks)`

Returns the tasks in clock order. Each `Task` can have an optional fixed start time, `time` (`"HH:MM"`). The sort key is a lambda:

```python
sorted(tasks, key=lambda t: (t.time is None, t.time or ""))
```

- Zero-padded `"HH:MM"` strings sort in clock order as plain strings, so there's no time parsing. `Task` rejects times like `"8:00"` that would break this.
- The first part of the key puts tasks with a time before tasks without one (`False` sorts before `True`).
- Tasks with the same time keep the order they were added.

`Scheduler.sort_tasks()` is the other sort. It orders tasks by priority (high first), then by duration (shortest first), and decides which tasks claim the owner's time first.

### Filtering: `Scheduler.filter_tasks(pet_name=None, completed=None)`

Returns the owner's tasks for one pet, one completion status, or both. `None` means "don't filter on this":

```python
scheduler.filter_tasks(pet_name="Luna")                    # all of Luna's tasks
scheduler.filter_tasks(completed=False)                    # everything still to do
scheduler.filter_tasks(pet_name="Mochi", completed=False)  # Mochi's unfinished tasks
```

Pet names match regardless of capitalization. Filters combine with sorting, e.g. `scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi"))`.

`Scheduler.fit_to_budget()` is a separate time-budget filter used when planning. Going in priority order, it keeps each task that still fits in `available_minutes` and records the rest in `scheduler.skipped`. A long task that doesn't fit doesn't block shorter tasks after it.

### Building the plan: `Scheduler.generate_plan()`

1. Collect tasks that aren't done and are due today or earlier (`collect_tasks()`).
2. Sort them by priority (`sort_tasks()`) and keep the ones that fit the time budget (`fit_to_budget()`).
3. Tasks with a fixed `time` keep it. Flexible tasks are placed back to back from `day_start` in priority order, jumping past any fixed task they would overlap.
4. Sort the plan by start time and run the conflict check.

The plan is stored as `(start_time, task)` pairs in `scheduler.plan`. The tasks themselves are not changed.

### Conflict detection: `Scheduler.detect_conflicts()`

Finds every pair of planned tasks whose time ranges overlap and returns a list of warning messages. `generate_plan()` saves them to `scheduler.conflicts`, `explain_plan()` prints them, and the Streamlit app shows them as warnings.

- **Overlap, not just same start time.** Each task covers `start` to `start + duration`. Two tasks conflict when one starts before the other ends, so a 07:35 task that runs into a 07:30–07:40 task is caught. Back-to-back tasks (one ends at 08:30, the next starts at 08:30) are not conflicts.
- **Same pet or different pets.** Each warning says which: `both for Mochi` or `Luna and Mochi`.
- **Simple and fast.** The plan is already sorted by start time, so each task is compared only with the tasks after it, stopping at the first one that starts after it ends.
- **Warns but never crashes or rearranges.** Clashing tasks both stay in the plan and the owner decides what to do. Feeding two pets at once may be fine, while moving a medication time on its own would not be. Only fixed-time tasks can conflict, because flexible tasks are placed around them.

### Recurring tasks: `Task.next_occurrence()` and `complete_task()`

Each `Task` has a `due_date` (default: today) and a `frequency` of `"once"`, `"daily"`, or `"weekly"`.

- **`Scheduler.complete_task(pet_name, description)`** (or `Pet.complete_task(description)`) marks the first unfinished matching task as done. If it repeats, a new copy of it is added to the pet, and the method returns that copy.
- **`Task.next_occurrence()`** builds that copy, not done and with a new due date:
  - daily: today + `timedelta(days=1)`
  - weekly: today + `timedelta(weeks=1)`
  - once: no copy (`None`)
- If a task is finished early (before its due date), the next copy counts from its due date instead of today, so two copies are never due on the same day.
- `collect_tasks()` only plans tasks due on or before the plan date (`Scheduler(..., plan_date=...)`, default today). The new copy shows up on the right day, not today.
- Finished tasks stay in the pet's list as history, so `filter_tasks(completed=True)` still finds them.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
