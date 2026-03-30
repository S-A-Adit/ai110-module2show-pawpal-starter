import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner.")

st.divider()

# ---------------------------------------------------------------------------
# Session state — initialise the Owner once per browser session.
# The "if key not in" guard means: create the object only on the very first
# page load; every subsequent rerun reuses the existing object from the vault.
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 1 — Owner profile
# ---------------------------------------------------------------------------

st.subheader("1. Owner Profile")

col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Your name", value=owner.name)
with col2:
    owner.available_minutes = st.number_input(
        "Minutes available today",
        min_value=10, max_value=480,
        value=owner.available_minutes,
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add a Pet  →  calls owner.add_pet(Pet(...))
# ---------------------------------------------------------------------------

st.subheader("2. Your Pets")

with st.form("add_pet_form", clear_on_submit=True):
    st.caption("Register a new pet with this owner.")
    pc1, pc2, pc3 = st.columns([2, 2, 1])
    with pc1:
        new_pet_name = st.text_input("Pet name", placeholder="e.g. Mochi")
    with pc2:
        new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    with pc3:
        st.write("")   # vertical spacer
        st.write("")
        add_pet_btn = st.form_submit_button("Add pet")

    if add_pet_btn:
        if not new_pet_name.strip():
            st.warning("Please enter a pet name.")
        elif any(p.name.lower() == new_pet_name.strip().lower() for p in owner.pets):
            st.warning(f"A pet named '{new_pet_name}' already exists.")
        else:
            # ↓ Phase 2 method: Owner.add_pet()
            owner.add_pet(Pet(name=new_pet_name.strip(), species=new_pet_species))
            st.success(f"Added {new_pet_name} the {new_pet_species}!")

if owner.pets:
    for pet in owner.pets:
        st.write(f"**{pet.name}** ({pet.species}) — {len(pet.tasks)} task(s), "
                 f"{pet.total_task_minutes()} min total")   # ↑ Pet.total_task_minutes()
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Add / manage tasks  →  calls pet.add_task(), pet.remove_task(),
#             task.mark_complete(), task.reset()
# ---------------------------------------------------------------------------

st.subheader("3. Tasks")

if not owner.pets:
    st.info("Add a pet first, then come back to add tasks.")
else:
    # Let the user choose which pet to work with.
    pet_names   = [p.name for p in owner.pets]
    chosen_name = st.selectbox("Select pet", pet_names)
    pet: Pet    = next(p for p in owner.pets if p.name == chosen_name)

    # --- Add task form ---
    with st.form("add_task_form", clear_on_submit=True):
        st.caption(f"Add a new task for **{pet.name}**.")
        tc1, tc2, tc3, tc4 = st.columns([3, 2, 2, 2])
        with tc1:
            task_desc = st.text_input("Description", placeholder="e.g. Morning walk")
        with tc2:
            task_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with tc3:
            task_priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        with tc4:
            task_frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
        add_task_btn = st.form_submit_button("Add task")

        if add_task_btn:
            new_task = Task(
                description=task_desc,
                duration_minutes=int(task_duration),
                priority=task_priority,
                frequency=task_frequency,
            )
            try:
                # ↓ Phase 2 method: Pet.add_task()
                pet.add_task(new_task)
                st.success(f"Added '{task_desc}' to {pet.name}.")
            except ValueError as e:
                st.error(str(e))

    # --- Task list with complete / reset / remove controls ---
    if pet.tasks:
        st.write(f"**{pet.name}'s tasks:**")
        for i, task in enumerate(pet.tasks):
            row = st.columns([3, 1, 1, 1, 1])
            status_icon = "✅" if task.completed else "⬜"
            row[0].write(f"{status_icon} **{task.description}**  "
                         f"({task.duration_minutes} min · {task.priority} · {task.frequency})")

            if row[1].button("Done", key=f"done_{i}"):
                # ↓ Phase 2 method: Task.mark_complete()
                task.mark_complete()
                st.rerun()

            if row[2].button("Reset", key=f"reset_{i}"):
                # ↓ Phase 2 method: Task.reset()
                task.reset()
                st.rerun()

            if row[3].button("Remove", key=f"remove_{i}"):
                # ↓ Phase 2 method: Pet.remove_task()
                pet.remove_task(task.description)
                st.rerun()
    else:
        st.info(f"No tasks for {pet.name} yet.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule  →  calls Scheduler(owner).generate_plan()
#             which internally calls owner.get_all_tasks() to collect tasks
#             across every pet, then applies the greedy priority algorithm.
# ---------------------------------------------------------------------------

st.subheader("4. Today's Schedule")

if st.button("Generate schedule", type="primary"):
    all_tasks = owner.get_all_tasks()       # ↑ Owner.get_all_tasks()
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        # ↓ Phase 2 method: Scheduler.generate_plan()
        plan = Scheduler(owner).generate_plan()
        st.markdown(plan.summary())

        if plan.skipped:
            st.info(f"{len(plan.skipped)} task(s) were skipped — "
                    "increase your available minutes or remove lower-priority tasks to fit them in.")
