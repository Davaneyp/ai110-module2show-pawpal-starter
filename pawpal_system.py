"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta

PRIORITY_VALUES = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")
REPEAT_INTERVALS = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


@dataclass
class Task:
    """A single pet care activity, such as a walk or feeding."""

    description: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    frequency: str = "daily"  # "once", "daily", or "weekly"
    category: str = "general"  # e.g. "walk", "feeding", "meds", "enrichment", "grooming"
    time: str | None = None  # fixed start time ("HH:MM"), or None to let the Scheduler pick
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Check the task's fields right after it is created."""
        self._validate()

    def _validate(self) -> None:
        """Raise ValueError if any field has an invalid value."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than 0")
        if self.priority not in PRIORITY_VALUES:
            raise ValueError(f"priority must be one of {list(PRIORITY_VALUES)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")
        if self.time is not None:
            # Require zero-padded "HH:MM" so times sort correctly as plain strings.
            try:
                valid = datetime.strptime(self.time, "%H:%M").strftime("%H:%M") == self.time
            except ValueError:
                valid = False
            if not valid:
                raise ValueError("time must be in zero-padded HH:MM format, e.g. '08:05'")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def reset(self) -> None:
        """Mark this task as not done."""
        self.completed = False

    def next_occurrence(self, today: date | None = None) -> Task | None:
        """Return a fresh copy of this task due next time, or None for a one-time task.

        A daily task is due today + 1 day and a weekly task today + 7 days. If this task
        was finished early (due after today), count from its due date instead so the next
        copy never lands on a day this one already covers.
        """
        if self.frequency not in REPEAT_INTERVALS:
            return None
        base = max(today or date.today(), self.due_date)
        return replace(self, completed=False, due_date=base + REPEAT_INTERVALS[self.frequency])

    def priority_value(self) -> int:
        """Return a number for the priority (low=1, medium=2, high=3) for sorting."""
        return PRIORITY_VALUES[self.priority]

    def edit(
        self,
        description: str | None = None,
        duration_minutes: int | None = None,
        priority: str | None = None,
        frequency: str | None = None,
        category: str | None = None,
    ) -> None:
        """Update any of the given fields, leaving the others unchanged."""
        old = (self.description, self.duration_minutes, self.priority, self.frequency, self.category)
        if description is not None:
            self.description = description
        if duration_minutes is not None:
            self.duration_minutes = duration_minutes
        if priority is not None:
            self.priority = priority
        if frequency is not None:
            self.frequency = frequency
        if category is not None:
            self.category = category
        try:
            self._validate()
        except ValueError:
            # Undo the changes so the task is never left in an invalid state.
            (self.description, self.duration_minutes, self.priority,
             self.frequency, self.category) = old
            raise


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str  # "dog", "cat", or "other"
    age: int = 0
    special_needs: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> None:
        """Remove the task with the given description."""
        task = self.find_task(description)
        if task is None:
            raise ValueError(f"{self.name} has no task named '{description}'")
        self.tasks.remove(task)

    def find_task(self, description: str) -> Task | None:
        """Return the task with the given description, or None if there isn't one."""
        for task in self.tasks:
            if task.description.lower() == description.lower():
                return task
        return None

    def complete_task(self, description: str, today: date | None = None) -> Task | None:
        """Mark the task as done and, if it repeats, add its next occurrence.

        Completes the first unfinished task with this description (case-insensitive)
        and keeps the finished one in the list as history. Returns the newly added
        task, or None for a one-time task. Raises ValueError if there is no match.
        """
        # Look for an unfinished match first: once a recurring task is done, its
        # finished copy and its next occurrence share the same description.
        task = next(
            (t for t in self.tasks
             if not t.completed and t.description.lower() == description.lower()),
            None,
        )
        if task is None:
            raise ValueError(f"{self.name} has no unfinished task named '{description}'")
        task.mark_complete()
        next_task = task.next_occurrence(today)
        if next_task is not None:
            self.add_task(next_task)
        return next_task

    def get_tasks(self) -> list[Task]:
        """Return all of this pet's tasks."""
        return list(self.tasks)


