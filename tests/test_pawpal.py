import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


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
