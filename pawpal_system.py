# pawpal_system.py
# Logic layer for PawPal+: all backend classes live here.


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
    ):
        self.description = description          # str  — what the task is
        self.duration_minutes = duration_minutes  # int  — how long it takes (>= 1)
        self.priority = priority                # str  — "low", "medium", or "high"
        self.frequency = frequency              # str  — "daily", "weekly", or "as-needed"
        self.completed = False                  # bool — completion status for today

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
        return (
            f'Task("{self.description}", {self.duration_minutes}min, '
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

    # ------------------------------------------------------------------
    # Organisation helpers
    # ------------------------------------------------------------------

    def _sort_tasks(self, pairs: list) -> list:
        """Sort (pet, task) pairs by priority descending, then alphabetically by description."""
        return sorted(pairs, key=lambda pt: (-pt[1].priority_rank(), pt[1].description.lower()))

    def tasks_by_priority(self) -> list:
        """Return all pending tasks sorted high → medium → low."""
        return self._sort_tasks(self.get_pending_tasks())

    # ------------------------------------------------------------------
    # Plan generation
    # ------------------------------------------------------------------

    def generate_plan(self) -> Schedule:
        """Build and return a Schedule by greedily fitting pending tasks into the time budget."""
        sorted_pairs = self._sort_tasks(self.get_pending_tasks())
        used = 0
        items = []
        skipped = []

        for pet, task in sorted_pairs:
            if used + task.duration_minutes <= self.owner.available_minutes:
                items.append({
                    "pet": pet.name,
                    "description": task.description,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "frequency": task.frequency,
                    "reason": (
                        f"Included: {task.priority} priority, "
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
