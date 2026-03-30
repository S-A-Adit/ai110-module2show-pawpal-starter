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

The scheduler considers four constraints:

1. **Time budget** (`Owner.available_minutes`) — the hard cap. A task that would push total minutes over the budget is skipped entirely. This is the binding constraint because it represents a real-world limit the owner cannot negotiate around.
2. **Priority** (`Task.priority`: high / medium / low) — the tiebreaker and ordering rule. `_sort_tasks()` evaluates high-priority tasks first so the greedy loop fills the budget with the most important work before lower-priority tasks compete for the remaining time.
3. **Scheduled clock time** (`Task.scheduled_time`) — an anchor constraint. Timed tasks are placed ahead of all floating tasks in the sort order regardless of priority, because a task with a fixed time (e.g., "8:00 AM medication") cannot be freely rescheduled the way an untimed grooming session can.
4. **Frequency and due-day** (`Task.frequency`, `Task.due_day`) — an eligibility gate. `is_due_today()` screens out weekly tasks completed fewer than seven days ago and future occurrences whose `due_day` hasn't arrived yet, so the plan never double-counts a task.

Time was chosen as the primary constraint because it is objective and non-negotiable — the owner has a fixed number of minutes. Priority was secondary because it encodes the owner's values, not an external limit. Clock time was tertiary because anchored tasks narrow the solution space before priority-based sorting begins.

**b. Tradeoffs**

**Tradeoff: conflict detection is advisory, not enforced — the schedule can include tasks that overlap.**

`conflict_warnings()` and `generate_plan()` are completely independent. When you call `generate_plan()`, it picks tasks greedily by time and priority; it never consults `conflict_warnings()` and never removes or reschedules a task because it overlaps with another. The result is that a generated schedule can contain two tasks at the same time slot while also printing a warning that they conflict. The owner sees both the conflict notice and a schedule that still includes both tasks, and must resolve the clash manually.

The alternative — having `generate_plan()` automatically drop one of the conflicting tasks — would require the scheduler to make a value judgment it isn't equipped to make: which task to sacrifice, whether to shift start times, or whether to ask the user. Embedding that decision silently inside the algorithm would hide the conflict from the owner rather than informing them. Keeping the two concerns separate (detect vs. schedule) is a deliberate choice: the scheduler's job is to fit tasks into a time budget, and the conflict detector's job is to surface information. Mixing them would make both harder to reason about and test.

This tradeoff is reasonable for an MVP where the owner is expected to look at the output and make final decisions. It would become unreasonable in a fully automated system where the schedule is executed without human review — at that point, enforcing conflict resolution inside `generate_plan()` would be necessary.

---

## 3. AI Collaboration

**a. How you used AI**

I used VS Code Copilot across all three phases of the project, but in different ways at each stage.

**Phase 1 — Design:** Copilot Chat with `#codebase` context was the most useful feature here. I described the scenario in plain English and asked it to identify the nouns (potential classes) and verbs (potential methods). It surfaced `Task`, `Pet`, `Owner`, `Scheduler`, and `Schedule` as candidates, which matched my own thinking and gave me confidence to commit to that structure. The most effective prompt type was "given this user story, what responsibilities belong to each class?" because it forced the AI to reason about separation of concerns rather than just generating code.

**Phase 2 — Implementation:** Inline completions handled the mechanical boilerplate — constructors, `__repr__` methods, property assignments — which freed me to focus on the logic inside methods like `_sort_tasks()` and `detect_conflicts()`. The most effective prompts were narrow and specific: "complete this method given these two inputs and this expected output" rather than "write the Scheduler class." Narrower scope meant the AI stayed on task and I could verify the output in one read.

**Phase 3 — Testing and UI:** I used Copilot Chat with `#file:pawpal_system.py` to ask "what edge cases for `detect_conflicts` should I test?" It suggested the adjacent-task false-positive case (`end_a == start_b` should not conflict), which I had not considered. I used `#file:app.py` to ask how to replace the raw `st.markdown(plan.summary())` call with a proper table — it suggested `st.dataframe`, I modified that to `st.table` for a cleaner static display.

**b. Judgment and verification**

The clearest moment where I rejected an AI suggestion involved the `Scheduler` class structure. The initial design in the reflection had `Scheduler` holding two separate attributes — `self.owner` and `self.pet` — passed in independently. When I asked Copilot to generate the constructor, it faithfully reproduced that two-parameter signature. I rejected this because it made `Scheduler` incompatible with a multi-pet `Owner`: there would be no way to schedule tasks across all pets without calling the scheduler once per pet and merging results manually.

I evaluated the suggestion by asking: "what happens if Jordan has two dogs?" The two-parameter design breaks immediately. The fix was to remove `pet` from `Scheduler.__init__` entirely and have `Scheduler` retrieve tasks through `Owner.get_all_tasks()`, which already returns a flat `(pet, task)` list across every pet. I verified the change was safe by checking every method in `Scheduler` — none of them needed direct `pet` access once `get_all_tasks()` was in place. The AI's suggestion was locally correct but architecturally wrong; catching that required holding the broader design in my head rather than evaluating the suggestion in isolation.

**c. Separate chat sessions for different phases**

Using separate chat sessions for design, implementation, and UI kept each conversation focused on one type of thinking. The design session stayed at the level of classes and responsibilities without drifting into implementation syntax. The implementation session could reference `#file:pawpal_system.py` specifically without dragging in UI concerns. The UI session could treat the backend as a black box and focus purely on display logic.

