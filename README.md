# PawPal+ (Module 2 Project)

**PawPal+** is a pet care planner built with Python and Streamlit. A busy owner enters their pets, each pet's care tasks (walks, feeding, meds, enrichment, grooming), and how much time they have today. PawPal+ builds a daily schedule that fits that time, puts the most important tasks first, respects tasks that must happen at a set time, warns about clashes, and explains every choice it made.

## ✨ Features

**Scheduling algorithms** (all in [`pawpal_system.py`](pawpal_system.py)):

- **Priority-first ordering:** tasks are ranked high → medium → low, and shorter tasks go first within the same priority, so the most important work claims the day's time first (`Scheduler.sort_tasks()`).
- **Time budget:** a greedy pass keeps each task that still fits in the owner's available minutes and lists the rest as skipped. A long task that doesn't fit never blocks shorter tasks behind it (`Scheduler.fit_to_budget()`).
- **Set times and flexible slotting:** a task with a set time (e.g. meds at 08:00) keeps it. Flexible tasks are placed back to back from the start of the day and jump past any set-time task they would run into (`Scheduler.generate_plan()`).
- **Sorting by time:** lists tasks in clock order, with untimed tasks last and ties in the order they were added (`Scheduler.sort_by_time()`).
- **Filtering:** shows one pet's tasks, unfinished or finished tasks, or both combined (`Scheduler.filter_tasks()`).
- **Conflict warnings:** finds every pair of planned tasks whose time ranges overlap, including partial overlaps, and says whether they're for the same pet or two different pets. Conflicts are flagged, never silently moved (`Scheduler.detect_conflicts()`).
- **Daily and weekly recurrence:** completing a repeating task adds its next copy, due tomorrow (daily) or in 7 days (weekly). One-time tasks just stay done (`Task.next_occurrence()`, `Pet.complete_task()`).
- **Due-date-aware planning:** only tasks due today or earlier are planned, so overdue tasks are caught up and next week's copy doesn't show up today (`Scheduler.collect_tasks()`).
- **Plan explanation:** a plain-English summary of minutes used, why tasks are in that order, what was skipped, and any conflicts (`Scheduler.explain_plan()`).
- **Input checks:** invalid durations, priorities, frequencies, times, and duplicate pet names are rejected with a clear message, and a failed edit leaves the task unchanged.

**Streamlit app** ([`app.py`](app.py)): owner and pet setup, a task form, a filterable and sortable task table, one-click task completion, and a schedule view with summary numbers, conflict warnings, a skipped-task table, and a "Why this plan?" explanation.

## 🚀 Getting started

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

| Command | What it does |
|---------|--------------|
| `streamlit run app.py` | Opens the interactive app in your browser |
| `python main.py` | Runs a scripted demo in the terminal (see the sample output below) |
| `python -m pytest` | Runs the test suite |

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

### What you can do in the app

Start the app with `streamlit run app.py`. The page runs top to bottom:

| Section | What you can do |
|---------|-----------------|
| **Owner** | Set your name and how many minutes you have for pet care today. |
| **Add a Pet** | Add a pet with a name, species (dog, cat, other), and age. The pet table shows how many tasks each pet has. A duplicate name shows an error. |
| **Tasks** | Add a task for any pet: description, duration, priority, frequency (daily, weekly, once), category, and an optional set time. |
| **Current tasks** | View every task in one table. Filter it by pet and by status (All, To do, Done), and sort it by time of day or by priority. Each row shows the set time (or "flexible"), the due date, and whether it's done. |
| **Mark a task done** | Pick an unfinished task and mark it done. For a daily or weekly task, a message confirms that the next copy was added and when it's due. |
| **Build Schedule** | Choose when your day starts and click **Generate schedule**. |

The schedule view shows:

- **Summary numbers:** tasks scheduled, minutes used out of minutes available, and the number of conflicts.
- **The plan table** in start-time order, with start, end, task, pet, duration, priority, and whether the time was set by you or chosen by the scheduler.
- **Conflict warnings:** one yellow warning per overlapping pair, or a green "No time conflicts" message.
- **Skipped tasks:** a table of tasks that didn't fit in the time available.
- **Why this plan?:** an expandable section with the full explanation from `explain_plan()`.

### Example workflow

1. **Set up the owner.** Enter "Jordan" with **60** minutes available.
2. **Add two pets:** Mochi (dog, 3) and Luna (cat, 5).
3. **Add four tasks:**

   | Pet | Task | Duration | Priority | Frequency | Set time |
   |-----|------|----------|----------|-----------|----------|
   | Mochi | Morning walk | 30 min | high | daily | 08:00 |
   | Luna | Give medication | 5 min | high | daily | 08:10 |
   | Luna | Feather toy play | 40 min | medium | daily | none |
   | Mochi | Brush coat | 10 min | low | weekly | none |

