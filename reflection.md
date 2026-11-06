# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

My initial UML design has four classes: `Owner`, `Pet`, `Task`, and `Scheduler`. The first three hold the data, and the `Scheduler` holds the planning logic. An `Owner` has one or more `Pet`s, and each `Pet` has zero or more `Task`s (both are composition: if a pet is removed, its tasks go with it). The `Scheduler` keeps a reference to one `Owner` and depends on `Task`. It doesn't own any tasks; it collects them from the owner's pets each time it builds a plan.

- What classes did you include, and what responsibilities did you assign to each?

- **Owner**: stores the owner's name, how many minutes they have for pet care that day (`available_minutes`), their preferences, and their list of pets. It is responsible for managing pets (`add_pet`, `remove_pet`, `get_pets`).
- **Pet**: stores the pet's name, species, age, any special needs, and its list of care tasks. It is responsible for managing its own tasks (`add_task`, `remove_task`, `get_tasks`).
- **Task**: represents one care activity with a title, duration in minutes, priority (low, medium, or high), category (walk, feeding, meds, and so on), and whether it is completed. It is responsible for updating itself (`mark_complete`, `edit`) and for turning its priority into a number (`priority_value`) so tasks can be sorted.
- **Scheduler**: takes an owner and a day start time and builds the daily plan. It gathers tasks from all pets (`collect_tasks`), orders them by priority and then duration (`sort_tasks`), drops tasks that don't fit in the available time (`filter_tasks`), assigns start times (`generate_plan`), and explains why each task was scheduled or skipped (`explain_plan`). It stores the result as a list of `(start_time, task)` pairs in `plan` and the left-out tasks in `skipped`.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

When two tasks with fixed times overlap, my scheduler only warns about it; it does not fix it. `detect_conflicts()` checks whether the time ranges overlap (start + duration), not just whether two tasks start at the same minute. For example, it catches a 15-minute puzzle feeder at 07:35 that runs into a 07:30 breakfast. But it never moves, shortens, or drops either task. It adds a message such as *"'Give medication' (08:00-08:05) overlaps 'Morning walk' (08:00-08:30), Luna and Mochi"* to `scheduler.conflicts`, keeps both tasks in the plan, and leaves the decision to the owner. Flexible tasks (ones with no set time) are the only ones the scheduler moves, and it places them in the open gaps around the fixed ones.

- Why is that tradeoff reasonable for this scenario?

A fixed time usually means something real, like a vet appointment or a medication that has to be given at 08:00, and the scheduler doesn't know which of two clashing tasks matters more in real life. Some overlaps are not even problems: one person can often feed two pets at once, or give a cat its pill while the dog is eating. If the scheduler moved a fixed task on its own, it could quietly push medication to the wrong time, which is worse than showing a warning. Returning a warning instead of raising an error also means one clash never stops the rest of the day from being planned. The cost is that the plan the owner sees can contain overlaps until they fix them by hand.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
