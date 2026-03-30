from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=180)

mochi = Pet(name="Mochi", species="dog")
rex   = Pet(name="Rex",   species="cat")

owner.add_pet(mochi)
owner.add_pet(rex)

# ---------------------------------------------------------------------------
# Tasks — two deliberate conflicts planted among valid tasks
#
# CONFLICT 1 (same pet — Mochi):
#   "Morning walk"  07:00 for 30 min  (ends 07:30)
#   "Feeding"       07:15 for 10 min  (starts inside the walk window)
#
# CONFLICT 2 (different pets — Mochi & Rex):
#   "Brush coat"    09:00 for 20 min  (ends 09:20)
#   "Vet call"      09:00 for 15 min  (exact same start time)
#
# No conflict:
#   "Litter box"    08:00 for 10 min  (ends 08:10, nothing overlaps)
#   "Medication"    07:45 for  5 min  (ends 07:50, no overlap with others)
# ---------------------------------------------------------------------------

# Mochi
mochi.add_task(Task("Morning walk", duration_minutes=30, priority="high",   frequency="daily",  scheduled_time="07:00"))
mochi.add_task(Task("Feeding",      duration_minutes=10, priority="high",   frequency="daily",  scheduled_time="07:15"))  # <- overlaps walk
mochi.add_task(Task("Brush coat",   duration_minutes=20, priority="low",    frequency="weekly", scheduled_time="09:00"))  # <- overlaps Rex's vet call

# Rex
rex.add_task(Task("Medication",       duration_minutes=5,  priority="high",   frequency="daily",  scheduled_time="07:45"))
rex.add_task(Task("Litter box",       duration_minutes=10, priority="medium", frequency="daily",  scheduled_time="08:00"))
rex.add_task(Task("Vet call",         duration_minutes=15, priority="medium", frequency="weekly", scheduled_time="09:00"))  # <- overlaps Mochi's brush coat

scheduler = Scheduler(owner)

# ---------------------------------------------------------------------------
# Print all registered tasks in time order so the overlap is easy to see
# ---------------------------------------------------------------------------
print("=" * 62)
print("REGISTERED TASKS  (sorted by time)")
print("=" * 62)
all_sorted = scheduler.sort_by_time(scheduler.get_all_tasks())
for pet, task in all_sorted:
    end_time_min = task.time_as_minutes() + task.duration_minutes
    end_hh = end_time_min // 60
    end_mm = end_time_min % 60
    print(
        f"  {task.scheduled_time}–{end_hh:02d}:{end_mm:02d}"
        f"  [{pet.name:<5}]  {task.description}"
    )

# ---------------------------------------------------------------------------
# Run conflict detection — returns warning strings, never raises
# ---------------------------------------------------------------------------
print()
print("=" * 62)
print("CONFLICT DETECTION  (conflict_warnings)")
print("=" * 62)

warnings = scheduler.conflict_warnings()

if warnings:
    for w in warnings:
        print(f"  {w}")
else:
    print("  No conflicts detected — schedule is clean.")

# ---------------------------------------------------------------------------
# Generate the plan anyway — the scheduler keeps going despite conflicts
# ---------------------------------------------------------------------------
print()
print("=" * 62)
print("TODAY'S SCHEDULE  (generated despite conflicts)")
print("=" * 62)

plan = scheduler.generate_plan(current_day=0)
print(f"  {plan.total_minutes_used} of {plan.available_minutes} minutes used.\n")

for item in plan.items:
    t = item.get("scheduled_time") or "no time"
    print(f"  {t}  [{item['pet']}]  {item['description']}  ({item['priority']})")

if plan.skipped:
    print(f"\n  Skipped ({len(plan.skipped)}):")
    for item in plan.skipped:
        print(f"    [{item['pet']}]  {item['description']}  — {item['reason']}")
