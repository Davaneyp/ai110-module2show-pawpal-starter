"""Temporary testing ground: build a sample owner, pets, and tasks, then print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_tasks(title: str, tasks: list[Task], scheduler: Scheduler) -> None:
    """Print a heading and one line per task."""
    print(f"\n{title}")
    print("-" * 50)
    if not tasks:
        print("  (none)")
    for task in tasks:
        status = "done" if task.completed else "todo"
        print(
            f"  {task.time or '--:--'}  {task.description:<18} "
            f"{scheduler.pet_name_for(task):<6} {task.frequency:<7} "
            f"due {task.due_date}  [{status}]"
        )


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=120)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5, special_needs=["daily medication"])
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added out of time order on purpose, to show sort_by_time() at work.
    mochi.add_task(Task("Evening walk", 30, priority="high", category="walk", time="18:00"))
    mochi.add_task(Task("Breakfast", 10, priority="high", category="feeding", time="07:30"))
    mochi.add_task(Task("Brush coat", 15, priority="low", frequency="weekly", category="grooming"))
    # Two clashes on purpose, to show detect_conflicts() at work:
    # same time as Luna's 08:00 medication (different pets) ...
    mochi.add_task(Task("Morning walk", 30, priority="high", category="walk", time="08:00"))
    # ... and starting while Mochi's own 07:30 breakfast is still going (same pet).
    mochi.add_task(Task("Puzzle feeder", 15, priority="medium", category="enrichment", time="07:35"))
    luna.add_task(Task("Dinner", 5, priority="high", category="feeding", time="17:30"))
    luna.add_task(Task("Give medication", 5, priority="high", category="meds", time="08:00"))
    luna.add_task(Task("Feather toy play", 20, priority="medium", category="enrichment"))
    luna.add_task(Task("Clean litter box", 10, priority="medium", category="general"))
    luna.add_task(Task("Nail trim", 25, priority="low", frequency="weekly", category="grooming"))
    luna.add_task(Task("Vet checkup", 45, priority="high", frequency="once", category="general"))

    scheduler = Scheduler(owner, day_start="07:30")

    print("=" * 50)
    print("Recurring Tasks")
    print("=" * 50)
    for pet_name, description in [
        ("Luna", "Clean litter box"),  # daily  -> next copy due tomorrow
        ("Mochi", "Brush coat"),  # weekly -> next copy due in 7 days
        ("Luna", "Vet checkup"),  # once   -> no next copy
    ]:
        next_task = scheduler.complete_task(pet_name, description)
        if next_task is None:
            print(f"  Completed '{description}' ({pet_name}); it does not repeat.")
        else:
            print(
                f"  Completed '{description}' ({pet_name}); "
                f"next {next_task.frequency} copy due {next_task.due_date}."
            )

    print()
    print("=" * 50)
    print("Sorting and Filtering")
    print("=" * 50)
    print_tasks("All tasks (in the order they were added):", owner.get_all_tasks(), scheduler)
    print_tasks("Sorted by time:", scheduler.sort_by_time(owner.get_all_tasks()), scheduler)
    print_tasks("Luna's tasks only:", scheduler.filter_tasks(pet_name="Luna"), scheduler)
    print_tasks("Still to do:", scheduler.filter_tasks(completed=False), scheduler)
    print_tasks("Completed:", scheduler.filter_tasks(completed=True), scheduler)
    print_tasks(
        "Mochi's tasks still to do, sorted by time:",
        scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi", completed=False)),
        scheduler,
    )

    scheduler.generate_plan()

    print()
    print("=" * 50)
    print("Conflict Check")
    print("=" * 50)
    if scheduler.conflicts:
        for warning in scheduler.conflicts:
            print(f"  WARNING: {warning}")
    else:
        print("  No conflicts.")

    print()
    print("=" * 50)
    print("Today's Schedule")
    print("=" * 50)
    print(scheduler.explain_plan())
    print("(Tasks completed today and copies due on later days are left out.)")


if __name__ == "__main__":
    main()