4. **Browse the task list.** Set **Show pet** to Luna to see only Luna's two tasks ("Showing 2 of 4 tasks"). Switch **Sort by** to Priority to see the high-priority tasks first.
5. **Generate the schedule** with the day starting at 08:00. The result:

   | Start | End | Task | Pet | Timing |
   |-------|-----|------|-----|--------|
   | 08:00 | 08:30 | Morning walk | Mochi | set time |
   | 08:10 | 08:15 | Give medication | Luna | set time |
   | 08:30 | 08:40 | Brush coat | Mochi | flexible |

   The summary shows **3** tasks scheduled, **45 / 60** minutes used, and **1** conflict.
6. **Read the warnings.**
   - *Conflict:* "'Morning walk' (08:00-08:30) overlaps 'Give medication' (08:10-08:15), Mochi and Luna." Both tasks stay in the plan, and you decide whether to move one.
   - *Skipped:* Feather toy play (40 min) didn't fit. The two high-priority tasks used 35 minutes first, leaving 25.
7. **Mark "Brush coat" done.** The app confirms that the next weekly copy was added, due 7 days later. It appears in the task list but stays out of today's schedule.

### Key scheduler behaviors in this example

- **Priority first:** Feather toy play (medium, 40 min) was skipped and Brush coat (low, 10 min) was kept. The high-priority tasks claimed time first, and the greedy budget still fit the short task after the long one was skipped.
- **Flexible slotting:** Brush coat would have started at 08:00, the start of the day. Instead it moved to 08:30, right after the walk.
- **Conflict detection across pets:** the set-time walk and medication overlap, and the warning names both pets.
- **Sorted output:** the plan is in start-time order, whatever order the tasks were added in.
- **Recurrence:** completing a weekly task schedules its next copy instead of losing it.

### Sample CLI output (`python main.py`)

`main.py` builds one owner (Jordan, 120 minutes available) and two pets (Mochi the dog and Luna the cat). It adds their tasks out of time order, including two clashes on purpose. Then it completes a daily, a weekly, and a one-time task, prints sorted and filtered task lists, and ends with the conflict check and today's plan. An excerpt (the dates depend on the day you run it):

```
==================================================
Recurring Tasks
==================================================
  Completed 'Clean litter box' (Luna); next daily copy due 2026-11-07.
  Completed 'Brush coat' (Mochi); next weekly copy due 2026-11-13.
  Completed 'Vet checkup' (Luna); it does not repeat.

==================================================
Sorting and Filtering
==================================================

Sorted by time:
--------------------------------------------------
  07:30  Breakfast          Mochi  daily   due 2026-11-06  [todo]
  07:35  Puzzle feeder      Mochi  daily   due 2026-11-06  [todo]
  08:00  Morning walk       Mochi  daily   due 2026-11-06  [todo]
  08:00  Give medication    Luna   daily   due 2026-11-06  [todo]
  17:30  Dinner             Luna   daily   due 2026-11-06  [todo]
  18:00  Evening walk       Mochi  daily   due 2026-11-06  [todo]
  --:--  Brush coat         Mochi  weekly  due 2026-11-06  [done]
  ...

Mochi's tasks still to do, sorted by time:
--------------------------------------------------
  07:30  Breakfast          Mochi  daily   due 2026-11-06  [todo]
  07:35  Puzzle feeder      Mochi  daily   due 2026-11-06  [todo]
  08:00  Morning walk       Mochi  daily   due 2026-11-06  [todo]
  18:00  Evening walk       Mochi  daily   due 2026-11-06  [todo]
  --:--  Brush coat         Mochi  weekly  due 2026-11-13  [todo]

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
Warnings (fixed times that overlap):
  Conflict: 'Breakfast' (07:30-07:40) overlaps 'Puzzle feeder' (07:35-07:50), both for Mochi.
  Conflict: 'Give medication' (08:00-08:05) overlaps 'Morning walk' (08:00-08:30), Luna and Mochi.
(Tasks completed today and copies due on later days are left out.)
```

## 🗂️ Architecture

The final class design is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd). `Owner` holds `Pet`s, each `Pet` holds its `Task`s, and `Scheduler` reads from the `Owner` to build, check, and explain the day's plan. The Phase 1 draft is kept in [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd) for comparison.
