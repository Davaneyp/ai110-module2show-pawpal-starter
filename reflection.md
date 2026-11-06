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

Yes. The four classes and their relationships stayed the same, but most of the methods inside them changed (the final version is in `diagrams/uml_final.mmd`).

The biggest change was splitting `filter_tasks()` in two. In my draft, `filter_tasks(tasks)` meant "drop the tasks that don't fit in the owner's time." Once I needed to show one pet's tasks, or only unfinished ones, that name no longer fit. I renamed the time-budget step to `fit_to_budget()` and made `filter_tasks(pet_name, completed)` a real filter by pet and completion status. Now each method does one thing, and its name says what that is.

Recurring tasks also changed shape. At one point the `Scheduler` had a `reset_recurring_tasks()` method that would un-complete tasks for a new day. I replaced it with `Task.next_occurrence()` and `Pet.complete_task()`. Completing a daily or weekly task now adds a new copy with the next `due_date`, and the finished copy stays as history. Each task knows how it repeats, so the Scheduler doesn't need a separate reset step, and the owner can still see what was done.

Other changes: `Task.title` became `description`, `Task` gained `frequency`, an optional fixed `time`, and a `due_date`, and an `Owner` can now have zero pets (not one or more), since the app starts with none.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers:

- **Available time:** the owner's `available_minutes` is a hard limit. Tasks that don't fit are skipped and listed.
- **Priority:** high, medium, then low. This decides which tasks get the limited time first.
- **Duration:** shorter tasks go first within the same priority, so more tasks fit.
- **Set times:** a task with a fixed `time` always keeps that time. Flexible tasks are placed around it.
- **Due date and completion:** only unfinished tasks due today or earlier are planned.
- **Day start:** flexible tasks are placed from the time the owner's day begins.

`Owner.preferences` exists in the model, but the scheduler doesn't use it yet.

I treated time as the one rule that can't be broken, because a plan that needs 90 minutes when the owner has 60 isn't a real plan. After that, priority matters most, because missing a medication or a meal is worse than missing a play session. Set times come next: if the owner says meds are at 08:00, the scheduler shouldn't move them just to make the plan tidier. Duration is only a tie-breaker. One result of this order is that a low-priority task with a set time can still be skipped if higher-priority tasks have used up the budget.

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

I used my AI coding assistant at every stage: turning the UML into class stubs, building the scheduling algorithms, writing tests, connecting the backend to the Streamlit UI, and writing the documentation. I used it most for implementing and checking, not for deciding what the system should be.

The most helpful prompts were specific and pointed at a file. "Based on `pawpal_system.py`, how should the Scheduler detect overlapping tasks for the same pet or different pets?" got much better answers than "make the scheduler smarter." Asking for edge cases ("what inputs would break `sort_by_time()`?") was also useful, because it found problems I hadn't thought of, such as `"8:00"` sorting after `"10:00"` as a string. That's why `Task` now requires zero-padded `HH:MM` times.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When I added conflict detection, the AI suggested that the scheduler should resolve conflicts itself, by moving or dropping one of two overlapping fixed-time tasks. I rejected that and kept conflicts as warnings only. A fixed time usually means something real, like a medication schedule or an appointment, and the scheduler has no way to know which of the two tasks can move. Some overlaps, like feeding two pets at once, aren't problems at all. Moving tasks automatically would have made the plan look clean while possibly putting a pet's medication at the wrong time. So `detect_conflicts()` only reports overlaps, and the owner decides. (Section 2b has the full tradeoff.)

To check the AI's work, I ran `python main.py`, which adds tasks out of order and includes two clashes on purpose, and compared the printed plan with what I expected. I also had it write pytest cases for the edge cases (same-pet and different-pet overlaps, partial overlaps, back-to-back tasks that should not be flagged), then read each test to make sure it checked the right behavior before trusting a passing result.

**c. AI strategy**

- Which AI coding assistant features were most effective for building your scheduler?

Three features helped the most:

1. **Agent edits across files.** One feature, like recurring tasks, touched `pawpal_system.py`, `main.py`, `app.py`, and the tests. Having the assistant make all of those changes together kept them consistent. I reviewed the diff before accepting it instead of trusting the summary.
2. **Test generation.** Asking for tests of specific edge cases gave me 35 tests quickly, including an `xfail` test that records a real bug the AI and I found: plans that run past midnight.
3. **Code explanation and review.** Before accepting a method, I asked the AI to explain it or point out its weaknesses. That's how I learned that `fit_to_budget()` is greedy, not optimal. I kept it because it's simple and predictable, and I documented the limitation instead of hiding it.

