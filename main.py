from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

mochi = Pet(name="Mochi", species="dog")
rex = Pet(name="Rex", species="cat")

owner.add_pet(mochi)
owner.add_pet(rex)

# --- Tasks for Mochi ---
mochi.add_task(Task("Morning walk",      duration_minutes=30, priority="high",   frequency="daily"))
mochi.add_task(Task("Feeding",           duration_minutes=10, priority="high",   frequency="daily"))
mochi.add_task(Task("Brush coat",        duration_minutes=15, priority="low",    frequency="weekly"))

# --- Tasks for Rex ---
rex.add_task(Task("Medication",          duration_minutes=5,  priority="high",   frequency="daily"))
rex.add_task(Task("Litter box cleaning", duration_minutes=10, priority="medium", frequency="daily"))
rex.add_task(Task("Enrichment play",     duration_minutes=20, priority="medium", frequency="as-needed"))

# --- Generate plan ---
scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

# --- Print Today's Schedule ---
print("=" * 50)
print("       PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 50)
print(f"Owner : {owner.name}")
print(f"Pets  : {', '.join(p.name for p in owner.pets)}")
print(f"Budget: {owner.available_minutes} minutes")
print("-" * 50)

if plan.has_items():
    print(f"\nSCHEDULED  ({plan.total_minutes_used} min used)\n")
    for item in plan.items:
        print(f"  [{item['pet']}] {item['description']}")
        print(f"         {item['duration_minutes']} min | {item['priority']} priority | {item['frequency']}")
        print(f"         {item['reason']}")
        print()
else:
    print("\n  No tasks could be scheduled.\n")

if plan.skipped:
    print(f"SKIPPED  ({len(plan.skipped)} task(s) didn't fit)\n")
    for item in plan.skipped:
        print(f"  [{item['pet']}] {item['description']} — {item['reason']}")
    print()

print("=" * 50)
print(plan.summary())
print("=" * 50)
