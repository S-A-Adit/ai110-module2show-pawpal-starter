# pawpal_system.py
# Logic layer for PawPal+: all backend classes live here.


class Task:
    """A single pet care activity (walk, feeding, meds, etc.)."""

    VALID_PRIORITIES = {"low", "medium", "high"}

    def __init__(self, title: str, duration_minutes: int, priority: str):
        self.title = title                      # str  — e.g. "Morning walk"
        self.duration_minutes = duration_minutes  # int  — how long the task takes (>= 1)
        self.priority = priority                # str  — "low", "medium", or "high"

    def priority_rank(self) -> int:
        """Return 3/2/1 for high/medium/low. Used to sort tasks before scheduling."""
        pass

    def is_valid(self) -> bool:
        """Return True if title is non-empty, duration >= 1, and priority is valid."""
        pass

    def __repr__(self) -> str:
        pass


class Pet:
    """The animal being cared for. Owns the list of care tasks."""

    def __init__(self, name: str, species: str):
        self.name = name        # str        — e.g. "Mochi"
        self.species = species  # str        — "dog", "cat", or "other"
        self.tasks = []         # list[Task] — all tasks for this pet

    def add_task(self, task: "Task") -> None:
        """Append task to self.tasks. Raise ValueError if task.is_valid() is False."""
        pass

    def remove_task(self, title: str) -> bool:
        """Remove the first task whose title matches (case-insensitive).
        Return True if found and removed, False otherwise."""
        pass

    def total_task_minutes(self) -> int:
        """Return the sum of duration_minutes across all tasks."""
        pass

    def __repr__(self) -> str:
        pass


class Owner:
    """The human user. Holds their name and daily time budget for pet care."""

    def __init__(self, name: str, available_minutes: int = 120):
        self.name = name                          # str — owner's name
        self.available_minutes = available_minutes  # int — minutes available per day

    def __repr__(self) -> str:
        pass


class Schedule:
    """The output produced by Scheduler.generate().
    Contains the ordered plan and any tasks that were skipped."""

    def __init__(
        self,
        pet_name: str,
        items: list,
        skipped: list,
        total_minutes_used: int,
        available_minutes: int,
    ):
        self.pet_name = pet_name                      # str       — for display
        self.items = items                            # list[dict] — scheduled tasks
        self.skipped = skipped                        # list[dict] — excluded tasks
        self.total_minutes_used = total_minutes_used  # int       — minutes consumed
        self.available_minutes = available_minutes    # int       — owner's budget

        # Each dict in items / skipped has shape:
        # {
        #   "title": str,
        #   "duration_minutes": int,
        #   "priority": str,
        #   "reason": str   <- natural-language explanation for the UI
        # }

    def has_items(self) -> bool:
        """Return True if at least one task was scheduled."""
        pass

    def summary(self) -> str:
        """Return a multi-line markdown string summarising the plan.
        Suitable for passing to st.markdown() in app.py."""
        pass


class Scheduler:
    """Generates a daily care schedule by greedily fitting tasks into the time budget."""

    def __init__(self, owner: "Owner", pet: "Pet"):
        self.owner = owner  # Owner — provides available_minutes
        self.pet = pet      # Pet   — provides the task list

    def _sort_tasks(self) -> list:
        """Return pet.tasks sorted by priority_rank() descending.
        Ties are broken alphabetically by title for determinism."""
        pass

    def generate(self) -> "Schedule":
        """Build and return a Schedule.

        Algorithm:
        1. Sort tasks via _sort_tasks() (high priority first).
        2. Walk the sorted list, accumulating used minutes.
        3. Include a task if used + duration <= available_minutes.
        4. Otherwise add it to skipped with a reason explaining the overage.
        5. Return Schedule(pet_name, items, skipped, used, available_minutes).
        """
        pass
