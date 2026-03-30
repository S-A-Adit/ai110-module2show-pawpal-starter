# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

**Three core user actions:**

1. **Enter owner and pet information.** The user provides basic profile details — their name, the pet's name, and how much time they have available in a day. This sets the constraints that the scheduler will work within and personalizes the experience.

2. **Add and edit care tasks.** The user can create tasks such as walks, feeding, medication, grooming, or enrichment activities. Each task has at minimum a duration (how long it takes) and a priority (how important it is). The user can also edit or remove existing tasks to keep the list current.

3. **Generate and view a daily care schedule.** The user requests a daily plan, and the app produces an ordered schedule of tasks that fits within the available time. The plan is displayed clearly and includes an explanation of why tasks were chosen and ordered that way — helping the owner understand and trust the recommendations.

The system uses five classes, all defined in `pawpal_system.py`. Each class has a single, clear responsibility:

**`Task`** — represents one care activity. Attributes: `title` (str), `duration_minutes` (int), `priority` (str: `"low"`, `"medium"`, or `"high"`). Methods: `priority_rank()` converts the priority string to a number (3/2/1) so tasks can be sorted; `is_valid()` enforces that a task has a non-empty title, a duration of at least one minute, and a recognised priority before it is accepted by the scheduler; `__repr__()` produces a readable string for debugging.

**`Pet`** — represents the animal being cared for. Attributes: `name`, `species`, `tasks` (a list of `Task` objects). Methods: `add_task()` appends a validated `Task` and raises `ValueError` on bad input; `remove_task()` finds and removes a task by title (case-insensitive); `total_task_minutes()` sums all task durations and is useful for warning the user when the total workload exceeds their time budget. Tasks live on `Pet`, not `Owner`, so a future multi-pet extension does not require restructuring.

**`Owner`** — represents the human user. Attributes: `name`, `available_minutes` (defaults to 120). The time budget is an attribute of the owner because it reflects the human's day, not anything intrinsic to the animal.

**`Scheduler`** — the core logic class. Attributes: `owner`, `pet`. Methods: `generate()` is the public entry point that runs the greedy scheduling algorithm and returns a `Schedule`; `_sort_tasks()` is a private helper that sorts `pet.tasks` by `priority_rank()` descending, breaking ties alphabetically for determinism.

**`Schedule`** — the output object returned by `Scheduler.generate()`. Attributes: `owner_name`, `pet_name`, `items` (list of dicts for included tasks), `skipped` (list of dicts for excluded tasks), `total_minutes_used`, `available_minutes`. Each dict contains `title`, `duration_minutes`, `priority`, and a `"reason"` string — the natural-language explanation shown in the UI. Methods: `summary()` returns a markdown string for `st.markdown()`; `has_items()` lets the UI decide whether to render the results section.

Data flow: `Owner` + `Pet` (with `Task` list) → `Scheduler.generate()` → `Schedule` → displayed in `app.py`.

**b. Design changes**

Yes. Reviewing `pawpal_system.py` against the initial design surfaced three issues:

**Change 1 — Added `owner_name` to `Schedule` (implemented).**
The original `Schedule.__init__` stored `pet_name` but not `owner_name`. This meant `summary()` could say "Plan for Mochi" but not "Jordan's plan for Mochi." Since the owner's name is available at generation time (it's on the `Owner` object passed to `Scheduler`), there was no reason to discard it. Added `owner_name` as the first parameter of `Schedule.__init__` so the summary can personalise the output.

**Change 2 — No direct `Owner` → `Pet` relationship (documented, not changed).**
In the design, `Owner` and `Pet` are independent objects with no link to each other — they are joined only when both are passed into `Scheduler`. This means the model has no concept of an owner "having" a pet. For a single-pet MVP this is fine: the UI always supplies both together, and the scheduler always receives both. Adding an `owner.pet` attribute would not simplify any logic at this stage and would complicate future multi-pet support. Kept as-is, noted as a deliberate simplification.

**Change 3 — Greedy algorithm cannot reconsider skipped tasks (documented, not changed).**
The scheduler evaluates tasks in priority order and permanently skips any task that would exceed the remaining budget. This means a long high-priority task that doesn't fit is marked as skipped, even if a later smaller task creates no new room for it. This is a known limitation of greedy bin-packing. Solving it properly (e.g. with backtracking or dynamic programming) is out of scope for this MVP. The tradeoff is reasonable because: (a) most pet care tasks are small enough that the budget cap rarely causes surprising skips, and (b) the scheduler shows the skipped list with reasons, so the owner is always informed.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
