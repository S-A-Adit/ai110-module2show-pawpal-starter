class Task:
    """A single pet care activity with a title, duration, and priority."""

    VALID_PRIORITIES = {"low", "medium", "high"}

    def __init__(self, title: str, duration_minutes: int, priority: str):
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority

    def priority_rank(self) -> int:
        """Return 3/2/1 for high/medium/low priority. Used for sorting."""
        ranks = {"high": 3, "medium": 2, "low": 1}
        return ranks.get(self.priority, 0)

    def is_valid(self) -> bool:
        """Return True if this task has a non-empty title, duration >= 1, and valid priority."""
        return (
            bool(self.title and self.title.strip())
            and self.duration_minutes >= 1
            and self.priority in self.VALID_PRIORITIES
        )

    def __repr__(self) -> str:
        return f'Task("{self.title}", {self.duration_minutes}min, {self.priority})'


class Pet:
    """The animal being cared for. Owns the list of care tasks."""

    def __init__(self, name: str, species: str):
        self.name = name
        self.species = species
        self.tasks: list = []

    def add_task(self, task: Task) -> None:
        """Append a task. Raises ValueError if the task is invalid."""
        if not task.is_valid():
            raise ValueError(f"Invalid task: {task!r}")
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove the first task matching title (case-insensitive). Returns True if found."""
        for i, t in enumerate(self.tasks):
            if t.title.lower() == title.lower():
                self.tasks.pop(i)
                return True
        return False

    def total_task_minutes(self) -> int:
        """Return the sum of all task durations."""
        return sum(t.duration_minutes for t in self.tasks)

    def __repr__(self) -> str:
        return f'Pet("{self.name}", {self.species}, {len(self.tasks)} tasks)'


class Owner:
    """The human user. Holds their name and daily time budget."""

    def __init__(self, name: str, available_minutes: int = 120):
        self.name = name
        self.available_minutes = available_minutes

    def __repr__(self) -> str:
        return f'Owner({self.name}, {self.available_minutes} min available)'


class Schedule:
    """The output of the Scheduler — included tasks, skipped tasks, and a summary."""

    def __init__(
        self,
        pet_name: str,
        items: list,
        skipped: list,
        total_minutes_used: int,
        available_minutes: int,
    ):
        self.pet_name = pet_name
        self.items = items          # list of dicts: title, duration_minutes, priority, reason
        self.skipped = skipped      # list of dicts: title, duration_minutes, priority, reason
        self.total_minutes_used = total_minutes_used
        self.available_minutes = available_minutes

    def has_items(self) -> bool:
        """Return True if at least one task was scheduled."""
        return len(self.items) > 0

    def summary(self) -> str:
        """Return a plain-text summary suitable for st.markdown()."""
        lines = [
            f"**Plan for {self.pet_name}:** "
            f"{self.total_minutes_used} of {self.available_minutes} minutes used.",
        ]
        if self.items:
            lines.append("\n**Scheduled tasks:**")
            for item in self.items:
                lines.append(
                    f"- {item['title']} ({item['duration_minutes']} min, "
                    f"{item['priority']} priority) — {item['reason']}"
                )
        if self.skipped:
            lines.append("\n**Skipped tasks:**")
            for item in self.skipped:
                lines.append(
                    f"- {item['title']} ({item['duration_minutes']} min, "
                    f"{item['priority']} priority) — {item['reason']}"
                )
        return "\n".join(lines)


class Scheduler:
    """Generates a daily care schedule by greedily fitting tasks into the owner's time budget."""

    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet

    def _sort_tasks(self) -> list:
        """Return tasks sorted by priority (high first), ties broken alphabetically."""
        return sorted(
            self.pet.tasks,
            key=lambda t: (-t.priority_rank(), t.title.lower()),
        )

    def generate(self) -> Schedule:
        """Build and return a Schedule by fitting tasks into the available time budget."""
        sorted_tasks = self._sort_tasks()
        used = 0
        items = []
        skipped = []

        for task in sorted_tasks:
            if used + task.duration_minutes <= self.owner.available_minutes:
                items.append({
                    "title": task.title,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "reason": (
                        f"Included: {task.priority} priority, "
                        f"fits within {self.owner.available_minutes}-minute budget."
                    ),
                })
                used += task.duration_minutes
            else:
                over = (used + task.duration_minutes) - self.owner.available_minutes
                skipped.append({
                    "title": task.title,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "reason": f"Skipped: would exceed time budget by {over} minute(s).",
                })

        return Schedule(
            pet_name=self.pet.name,
            items=items,
            skipped=skipped,
            total_minutes_used=used,
            available_minutes=self.owner.available_minutes,
        )
