# PawPal+ — Daily Pet Care Planner

A Streamlit app that helps busy pet owners build a realistic daily care schedule.
Enter your time budget, register your pets, add tasks with priorities and optional clock times,
and PawPal+ generates an ordered plan — complete with conflict warnings and skip explanations.

---

## 📸 Demo

<a href="/course_images/ai110/AditAppDemo.png" target="_blank"><img src='/course_images/ai110/AditAppDemo.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

---

## ✨ Features

### 1. Priority-Based Greedy Scheduling
`Scheduler.generate_plan()` fits pending tasks into the owner's daily time budget using a greedy algorithm:
tasks are evaluated in priority order (high → medium → low) and added to the plan as long as they fit.
Tasks that would exceed the remaining budget are placed in a "skipped" list with a plain-English explanation
of exactly how many minutes over budget they would go.

### 2. Smart Sort — Timed Tasks First, Then Priority
`Scheduler._sort_tasks()` produces a two-group ordering before the greedy loop runs:
- **Group 1 — timed tasks** sorted chronologically by `scheduled_time` ("HH:MM").
  Zero-padded strings compare correctly as plain strings, so no numeric conversion is needed.
  Ties at the same minute break by priority (high first), then alphabetically for determinism.
- **Group 2 — untimed (floating) tasks** sorted by priority (high first), then alphabetically.

This ensures time-anchored care (morning meds, evening walk) is always respected before
flexible tasks are slotted in.

### 3. Chronological Sort
`Scheduler.sort_by_time(pairs)` sorts any list of `(Pet, Task)` pairs by `scheduled_time`
using a lambda key that places tasks without a time at the very end (`"99:99"` sentinel).
Used in the UI to display a pet's tasks in clock order.

### 4. Conflict Detection & Warnings
`Scheduler.detect_conflicts()` uses `itertools.combinations` to check every unique pair of
timed tasks for window overlap with the standard interval-intersection test
(`start_a < end_b and start_b < end_a`).
Each conflict record includes both task names, both start times, and the exact overlap in minutes.

`Scheduler.conflict_warnings()` wraps those records into human-readable strings.
The Streamlit UI surfaces these as `st.warning` cards — visible immediately on page load,
before the owner even clicks "Generate schedule" — so clashes are caught and fixed proactively.

### 5. Recurring Task Auto-Recurrence
`Task.next_occurrence(current_day)` creates a fresh pending copy of a completed task
and sets its `due_day` to prevent it from appearing too early:
- **Daily** tasks → `due_day = current_day + 1`
- **Weekly** tasks → `due_day = current_day + 7`
- **As-needed** tasks → returns `None` (no automatic recurrence)

`Scheduler.mark_task_complete()` calls this automatically and appends the new instance
to the pet's task list, so recurring care never needs to be re-entered manually.

### 6. Task Filtering
- `Scheduler.filter_by_pet(name)` — isolates all tasks for one pet (case-insensitive).
- `Scheduler.filter_by_status(completed)` — returns done or pending tasks across every pet at once.

Both return plain lists that compose freely with `sort_by_time`.
Used in the Section 3 task list to display each pet's tasks in priority order.

### 7. Multi-Pet Support
`Owner` holds a list of `Pet` objects; each `Pet` holds its own list of `Task` objects.
`Owner.get_all_tasks()` returns a flat list of `(Pet, Task)` tuples that the `Scheduler`
consumes without ever needing to know the internal structure of the pets list.
This design means adding a second or third pet requires zero changes to the scheduling logic.

### 8. Professional Streamlit UI
| Component | Usage |
|---|---|
| `st.success` | Confirmation when tasks/pets are added; scheduled task count |
| `st.warning` | Conflict details; skipped-task explanations |
| `st.error` | Conflict banner (shown on every page load, not just after Generate) |
| `st.table` | Clean tabular schedule with Pet / Task / Time / Duration / Priority / Frequency columns |
| `st.progress` + `st.metric` | Visual time-budget meter showing minutes used vs. available |
| Priority badges | 🔴 high · 🟡 medium · 🟢 low in the task list |

---

## 🏗 Architecture

```
Owner  ──owns──►  Pet  ──has──►  Task
                                  │
Scheduler ──reads──► Owner        │ next_occurrence()
     │                            ▼
     └──creates──► Schedule   (new Task)
```

| Class | Responsibility |
|---|---|
| `Task` | A single care activity — stores description, duration, priority, frequency, and clock time |
| `Pet` | The animal — owns a task list and exposes add/remove/query helpers |
| `Owner` | The human — tracks time budget and a list of pets |
| `Scheduler` | The brain — sorts, filters, detects conflicts, and generates the daily plan |
| `Schedule` | The output — holds scheduled items, skipped items, and the plain-English summary |

Full class diagram: [uml_final.png](uml_final.png) · source: [uml_final.mmd](uml_final.mmd)

---

## 🧪 Testing

```bash
python -m pytest
```

| Area | What is verified |
|---|---|
| **Task lifecycle** | `mark_complete()` flips `completed`; `add_task()` grows the pet's task list |
| **Sort — chronological** | `sort_by_time()` returns tasks earliest-first regardless of insertion order |
| **Sort — timed before untimed** | `_sort_tasks()` always places time-anchored tasks ahead of floating ones |
| **Sort — tie-breaking** | Same `scheduled_time` → high priority sorts before low |
| **Recurrence — daily** | Completing a daily task creates a next occurrence with `due_day = current_day + 1` |
| **Recurrence — weekly** | New occurrence is not due again until `current_day + 7` |
| **Recurrence — as-needed** | `next_occurrence()` returns `None`; no auto-enqueue |
| **Conflict — overlap** | Two overlapping tasks produce exactly one conflict with the correct `overlap_minutes` |
| **Conflict — no false positive** | Adjacent tasks (end == start) produce zero conflicts |
| **Conflict — untimed ignored** | Tasks without `scheduled_time` are never flagged |
| **Conflict warnings** | `conflict_warnings()` returns strings containing `"WARNING"` and both task names |

**Confidence: ★★★★☆ (4/5)** — All 12 tests pass. The Streamlit UI layer is verified manually.

---

## 🚀 Getting Started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the tests

```bash
python -m pytest
```

---

## 📁 Project Structure

```
pawpal_system.py   — all backend classes (Task, Pet, Owner, Scheduler, Schedule)
app.py             — Streamlit UI
tests/
  test_pawpal.py   — automated test suite (12 tests)
uml_final.mmd      — Mermaid source for the class diagram
uml_final.png      — rendered class diagram
reflection.md      — design decisions and tradeoffs
```
