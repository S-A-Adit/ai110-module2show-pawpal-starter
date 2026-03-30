# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

**Three core user actions:**

1. **Enter owner and pet information.** The user provides basic profile details — their name, the pet's name, and how much time they have available in a day. This sets the constraints that the scheduler will work within and personalizes the experience.

2. **Add and edit care tasks.** The user can create tasks such as walks, feeding, medication, grooming, or enrichment activities. Each task has at minimum a duration (how long it takes) and a priority (how important it is). The user can also edit or remove existing tasks to keep the list current.

3. **Generate and view a daily care schedule.** The user requests a daily plan, and the app produces an ordered schedule of tasks that fits within the available time. The plan is displayed clearly and includes an explanation of why tasks were chosen and ordered that way — helping the owner understand and trust the recommendations.

The system uses five classes, all defined in `scheduler.py`:

**`Task`** — holds one care activity. Attributes: `title` (str), `duration_minutes` (int), `priority` (str: low/medium/high). Methods: `priority_rank()` converts priority to a number for sorting; `is_valid()` validates inputs before scheduling; `__repr__()` for debugging.

**`Pet`** — represents the animal. Attributes: `name`, `species`, `tasks` (list of Task). Methods: `add_task()` appends a validated task; `remove_task()` removes by title; `total_task_minutes()` sums all durations. Tasks belong to Pet, not Owner, so the design can support multiple pets in the future.

**`Owner`** — represents the human user. Attributes: `name`, `available_minutes` (default 120). `available_minutes` lives here because it's the human's time budget, not a property of the animal.

**`Scheduler`** — the core logic class. Attributes: `owner`, `pet`. Methods: `generate()` is the public entry point that runs a greedy scheduling algorithm; `_sort_tasks()` is a private helper that orders tasks high → medium → low priority, with alphabetical tiebreaking for determinism.

**`Schedule`** — the output object. Attributes: `items` (included tasks as dicts), `skipped` (excluded tasks as dicts), `total_minutes_used`, `available_minutes`. Each dict includes a `"reason"` key with a natural-language explanation of why the task was included or skipped. Methods: `summary()` produces a markdown string for the UI; `has_items()` lets the UI decide whether to render results.

Data flow: `Owner` + `Pet` (with `Task` list) → `Scheduler.generate()` → `Schedule` → displayed in `app.py`.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

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
