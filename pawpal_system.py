# pawpal_system.py
# Logic layer for PawPal+: all backend classes live here.

from itertools import combinations


class Task:
    """A single pet care activity (walk, feeding, meds, grooming, etc.)."""

    VALID_PRIORITIES = {"low", "medium", "high"}
    VALID_FREQUENCIES = {"daily", "weekly", "as-needed"}

    def __init__(
        self,
        description: str,
        duration_minutes: int,
        priority: str = "medium",
        frequency: str = "daily",
        scheduled_time: str | None = None,
        last_completed_day: int | None = None,
    ):
        self.description = description            # str       — what the task is
        self.duration_minutes = duration_minutes  # int       — how long it takes (>= 1)
        self.priority = priority                  # str       — "low", "medium", or "high"
        self.frequency = frequency                # str       — "daily", "weekly", or "as-needed"
        self.completed = False                    # bool      — completion status for today
        self.scheduled_time = scheduled_time      # str|None  — "HH:MM", e.g. "08:00"
        self.last_completed_day = last_completed_day  # int|None  — day number when last done
        self.due_day = 0                          # int       — first day this occurrence is eligible

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def mark_complete(self) -> None:
        """Mark this task as done for today."""
        self.completed = True

    def reset(self) -> None:
        """Clear the completion status (e.g. at the start of a new day)."""
        self.completed = False

    # ------------------------------------------------------------------
    # Time helpers
    # ------------------------------------------------------------------

    def time_as_minutes(self) -> int | None:
        """Convert the task's scheduled_time string to an integer minute offset from midnight.

        Splits the "HH:MM" string on ":" and computes hours * 60 + minutes.
        Used internally by detect_conflicts() and _sort_tasks() so that clock
        times can be compared with ordinary arithmetic.

        Returns:
            int: Minutes since midnight (e.g. "08:30" -> 510), or
            None: if scheduled_time is not set on this task.
        """
        if self.scheduled_time is None:
            return None
        h, m = self.scheduled_time.split(":")
        return int(h) * 60 + int(m)

    def is_due_today(self, current_day: int = 0) -> bool:
        """Return True if this task should appear in today's plan.

        current_day: day counter (0 = today, 1 = tomorrow, …).
        A task's due_day gates whether it is even eligible yet — used to hold
        auto-created next occurrences back until their scheduled day arrives.
        Weekly tasks additionally require 7 days since last completion.
        """
        # Block future occurrences that haven't ripened yet
        if current_day < self.due_day:
            return False
        if self.frequency in ("daily", "as-needed"):
            return True
        if self.frequency == "weekly":
            if self.last_completed_day is None:
                return True
            return (current_day - self.last_completed_day) >= 7
        return True

    def next_occurrence(self, current_day: int = 0) -> "Task | None":
        """Create and return a new pending Task instance for the next recurrence of this task.

        Copies all scheduling attributes (description, duration, priority, frequency,
        scheduled_time) from the current task into a fresh instance whose completed
        flag is False.  Sets due_day so the new instance is invisible to
        is_due_today() until the correct future day arrives:

            daily  -> due_day = current_day + 1
            weekly -> due_day = current_day + 7

        as-needed tasks do not recur automatically and return None.

        Args:
            current_day (int): The day counter on which this task is being completed.
                               Defaults to 0 (today).

        Returns:
            Task: A fresh pending task due on the next occurrence date, or
            None: if frequency is "as-needed".
        """
        if self.frequency == "daily":
            interval = 1
        elif self.frequency == "weekly":
            interval = 7
        else:
            return None   # as-needed tasks don't auto-recur

        next_task = Task(
            description=self.description,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            scheduled_time=self.scheduled_time,
            last_completed_day=current_day,
        )
        next_task.due_day = current_day + interval
        return next_task

    # ------------------------------------------------------------------
    # Validation / sorting helpers
    # ------------------------------------------------------------------

    def priority_rank(self) -> int:
        """Return 3 / 2 / 1 for high / medium / low. Used to sort tasks."""
        return {"high": 3, "medium": 2, "low": 1}.get(self.priority, 0)

    def is_valid(self) -> bool:
        """Return True if description is non-empty, duration >= 1, and priority is valid."""
        return (
            bool(self.description and self.description.strip())
            and self.duration_minutes >= 1
            and self.priority in self.VALID_PRIORITIES
        )

    def __repr__(self) -> str:
        """Return a readable string showing description, duration, priority, frequency, and status."""
        status = "done" if self.completed else "pending"
        time_part = f" @{self.scheduled_time}" if self.scheduled_time else ""
        return (
            f'Task("{self.description}"{time_part}, {self.duration_minutes}min, '
            f'{self.priority}, {self.frequency}, {status})'
        )


