# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

PawPal+ goes beyond a simple priority list. The `Scheduler` class in `pawpal_system.py` includes four algorithmic features added in Phase 3:

**Sort by time**
`sort_by_time(pairs)` orders tasks chronologically using a lambda key that compares zero-padded `"HH:MM"` strings directly — no numeric conversion needed. Tasks without a `scheduled_time` float to the end automatically.

**Filter by pet or status**
`filter_by_pet(name)` isolates all tasks for one pet. `filter_by_status(completed)` returns only done or only pending tasks across every pet at once. Both methods return plain lists so they compose freely with `sort_by_time`.

**Recurring task auto-recurrence**
`Task.next_occurrence(current_day)` clones a completed task and sets its `due_day` to `current_day + 1` (daily) or `current_day + 7` (weekly). `Scheduler.mark_task_complete()` calls this automatically and appends the new instance to the pet's task list, so recurring care never has to be re-entered manually. Tasks with frequency `"as-needed"` opt out and return `None`.

**Conflict detection**
`detect_conflicts()` uses `itertools.combinations` to check every unique pair of timed tasks for window overlap (`start_a < end_b and start_b < end_a`). `conflict_warnings()` wraps those results into plain warning strings — it never raises, so the schedule always generates even when overlaps exist. The owner is informed and makes the final call.

## Testing PawPal+

### Run the tests

```bash
python -m pytest
```

### What the tests cover

| Area | Tests |
|---|---|
| **Task lifecycle** | Marking a task complete flips `completed` to `True`; adding a task increases the pet's task list |
| **Sorting** | `sort_by_time()` returns tasks in chronological order; timed tasks always appear before untimed ones; same-time ties break by priority (high before low) |
| **Recurrence** | Completing a daily task auto-creates a next occurrence due the following day; weekly tasks are not due again for 7 days; `as-needed` tasks never recur |
| **Conflict detection** | Overlapping timed tasks produce exactly one conflict entry with the correct overlap in minutes; adjacent (edge-touching) tasks produce no false positive; untimed tasks are never flagged |
| **Conflict warnings** | `conflict_warnings()` returns human-readable strings that include `"WARNING"` and both task names |

### Confidence Level

★★★★☆ (4 / 5)

The scheduling logic — sorting, recurrence, and conflict detection — is well-covered by the 12 tests above, all of which pass. A fifth star is withheld because the Streamlit UI layer (`app.py`) has no automated tests yet, so end-to-end user flows (form input, session state, display rendering) are only verified manually.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
