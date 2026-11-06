from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# Streamlit reruns this script on every click, so keep one Owner in session_state
# and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=60)
owner = st.session_state.owner

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value="Jordan", key="owner_name")
with col2:
    owner.available_minutes = int(
        st.number_input(
            "Minutes available today",
            min_value=0,
            max_value=1440,
            value=60,
            step=5,
            key="available_minutes",
        )
    )

st.subheader("Add a Pet")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=40, value=3)
    if st.form_submit_button("Add pet"):
        try:
            owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
            st.success(f"Added {pet_name}.")
        except ValueError as e:
            st.error(str(e))

pets = owner.get_pets()
if pets:
    st.write("Your pets:")
    st.table(
        [
            {"name": p.name, "species": p.species, "age": p.age, "tasks": len(p.get_tasks())}
            for p in pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
if not pets:
    st.caption("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        task_pet = st.selectbox("For which pet?", [p.name for p in pets])
        col1, col2, col3 = st.columns(3)
        with col1:
            description = st.text_input("Task description", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        col4, col5 = st.columns(2)
        with col4:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        with col5:
            category = st.selectbox(
                "Category", ["walk", "feeding", "meds", "enrichment", "grooming", "general"]
            )
        col6, col7 = st.columns(2)
        with col6:
            has_fixed_time = st.checkbox("Must happen at a set time")
        with col7:
            fixed_time = st.time_input("Set time", value=time(8, 0), step=300)
        if st.form_submit_button("Add task"):
            try:
                owner.find_pet(task_pet).add_task(
                    Task(
                        description=description.strip(),
                        duration_minutes=int(duration),
                        priority=priority,
                        frequency=frequency,
                        category=category,
                        time=fixed_time.strftime("%H:%M") if has_fixed_time else None,
                    )
                )
                st.success(f"Added '{description}' for {task_pet}.")
            except ValueError as e:
                st.error(str(e))

    all_tasks = [(p, t) for p in owner.get_pets() for t in p.get_tasks()]
    if all_tasks:
        st.write("Current tasks:")
        st.table(
            [
                {
                    "pet": p.name,
                    "description": t.description,
                    "duration (min)": t.duration_minutes,
                    "priority": t.priority,
                    "frequency": t.frequency,
                    "due": t.due_date.isoformat(),
                    "done": "✅" if t.completed else "",
                }
                for p, t in all_tasks
            ]
        )

        unfinished = [(p, t) for p, t in all_tasks if not t.completed]
        if unfinished:
            with st.form("complete_task"):
                choice = st.selectbox(
                    "Mark a task done",
                    range(len(unfinished)),
                    format_func=lambda i: (
                        f"{unfinished[i][1].description} ({unfinished[i][0].name}, "
                        f"due {unfinished[i][1].due_date})"
                    ),
                )
                if st.form_submit_button("Mark done"):
                    pet, task = unfinished[choice]
                    next_task = pet.complete_task(task.description)
                    message = f"Done: '{task.description}'."
                    if next_task is not None:
                        message += (
                            f" Next {next_task.frequency} copy added, due {next_task.due_date}."
                        )
                    # Rerun so the table above shows the change; keep the message for it.
                    st.session_state.done_message = message
                    st.rerun()
        if "done_message" in st.session_state:
            st.success(st.session_state.pop("done_message"))
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
day_start = st.time_input("Day starts at", value=time(8, 0), step=900)

if st.button("Generate schedule"):
    scheduler = Scheduler(owner, day_start=day_start.strftime("%H:%M"))
    plan = scheduler.generate_plan()

    if plan:
        st.success(f"Today's schedule for {owner.name}")
        st.table(
            [
                {
                    "time": start,
                    "task": task.description,
                    "pet": scheduler.pet_name_for(task),
                    "duration (min)": task.duration_minutes,
                    "priority": task.priority,
                }
                for start, task in plan
            ]
        )
    else:
        st.warning("Nothing could be scheduled. Add tasks or increase your available minutes.")

    for warning in scheduler.conflicts:
        st.warning(warning, icon="⚠️")

    if scheduler.skipped:
        st.warning(
            "Skipped (not enough time): "
            + ", ".join(f"{t.description} ({t.duration_minutes} min)" for t in scheduler.skipped)
        )

    with st.expander("Why this plan?"):
        st.text(scheduler.explain_plan())