class Pet:
    """The animal being cared for. Stores pet details and owns a list of tasks."""

    def __init__(self, name: str, species: str):
        self.name = name        # str        — e.g. "Mochi"
        self.species = species  # str        — "dog", "cat", or "other"
        self.tasks: list = []   # list[Task] — all tasks registered for this pet

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Append a task. Raise ValueError if the task fails is_valid()."""
        if not task.is_valid():
            raise ValueError(f"Invalid task: {task!r}")
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task matching description (case-insensitive); return True if found."""
        for i, t in enumerate(self.tasks):
            if t.description.lower() == description.lower():
                self.tasks.pop(i)
                return True
        return False

    def get_pending_tasks(self) -> list:
        """Return only tasks that have not yet been marked complete."""
        return [t for t in self.tasks if not t.completed]

    def total_task_minutes(self) -> int:
        """Return the sum of duration_minutes across all tasks for this pet."""
        return sum(t.duration_minutes for t in self.tasks)

    def __repr__(self) -> str:
        """Return a readable string showing the pet's name, species, and task count."""
        return f'Pet("{self.name}", {self.species}, {len(self.tasks)} task(s))'


class Owner:
    """The human user. Manages one or more pets and provides access to all their tasks."""

    def __init__(self, name: str, available_minutes: int = 120):
        self.name = name                            # str       — owner's name
        self.available_minutes = available_minutes  # int       — daily time budget
        self.pets: list = []                        # list[Pet] — all pets this owner cares for

    # ------------------------------------------------------------------
    # Pet management
    # ------------------------------------------------------------------

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove the first pet matching name (case-insensitive); return True if found."""
        for i, p in enumerate(self.pets):
            if p.name.lower() == name.lower():
                self.pets.pop(i)
                return True
        return False

    # ------------------------------------------------------------------
    # Task access — used by Scheduler to retrieve tasks without
    # needing to know about the internal pets list structure.
    # ------------------------------------------------------------------

    def get_all_tasks(self) -> list:
        """Return a flat list of (pet, task) tuples across every pet the owner has."""
        result = []
        for pet in self.pets:
            for task in pet.tasks:
                result.append((pet, task))
        return result

    def get_tasks_by_pet(self) -> dict:
        """Return a dict mapping each pet's name to its task list, for grouped UI display."""
        return {pet.name: pet.tasks for pet in self.pets}

    def __repr__(self) -> str:
        """Return a readable string showing the owner's name, time budget, and pet count."""
        return (
            f'Owner("{self.name}", {self.available_minutes} min available, '
            f'{len(self.pets)} pet(s))'
        )


class Schedule:
    """The output produced by Scheduler.generate_plan().
    Holds the ordered list of tasks that fit the day and those that were skipped."""

    def __init__(
        self,
        owner_name: str,
        items: list,
        skipped: list,
        total_minutes_used: int,
        available_minutes: int,
    ):
        self.owner_name = owner_name                  # str        — for display
        self.items = items                            # list[dict] — scheduled tasks
        self.skipped = skipped                        # list[dict] — excluded tasks
        self.total_minutes_used = total_minutes_used  # int        — minutes consumed
        self.available_minutes = available_minutes    # int        — owner's budget

        # Each dict in items / skipped has the shape:
        # {
        #   "pet":              str,   <- which pet the task belongs to
        #   "description":      str,
        #   "duration_minutes": int,
        #   "priority":         str,
        #   "frequency":        str,
        #   "reason":           str    <- natural-language explanation for the UI
        # }

    def has_items(self) -> bool:
        """Return True if at least one task was scheduled."""
        return len(self.items) > 0

    def summary(self) -> str:
        """Return a markdown-formatted plan summary suitable for st.markdown()."""
        lines = [
            f"**{self.owner_name}'s plan:** "
            f"{self.total_minutes_used} of {self.available_minutes} minutes used.",
        ]
        if self.items:
            lines.append("\n**Scheduled tasks:**")
            for item in self.items:
                lines.append(
                    f"- [{item['pet']}] {item['description']} "
                    f"({item['duration_minutes']} min, {item['priority']} priority, "
                    f"{item['frequency']}) — {item['reason']}"
                )
        if self.skipped:
            lines.append("\n**Skipped tasks:**")
            for item in self.skipped:
                lines.append(
                    f"- [{item['pet']}] {item['description']} "
                    f"({item['duration_minutes']} min, {item['priority']} priority) "
                    f"— {item['reason']}"
                )
        return "\n".join(lines)