@dataclass
class Owner:
    """A pet owner, their available time, and their pets."""

    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        if self.find_pet(pet.name) is not None:
            raise ValueError(f"{self.name} already has a pet named '{pet.name}'")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove the pet with the given name (its tasks go with it)."""
        pet = self.find_pet(pet_name)
        if pet is None:
            raise ValueError(f"{self.name} has no pet named '{pet_name}'")
        self.pets.remove(pet)

    def find_pet(self, pet_name: str) -> Pet | None:
        """Return the pet with the given name, or None if there isn't one."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet
        return None

    def get_pets(self) -> list[Pet]:
        """Return all of this owner's pets."""
        return list(self.pets)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds a daily care plan for an owner's pets based on time and priority."""

    def __init__(
        self, owner: Owner, day_start: str = "08:00", plan_date: date | None = None
    ) -> None:
        """Set up a scheduler for the given owner and day (default today), starting at day_start."""
        self.owner = owner
        self.day_start = day_start
        self.plan_date = plan_date or date.today()
        self.plan: list[tuple[str, Task]] = []  # (start_time, task) pairs
        self.skipped: list[Task] = []
        self.conflicts: list[str] = []  # warnings from detect_conflicts()

    def collect_tasks(self) -> list[Task]:
        """Gather the incomplete tasks that are due on or before the plan date."""
        return [
            task
            for task in self.owner.get_all_tasks()
            if not task.completed and task.due_date <= self.plan_date
        ]

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (highest first), then by duration (shortest first)."""
        return sorted(tasks, key=lambda t: (-t.priority_value(), t.duration_minutes))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by their time ("HH:MM", earliest first); tasks without a time go last.

        Returns a new list and leaves the input unchanged. Tasks with the same time (or
        no time) keep their original order, since Python's sort is stable.
        """
        # Zero-padded "HH:MM" strings sort in clock order, so no parsing is needed.
        # The first key item puts timed tasks (False) before untimed ones (True).
        return sorted(tasks, key=lambda t: (t.time is None, t.time or ""))

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return the owner's tasks for one pet and/or completion status; None means any.

        The two filters combine, e.g. filter_tasks(pet_name="Mochi", completed=False)
        gives Mochi's unfinished tasks. Pet names match case-insensitively, and an
        unknown pet name gives an empty list rather than an error.
        """
        return [
            task
            for pet in self.owner.pets
            if pet_name is None or pet.name.lower() == pet_name.lower()
            for task in pet.tasks
            if completed is None or task.completed == completed
        ]

    def fit_to_budget(self, tasks: list[Task]) -> list[Task]:
        """Keep tasks that fit in the owner's available time; record the rest in skipped.

        This is a greedy pass: it does not search for the combination that uses the
        most time, it just lets earlier (higher-priority) tasks claim time first.
        """
        # Tasks are checked in the order given, so higher-priority tasks claim time first.
        # A task that doesn't fit is skipped, but later, shorter tasks can still fit.
        remaining = self.owner.available_minutes
        kept: list[Task] = []
        self.skipped = []
        for task in tasks:
            if task.duration_minutes <= remaining:
                kept.append(task)
                remaining -= task.duration_minutes
            else:
                self.skipped.append(task)
        return kept

    def generate_plan(self) -> list[tuple[str, Task]]:
        """Collect, sort, and fit tasks to the budget, then build a plan ordered by start time.

        Tasks with a fixed time keep it. The rest are placed back to back from day_start
        in priority order, sliding past any fixed task they would overlap.

        Saves and returns the plan as (start "HH:MM", task) pairs, records tasks that
        did not fit in self.skipped, and records overlap warnings in self.conflicts.
        Tasks themselves are not changed.
        """
        tasks = self.fit_to_budget(self.sort_tasks(self.collect_tasks()))
        fixed = [task for task in tasks if task.time is not None]
        flexible = [task for task in tasks if task.time is None]

        busy = []  # (start, end) of each fixed task, sorted by start
        for task in fixed:
            start = datetime.strptime(task.time, "%H:%M")
            busy.append((start, start + timedelta(minutes=task.duration_minutes)))
        busy.sort()

        self.plan = [(task.time, task) for task in fixed]
        current = datetime.strptime(self.day_start, "%H:%M")
        for task in flexible:
            length = timedelta(minutes=task.duration_minutes)
            # Because busy is sorted by start, one pass is enough: after jumping past a
            # block, only blocks further down the list can still be in the way.
            for busy_start, busy_end in busy:
                if current < busy_end and busy_start < current + length:
                    current = busy_end
            self.plan.append((current.strftime("%H:%M"), task))
            current += length

        self.plan.sort(key=lambda entry: entry[0])
        self.conflicts = self.detect_conflicts()
        return self.plan

    def detect_conflicts(self) -> list[str]:
        """Return a warning for each pair of planned tasks whose time slots overlap.

        Two tasks overlap when one starts before the other ends, so this catches partial
        overlaps as well as identical start times; back-to-back tasks are fine. It
        works for the same pet or different pets, and each warning says which.

        Only fixed-time tasks can clash, since flexible ones are placed around them.
        Conflicts are reported, not fixed or raised: the owner decides whether two
        tasks can really happen together (e.g. feeding both pets at once).
        """
        slots = []  # (start, end, task, pet name), in start-time order like self.plan
        for start_text, task in self.plan:
            start = datetime.strptime(start_text, "%H:%M")
            end = start + timedelta(minutes=task.duration_minutes)
            # Look up the pet once per task here, not once per compared pair below.
            slots.append((start, end, task, self.pet_name_for(task)))

        warnings = []
        for i, (start_a, end_a, task_a, pet_a) in enumerate(slots):
            for start_b, end_b, task_b, pet_b in slots[i + 1:]:
                # Sorted by start, so once one task starts after task_a ends, all later ones do.
                if start_b >= end_a:
                    break
                who = f"both for {pet_a}" if pet_a == pet_b else f"{pet_a} and {pet_b}"
                warnings.append(
                    f"Conflict: '{task_a.description}' "
                    f"({start_a:%H:%M}-{end_a:%H:%M}) overlaps '{task_b.description}' "
                    f"({start_b:%H:%M}-{end_b:%H:%M}), {who}."
                )
        return warnings

    def complete_task(self, pet_name: str, description: str) -> Task | None:
        """Mark one pet's task as done; return its next occurrence if it repeats."""
        pet = self.owner.find_pet(pet_name)
        if pet is None:
            raise ValueError(f"{self.owner.name} has no pet named '{pet_name}'")
        return pet.complete_task(description, today=self.plan_date)

    def explain_plan(self) -> str:
        """Return a readable explanation of why each task was scheduled or skipped."""
        if not self.plan and not self.skipped:
            return "No tasks to schedule."

        used = sum(task.duration_minutes for _, task in self.plan)
        lines = [
            f"Daily plan for {self.owner.name} "
            f"({used} of {self.owner.available_minutes} minutes used):"
        ]
        for start, task in self.plan:
            lines.append(
                f"  {start} - {task.description} for {self.pet_name_for(task)} "
                f"({task.duration_minutes} min) [priority: {task.priority}]"
            )
        lines.append(
            "Tasks with a set time keep it; the rest fill the open gaps by priority "
            "(high first), then shorter tasks first."
        )

        if self.skipped:
            lines.append("Skipped (not enough time left):")
            for task in self.skipped:
                lines.append(
                    f"  {task.description} for {self.pet_name_for(task)} "
                    f"({task.duration_minutes} min) [priority: {task.priority}]"
                )

        if self.conflicts:
            lines.append("Warnings (fixed times that overlap):")
            lines.extend(f"  {warning}" for warning in self.conflicts)
        return "\n".join(lines)

    def pet_name_for(self, task: Task) -> str:
        """Return the name of the pet that owns this task."""
        for pet in self.owner.pets:
            if any(t is task for t in pet.tasks):
                return pet.name
        return "unknown pet"
