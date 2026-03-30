import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet, Owner, Scheduler


def test_mark_complete_changes_status():
    """Calling mark_complete() should flip task.completed from False to True."""
    task = Task("Morning walk", duration_minutes=30, priority="high", frequency="daily")

    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True   # now done


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its tasks list length by one."""
    pet = Pet(name="Mochi", species="dog")

    assert len(pet.tasks) == 0  # no tasks yet

    pet.add_task(Task("Feeding", duration_minutes=10, priority="high", frequency="daily"))

    assert len(pet.tasks) == 1  # one task added


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() must return tasks earliest-first regardless of insertion order."""
    owner = Owner("Alex", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    afternoon = Task("Afternoon walk", duration_minutes=30, priority="medium", frequency="daily", scheduled_time="14:00")
    morning   = Task("Morning meds",   duration_minutes=10, priority="high",   frequency="daily", scheduled_time="08:00")
    midday    = Task("Midday feeding", duration_minutes=15, priority="high",   frequency="daily", scheduled_time="12:00")

    pet.add_task(afternoon)
    pet.add_task(morning)
    pet.add_task(midday)

    scheduler = Scheduler(owner)
    sorted_pairs = scheduler.sort_by_time(scheduler.get_all_tasks())
    times = [task.scheduled_time for _, task in sorted_pairs]

    assert times == ["08:00", "12:00", "14:00"]


def test_sort_tasks_places_timed_before_untimed():
    """_sort_tasks() must put time-anchored tasks before floating (untimed) ones."""
    owner = Owner("Alex", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    untimed = Task("Grooming",     duration_minutes=20, priority="high",   frequency="weekly")
    timed   = Task("Evening walk", duration_minutes=30, priority="low",    frequency="daily", scheduled_time="18:00")

    pet.add_task(untimed)
    pet.add_task(timed)

    scheduler = Scheduler(owner)
    sorted_pairs = scheduler._sort_tasks(scheduler.get_all_tasks())
    descriptions = [task.description for _, task in sorted_pairs]

    assert descriptions[0] == "Evening walk"   # timed comes first
    assert descriptions[1] == "Grooming"       # untimed comes second


def test_sort_tasks_breaks_same_time_tie_by_priority():
    """When two timed tasks share the same scheduled_time, high priority must sort before low."""
    owner = Owner("Alex", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    low_task  = Task("Bath",  duration_minutes=20, priority="low",  frequency="daily", scheduled_time="09:00")
    high_task = Task("Meds",  duration_minutes=10, priority="high", frequency="daily", scheduled_time="09:00")

    pet.add_task(low_task)
    pet.add_task(high_task)

    scheduler = Scheduler(owner)
    sorted_pairs = scheduler._sort_tasks(scheduler.get_all_tasks())
    descriptions = [task.description for _, task in sorted_pairs]

    assert descriptions[0] == "Meds"   # high priority wins the tie
    assert descriptions[1] == "Bath"


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_mark_complete_daily_task_creates_next_occurrence():
    """Completing a daily task must add a new pending task with due_day = current_day + 1."""
    owner = Owner("Alex", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Morning walk", duration_minutes=30, priority="high", frequency="daily"))

    scheduler = Scheduler(owner)
    next_task = scheduler.mark_task_complete("Mochi", "Morning walk", current_day=0)

    assert next_task is not None
    assert next_task.due_day == 1          # due tomorrow
    assert next_task.completed is False    # starts fresh
    assert next_task.description == "Morning walk"
    assert len(pet.tasks) == 2            # original + new occurrence


def test_next_occurrence_daily_is_not_due_today():
    """The new occurrence created for a daily task must not be due on the current day."""
    task = Task("Feeding", duration_minutes=10, priority="high", frequency="daily")
    next_task = task.next_occurrence(current_day=0)

    assert next_task is not None
    assert next_task.is_due_today(current_day=0) is False   # not yet
    assert next_task.is_due_today(current_day=1) is True    # due tomorrow


def test_weekly_task_not_due_before_seven_days():
    """A weekly task completed on day 0 must not be due again until day 7."""
    task = Task("Bath", duration_minutes=20, priority="medium", frequency="weekly", last_completed_day=0)
    task.due_day = 0

    assert task.is_due_today(current_day=6) is False
    assert task.is_due_today(current_day=7) is True


def test_as_needed_task_does_not_recur():
    """next_occurrence() must return None for as-needed tasks."""
    task = Task("Vet visit", duration_minutes=60, priority="high", frequency="as-needed")
    result = task.next_occurrence(current_day=0)

    assert result is None


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_overlapping_tasks():
    """Two tasks with overlapping time windows must produce exactly one conflict entry."""
    owner = Owner("Alex", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    pet.add_task(Task("Walk",    duration_minutes=30, priority="high",   frequency="daily", scheduled_time="08:00"))
    pet.add_task(Task("Feeding", duration_minutes=20, priority="medium", frequency="daily", scheduled_time="08:15"))

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert conflicts[0]["overlap_minutes"] == 15


def test_detect_conflicts_no_false_positive_for_adjacent_tasks():
    """Tasks that share an edge (end time == start time) must not be flagged as a conflict."""
    owner = Owner("Alex", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    pet.add_task(Task("Walk",    duration_minutes=30, priority="high",   frequency="daily", scheduled_time="08:00"))
    pet.add_task(Task("Feeding", duration_minutes=20, priority="medium", frequency="daily", scheduled_time="08:30"))

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 0


def test_detect_conflicts_ignores_untimed_tasks():
    """Tasks without a scheduled_time must never appear in conflict results."""
    owner = Owner("Alex", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    pet.add_task(Task("Grooming", duration_minutes=60, priority="low",  frequency="weekly"))
    pet.add_task(Task("Training", duration_minutes=60, priority="high", frequency="daily"))

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 0


def test_conflict_warnings_returns_human_readable_strings():
    """conflict_warnings() must return non-empty strings describing each conflict."""
    owner = Owner("Alex", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    pet.add_task(Task("Walk",    duration_minutes=45, priority="high",   frequency="daily", scheduled_time="09:00"))
    pet.add_task(Task("Feeding", duration_minutes=30, priority="medium", frequency="daily", scheduled_time="09:20"))

    scheduler = Scheduler(owner)
    warnings = scheduler.conflict_warnings()

    assert len(warnings) == 1
    assert "WARNING" in warnings[0]
    assert "Walk" in warnings[0]
    assert "Feeding" in warnings[0]
