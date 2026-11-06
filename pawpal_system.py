"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

PRIORITY_VALUES = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")


@dataclass
class Task:
    """A single pet care activity, such as a walk or feeding."""

    description: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    frequency: str = "daily"  # "once", "daily", or "weekly"
    category: str = "general"  # e.g. "walk", "feeding", "meds", "enrichment", "grooming"
    time: str | None = None  # start time ("HH:MM"), set by the Scheduler
    completed: bool = False

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

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def reset(self) -> None:
        """Mark this task as not done, e.g. at the start of a new day."""
        self.completed = False

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

    def __init__(self, owner: Owner, day_start: str = "08:00") -> None:
        """Set up a scheduler for the given owner, starting the day at day_start ("HH:MM")."""
        self.owner = owner
        self.day_start = day_start
        self.plan: list[tuple[str, Task]] = []  # (start_time, task) pairs
        self.skipped: list[Task] = []

    def collect_tasks(self) -> list[Task]:
        """Gather the incomplete tasks from all of the owner's pets."""
        return [task for task in self.owner.get_all_tasks() if not task.completed]

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (highest first), then by duration (shortest first)."""
        return sorted(tasks, key=lambda t: (-t.priority_value(), t.duration_minutes))

    def filter_tasks(self, tasks: list[Task]) -> list[Task]:
        """Keep tasks that fit in the owner's available time; record the rest in skipped."""
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
        """Collect, sort, and filter tasks, then assign each a start time back to back."""
        tasks = self.filter_tasks(self.sort_tasks(self.collect_tasks()))

        self.plan = []
        current = datetime.strptime(self.day_start, "%H:%M")
        for task in tasks:
            task.time = current.strftime("%H:%M")
            self.plan.append((task.time, task))
            current += timedelta(minutes=task.duration_minutes)

        for task in self.skipped:
            task.time = None
        return self.plan

    def complete_task(self, pet_name: str, description: str) -> None:
        """Mark one pet's task as done."""
        pet = self.owner.find_pet(pet_name)
        if pet is None:
            raise ValueError(f"{self.owner.name} has no pet named '{pet_name}'")
        task = pet.find_task(description)
        if task is None:
            raise ValueError(f"{pet_name} has no task named '{description}'")
        task.mark_complete()

    def reset_recurring_tasks(self) -> None:
        """Start a new day: mark daily tasks as not done so they get scheduled again."""
        for task in self.owner.get_all_tasks():
            if task.frequency == "daily":
                task.reset()

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
            "Tasks are ordered by priority (high first), then shorter tasks first."
        )

        if self.skipped:
            lines.append("Skipped (not enough time left):")
            for task in self.skipped:
                lines.append(
                    f"  {task.description} for {self.pet_name_for(task)} "
                    f"({task.duration_minutes} min) [priority: {task.priority}]"
                )
        return "\n".join(lines)

    def pet_name_for(self, task: Task) -> str:
        """Return the name of the pet that owns this task."""
        for pet in self.owner.pets:
            if any(t is task for t in pet.tasks):
                return pet.name
        return "unknown pet"