The practical benefit was that each session had a clear "done" state. When the design session produced a UML diagram I was satisfied with, I closed it. When the implementation session produced passing tests, I closed it. There was no accumulated context from earlier decisions clouding the current conversation. Starting fresh also meant I had to re-explain the system briefly at the top of each session, which turned out to be useful — articulating "here is what exists and what I need next" is exactly the kind of architectural summary that keeps a project coherent.

**d. Being the "lead architect" with powerful AI tools**

The most important thing I learned is that the AI is an expert executor, not a decision-maker. It can implement any design you describe, and it will do so faster and with fewer typos than writing by hand. But it has no stake in whether the design is good. It will implement a design that couples classes too tightly, skips edge cases, or solves a slightly different problem than the one you have — not out of carelessness, but because it is optimizing for local coherence (does this code make sense?) rather than global correctness (does this code solve the right problem?).

Being the lead architect meant I had to hold three things the AI cannot: the "why" behind each design decision, the user's actual constraints (a pet owner with limited time, not a scheduling algorithm exercise), and the standard for "done." Every time I accepted a suggestion, I asked whether it would survive a design review — not just "does it run?" but "is this the right abstraction?" That discipline is what kept `Scheduler` from accumulating pet-management responsibilities that belong on `Owner`, and what kept the conflict detection advisory rather than silently dropping tasks.

The most useful reframe was treating the AI as a senior engineer who is very fast and very literal. You still have to write the design document. You still have to review the pull request. The collaboration is most productive when you are specific about what you want, skeptical about what you receive, and willing to push back when the suggestion is locally correct but architecturally wrong.

---

## 4. Testing and Verification

**a. What you tested**

The 12 tests cover five behavioral areas:

1. **Task lifecycle** — `mark_complete()` flips `completed` to `True`; `add_task()` increases the pet's task count by exactly one. These are the most fundamental operations and the first thing any other feature depends on, so they had to be verified before anything else.

2. **Sorting** — three tests covering `sort_by_time()` (chronological order), `_sort_tasks()` (timed before untimed), and tie-breaking (same `scheduled_time`, high priority wins). Sorting is the core of the scheduling algorithm — if it is wrong, every generated plan is wrong, but silently, which is the worst kind of bug.

3. **Recurrence** — four tests: completing a daily task creates a next occurrence with `due_day = current_day + 1`; the new occurrence is not due on the current day but is due the next; a weekly task is not due again for seven days; an as-needed task returns `None` from `next_occurrence()`. Recurrence logic has tricky off-by-one risk, so explicit boundary tests were important.

4. **Conflict detection** — three tests: overlapping windows produce exactly one conflict with the correct `overlap_minutes`; adjacent tasks (end == start) produce zero conflicts; untimed tasks are never flagged. The false-positive test for adjacent tasks was added after realising the interval test `start_a < end_b and start_b < end_a` correctly excludes touching-but-not-overlapping windows — worth confirming explicitly.

5. **Conflict warnings** — one test verifying that `conflict_warnings()` returns human-readable strings containing `"WARNING"` and both task names. This ensures the UI has useful content to display, not just a boolean flag.

**b. Confidence**

★★★★☆ (4/5). The scheduling logic is well-covered and all 12 tests pass. One star is withheld because the Streamlit UI (`app.py`) has no automated tests — form submissions, session state persistence, and display rendering are verified only by running the app manually. Edge cases I would test next: `generate_plan()` with zero available minutes, adding the same task description twice to the same pet, and `filter_by_pet()` with a name that matches no pet.

---

## 5. Reflection

**a. What went well**

The separation of concerns across the five classes held up throughout the entire build. I never had a moment where adding a new feature required rewriting a class that "shouldn't" need to change. When conflict detection was added, it went into `Scheduler` without touching `Task`, `Pet`, or `Owner`. When recurrence was added, `Task.next_occurrence()` was self-contained and `Scheduler.mark_task_complete()` just called it. The UML I drafted in Phase 1 remained structurally accurate through Phase 3 — the attributes and methods changed, but the relationships did not. That stability is the clearest sign that the initial design was right.

**b. What you would improve**

I would redesign the relationship between conflict detection and plan generation. Currently `detect_conflicts()` and `generate_plan()` are completely independent: the plan can include two tasks that conflict, and the owner must resolve the clash manually. For an MVP this is defensible, but it makes the UI feel inconsistent — it warns about the problem and then produces a schedule that ignores the warning. In a next iteration I would give `generate_plan()` an optional `resolve_conflicts` flag: when set, it would shift timed tasks to the earliest available slot rather than silently including both. That keeps the default behaviour simple while giving power users a smarter path.

**c. Key takeaway**

The most important thing I learned is that writing the design document first — even a rough one — transforms AI collaboration from reactive to intentional. Without a UML diagram, every Copilot suggestion is evaluated in a vacuum: does this code compile? does it do something reasonable? With a diagram, every suggestion is evaluated against a standard: does this belong on this class? does this coupling break the design? The diagram is not a constraint that slows you down; it is a decision already made, so you are not making it again under pressure while reading generated code. The skill of being a lead architect when working with AI is mostly the skill of making decisions early, writing them down, and then using that document as the lens through which you evaluate everything the AI produces.
