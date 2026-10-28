"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care activity, such as a walk or feeding."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    category: str = "general"  # e.g. "walk", "feeding", "meds", "enrichment", "grooming"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def priority_value(self) -> int:
        """Return a number for the priority (low=1, medium=2, high=3) for sorting."""
        pass

    def edit(
        self,
        duration_minutes: int | None = None,
        priority: str | None = None,
        category: str | None = None,
    ) -> None:
        """Update any of the given fields, leaving the others unchanged."""
        pass


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
        pass

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return all of this pet's tasks."""
        pass


@dataclass
class Owner:
    """A pet owner, their available time, and their pets."""

    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, pet_name: str) -> None:
        """Remove the pet with the given name."""
        pass

    def get_pets(self) -> list[Pet]:
        """Return all of this owner's pets."""
        pass


class Scheduler:
    """Builds a daily care plan for an owner's pets based on time and priority."""

    def __init__(self, owner: Owner, day_start: str = "08:00") -> None:
        self.owner = owner
        self.day_start = day_start
        self.plan: list[tuple[str, Task]] = []  # (start_time, task) pairs
        self.skipped: list[Task] = []

    def collect_tasks(self) -> list[Task]:
        """Gather the incomplete tasks from all of the owner's pets."""
        pass

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (highest first), then by duration."""
        pass

    def filter_tasks(self, tasks: list[Task]) -> list[Task]:
        """Keep tasks that fit in the owner's available time; record the rest in skipped."""
        pass

    def generate_plan(self) -> list[tuple[str, Task]]:
        """Collect, sort, and filter tasks, then assign each a start time."""
        pass

    def explain_plan(self) -> str:
        """Return a readable explanation of why each task was scheduled or skipped."""
        pass