- Give one example of an AI suggestion you rejected or modified to keep your system design clean.

The suggestion to fix conflicts automatically, described in 3b. Keeping `detect_conflicts()` to "find and report" kept the Scheduler's job clear. It plans flexible tasks, but it never changes a decision the owner made.

- How did using separate chat sessions for different phases help you stay organized?

I started a new chat session for each phase: design and UML, core classes, scheduling algorithms, testing, and the UI and documentation. Each session started with just the files and goal for that phase, so the AI wasn't mixing in old ideas. For example, after the redesign it never went back to the old meaning of `filter_tasks()`. It also made each phase feel like a finished unit of work that I could check and commit before moving on, and it gave me a clear point to ask "does the design still hold?" before building the next layer.

**d. Being the lead architect**

The AI is very good at producing code, and that is exactly why someone has to own the design. It wrote working methods quickly, but it didn't know that a medication time shouldn't move, that a method name should match what the method does, or that a simple, predictable algorithm is sometimes better than a clever one. Those were my decisions. Being the lead architect meant deciding the classes and responsibilities first (the UML), giving the AI narrow tasks inside that design, and checking everything it produced with tests and real runs before accepting it. When I gave it clear limits, it was a fast and reliable teammate. When I didn't, it tended to add features that blurred the design. The most useful thing I did was keep asking whether a change fit the system I had designed, not just whether the code worked.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The suite in `tests/test_pawpal.py` has 35 tests, and all use a fixed date so they don't depend on the day they run. They cover:

- **Sorting:** clock order, untimed tasks last, stable ties, and the input list left unchanged. Also priority-then-duration order, and the final plan in start-time order.
- **Recurring tasks:** daily copies are due the next day, weekly copies 7 days later, and one-time tasks get no copy. Tasks finished early or late are handled. The next copy stays out of today's plan.
- **Conflict detection:** same-pet and different-pet clashes, partial overlaps, back-to-back tasks not flagged, and flexible tasks moved past fixed ones.
- **Time budget:** an exact fit is kept, a zero budget skips everything, and a long skipped task doesn't block shorter ones. Completed and future tasks are left out, and overdue tasks are included.
- **Input checks:** invalid values raise `ValueError`, a failed `edit()` rolls back, and duplicate pet names are rejected.

These tests matter because the scheduler's mistakes would be quiet ones. A wrong order, a missed overlap, or a duplicate recurring task wouldn't crash anything. The plan would just be wrong, and the owner might not notice until a pet missed its medication. The edge-case tests check the exact boundaries where that kind of bug happens, such as a task ending at 08:30 and the next starting at 08:30.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

About 4 out of 5. All the core behaviors pass, including their edge cases. I'm holding back one point for one known bug and for the gaps below. The bug: if a plan runs past midnight, a flexible task's start time wraps to `"00:xx"` and sorts to the top. It's recorded as an `xfail` test.

Next I would test:

- Fixed-time tasks set earlier than `day_start`, and single tasks longer than the whole day.
- Two tasks with the same description for one pet. `find_task()` and `remove_task()` return the first match, which could be a finished history copy instead of the current task.
- Changing a task's set time. `edit()` doesn't support `time` yet.
- The Streamlit UI itself, using Streamlit's `AppTest`, since `app.py` has no automated tests.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with how the scheduling pieces fit together. `generate_plan()` is a short pipeline of small steps (collect, sort, fit to budget, place, check conflicts), and each step is its own method that I could test separately. Because of that, adding conflict detection and recurring tasks late in the project didn't require rewriting anything. I'm also happy that the plan explains itself: the owner can see why each task is where it is and why something was skipped.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would fix the midnight wrap by tracking full datetimes instead of `"HH:MM"` strings inside `generate_plan()`. I would also use `Owner.preferences` (for example, "walks in the morning"), and offer suggestions when tasks conflict, such as the nearest free slot, while still leaving the choice to the owner. Finally, I would save owners and pets to a file so the app keeps its data between sessions.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

A clear design is what makes AI help useful. Because I had decided the classes and their jobs up front, I could give the AI small, well-defined tasks and easily judge whether its answers fit. Whenever I skipped that step, I spent more time undoing suggestions than I saved. The AI can write the code, but deciding what the system should and shouldn't do is still my job.