class Scheduler:
    """The brain of PawPal+.

    Retrieves tasks from all of an owner's pets via Owner.get_all_tasks(),
    organises them by priority, and generates a daily care plan that fits
    within the owner's available time.
    """

    def __init__(self, owner: Owner):
        self.owner = owner  # Owner — single source of truth for pets, tasks, and time budget

    # ------------------------------------------------------------------
    # Task retrieval — delegates to Owner so Scheduler never touches
    # owner.pets directly.
    # ------------------------------------------------------------------

    def get_all_tasks(self) -> list:
        """Return every (pet, task) pair across all of the owner's pets."""
        return self.owner.get_all_tasks()

    def get_pending_tasks(self) -> list:
        """Return only (pet, task) pairs where task.completed is False."""
        return [(pet, task) for pet, task in self.owner.get_all_tasks() if not task.completed]

    def mark_task_complete(
        self, pet_name: str, task_description: str, current_day: int = 0
    ) -> "Task | None":
        """Mark a task complete and auto-enqueue the next occurrence for daily/weekly tasks.

        For 'daily'  tasks: creates a new instance with due_day = current_day + 1.
        For 'weekly' tasks: creates a new instance with due_day = current_day + 7.
        For 'as-needed' tasks: marks complete only, returns None.

        Returns the newly queued Task, or None if no next occurrence was created.
        Raises ValueError if the pet or task cannot be found.
        """
        pet = next(
            (p for p in self.owner.pets if p.name.lower() == pet_name.lower()),
            None,
        )
        if pet is None:
            raise ValueError(f"No pet named '{pet_name}'.")

        task = next(
            (t for t in pet.tasks if t.description.lower() == task_description.lower()),
            None,
        )
        if task is None:
            raise ValueError(f"No task '{task_description}' for {pet.name}.")

        task.mark_complete()

        next_task = task.next_occurrence(current_day)
        if next_task is not None:
            pet.add_task(next_task)

        return next_task

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    def filter_by_pet(self, pet_name: str) -> list:
        """Return every (pet, task) pair belonging to the named pet.

        Comparison is case-insensitive, so "mochi" matches a pet registered as "Mochi".
        Tasks for all other pets are excluded.  The original insertion order of
        the matched pet's tasks is preserved.

        Args:
            pet_name (str): The name of the pet whose tasks should be returned.

        Returns:
            list[tuple[Pet, Task]]: Matched (pet, task) pairs, or an empty list
            if no pet with that name exists.
        """
        return [
            (pet, task) for pet, task in self.owner.get_all_tasks()
            if pet.name.lower() == pet_name.lower()
        ]

    def filter_by_status(self, completed: bool) -> list:
        """Return every (pet, task) pair whose completion status matches the argument.

        Useful for answering "what still needs doing today?" (completed=False) or
        "what has already been finished?" (completed=True) across all pets at once.
        Results span every pet registered with the owner and preserve insertion order.

        Args:
            completed (bool): Pass True to retrieve finished tasks, False for pending ones.

        Returns:
            list[tuple[Pet, Task]]: All (pet, task) pairs where task.completed == completed.
        """
        return [
            (pet, task) for pet, task in self.owner.get_all_tasks()
            if task.completed == completed
        ]

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self) -> list:
        """Find pairs of tasks whose scheduled time windows overlap.

        Only tasks with a scheduled_time are considered.
        Returns a list of dicts, each describing one conflict.
        """
        timed = [
            (pet, task) for pet, task in self.owner.get_all_tasks()
            if task.scheduled_time is not None
        ]
        # itertools.combinations(timed, 2) visits every unique pair exactly once —
        # the same guarantee as the manual range(i) / range(i+1, …) double-loop,
        # but without the index arithmetic or off-by-one risk.
        conflicts = []
        for (pet_a, task_a), (pet_b, task_b) in combinations(timed, 2):
            start_a = task_a.time_as_minutes()
            end_a   = start_a + task_a.duration_minutes
            start_b = task_b.time_as_minutes()
            end_b   = start_b + task_b.duration_minutes
            if start_a < end_b and start_b < end_a:
                overlap = min(end_a, end_b) - max(start_a, start_b)
                conflicts.append({
                    "pet_a":           pet_a.name,
                    "task_a":          task_a.description,
                    "time_a":          task_a.scheduled_time,
                    "pet_b":           pet_b.name,
                    "task_b":          task_b.description,
                    "time_b":          task_b.scheduled_time,
                    "overlap_minutes": overlap,
                })
        return conflicts

    def conflict_warnings(self) -> list:
        """Return a list of human-readable warning strings for every scheduling conflict.

        Lightweight strategy: never raises — always returns a list (empty = no conflicts).
        Each warning describes which tasks overlap, which pets they belong to,
        and by how many minutes the windows collide.
        Callers can print, log, or display these strings however they like.
        """
        warnings = []
        for c in self.detect_conflicts():
            same_pet = c["pet_a"] == c["pet_b"]
            if same_pet:
                scope = f"{c['pet_a']}"
            else:
                scope = f"{c['pet_a']} and {c['pet_b']}"
            warnings.append(
                f"WARNING: Scheduling conflict for {scope} — "
                f'"{c["task_a"]}" (@{c["time_a"]}) overlaps '
                f'"{c["task_b"]}" (@{c["time_b"]}) '
                f"by {c['overlap_minutes']} minute(s)."
            )
        return warnings

    # ------------------------------------------------------------------
    # Organisation helpers
    # ------------------------------------------------------------------

    def sort_by_time(self, pairs: list) -> list:
        """Return (pet, task) pairs sorted chronologically by scheduled_time.

        Uses sorted() with a lambda key that compares "HH:MM" strings directly.
        Zero-padded strings ("07:00", "13:30") sort correctly as plain strings,
        so no numeric conversion is needed.
        Tasks without a scheduled_time are placed at the end ("99:99" sentinel).
        """
        return sorted(
            pairs,
            key=lambda pt: pt[1].scheduled_time if pt[1].scheduled_time is not None else "99:99",
        )

    def _sort_tasks(self, pairs: list) -> list:
        """Sort (pet, task) pairs for plan generation: timed tasks first, then untimed by priority.

        Produces a two-group ordering:
          Group 0 — tasks that have a scheduled_time, sorted by clock time (earliest first).
                    Ties within the same minute are broken by priority (high first), then
                    alphabetically by description for determinism.
          Group 1 — tasks without a scheduled_time, sorted by priority (high first), then
                    alphabetically.

        This ordering is consumed by generate_plan() so the greedy budget loop processes
        time-anchored tasks before floating ones.

        Args:
            pairs (list[tuple[Pet, Task]]): The (pet, task) pairs to sort.

        Returns:
            list[tuple[Pet, Task]]: A new sorted list; the input is not modified.
        """
        def sort_key(pt):
            task = pt[1]
            t = task.time_as_minutes()
            if t is not None:
                # Timed tasks: group 0, ordered by clock time, then priority
                return (0, t, -task.priority_rank(), task.description.lower())
            # Untimed tasks: group 1, ordered by priority then alpha
            return (1, 0, -task.priority_rank(), task.description.lower())

        return sorted(pairs, key=sort_key)

    def tasks_by_priority(self) -> list:
        """Return all pending tasks sorted high → medium → low."""
        return self._sort_tasks(self.get_pending_tasks())

    # ------------------------------------------------------------------
    # Plan generation
    # ------------------------------------------------------------------

    def generate_plan(self, current_day: int = 0) -> Schedule:
        """Build and return a Schedule by greedily fitting pending, due tasks into the time budget.

        current_day: day counter used to evaluate weekly/recurring task eligibility.
        """
        due_pending = [
            (pet, task) for pet, task in self.get_pending_tasks()
            if task.is_due_today(current_day)
        ]
        sorted_pairs = self._sort_tasks(due_pending)
        used = 0
        items = []
        skipped = []

        for pet, task in sorted_pairs:
            if used + task.duration_minutes <= self.owner.available_minutes:
                time_note = f" scheduled {task.scheduled_time}," if task.scheduled_time else ""
                items.append({
                    "pet": pet.name,
                    "description": task.description,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "frequency": task.frequency,
                    "scheduled_time": task.scheduled_time,
                    "reason": (
                        f"Included:{time_note} {task.priority} priority, "
                        f"fits within {self.owner.available_minutes}-minute budget."
                    ),
                })
                used += task.duration_minutes
            else:
                over = (used + task.duration_minutes) - self.owner.available_minutes
                skipped.append({
                    "pet": pet.name,
                    "description": task.description,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "frequency": task.frequency,
                    "reason": f"Skipped: would exceed time budget by {over} minute(s).",
                })

        return Schedule(
            owner_name=self.owner.name,
            items=items,
            skipped=skipped,
            total_minutes_used=used,
            available_minutes=self.owner.available_minutes,
        )
