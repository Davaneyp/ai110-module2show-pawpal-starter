"""Temporary testing ground: build a sample owner, pets, and tasks, then print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5, special_needs=["daily medication"])
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", 30, priority="high", category="walk"))
    mochi.add_task(Task("Breakfast", 10, priority="high", category="feeding"))
    mochi.add_task(Task("Brush coat", 15, priority="low", frequency="weekly", category="grooming"))
    luna.add_task(Task("Give medication", 5, priority="high", category="meds"))
    luna.add_task(Task("Feather toy play", 20, priority="medium", category="enrichment"))
    luna.add_task(Task("Clean litter box", 10, priority="medium", category="general"))
    luna.add_task(Task("Nail trim", 25, priority="low", frequency="weekly", category="grooming"))

    scheduler = Scheduler(owner, day_start="07:30")
    scheduler.generate_plan()

    print("=" * 50)
    print("Today's Schedule")
    print("=" * 50)
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
