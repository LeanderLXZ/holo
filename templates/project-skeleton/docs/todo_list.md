# TODO List

---

## Index (auto-generated; do not hand-edit)

> This section is a cache of the three sub-tables below, refreshed by
> whoever edits an entry's body **immediately after** any add / edit /
> segment-move / completion / abandonment in the body sections below.
> See `## File guide → Index maintenance` for refresh rules. The
> `/todo` skill (if used) does NOT parse the body — it reads only this
> Index, so this section MUST stay in sync with the body; drift here
> means `/todo` gives the wrong answer.

### 🟢 In Progress (0)

| ID | Title | Start time | Updated | Status |
|---|---|---|---|---|

### 🟡 Next (0)

| ID | Brief | Importance | Ready | Scope | Updated | Deps |
|---|---|---|---|---|---|---|

### ⚪ Discussing (0)

| ID | Brief | Open decisions | Updated | Blocked by |
|---|---|---|---|---|

**Total**: 0 — 🟢 In Progress 0 ｜ 🟡 Next 0 ｜ ⚪ Discussing 0

---

## File guide

### Purpose

Records **planned-but-unfinished** concrete engineering tasks.
Distinct from sibling files:

- `ai_context/next_steps.md` — architectural direction and high-level
  roadmap.
- `ai_context/current_status.md` — current project state snapshot.
- `logs/change_logs/` — history (timestamped, append-only).
- `docs/architecture/` — formal architecture documents.
- `docs/todo_list_archived.md` — slim archive of completed / abandoned
  tasks (full detail lives in git history + change logs).

This file is the **engineering-level** queue: file paths, line numbers,
change manifest, verification steps.

### Task flow

```
Discussing ──(decided)──▶ Next ──(start)──▶ In Progress ──(commit done)──▶ archived ## Completed
                                                                            ▲
any node ─────────────────(abandoned)──────────────────────────── archived ## Abandoned
```

Segment semantics:

- **In Progress** (single slot) — task that has been started but not
  yet committed. **Only one entry at a time** — so that if work is
  interrupted (ctrl-c / pause / session switch), the next AI session
  can see "what's currently in flight" without parsing git status or
  progress files.
- **Next** — tasks whose dependencies and design are ready; can be
  started any time. Ordered by user priority — the first entry is the
  next one to start.
- **Discussing** — tasks with open decisions / external dependencies /
  unsettled design. Don't start them; converge the decision first.

### What to record

✓ File / function-level concrete change tasks.
✓ Each entry MUST contain: **Context** (motivation + current state +
  trigger), **Change manifest** (file paths + line numbers; may be
  partial in `Discussing`), **Done criteria**, **Deps**.
✓ As appropriate: **Open decisions** (mandatory in `Discussing`),
  **Estimate**, **Why not landed yet**, **Out of scope**.
✓ **Requirements** (optional; positioned between **Context** and
  **Change manifest**): what the user wants done / what effect to
  achieve. Plain prose, no special format rules. Include when this
  session converged user-facing requirements worth preserving.
✓ **Solution details** (optional; positioned between **Requirements**
  and **Change manifest**): the final converged plan — what the
  solution is, what parts compose it. **Only the final converged
  version** — do NOT include rejected alternatives or debate
  history. Plain prose, no special format rules. Include when this
  session converged a concrete plan worth preserving.
✓ In `Discussing` entries, list the unresolved options and their
  trade-offs.

### What NOT to record

✗ Architectural direction / high-level roadmap → `ai_context/next_steps.md`.
✗ Completed / abandoned tasks → move to `docs/todo_list_archived.md` (slim).
✗ Temporary debug notes / mid-thought analysis → conversation or plan,
  not persistent.
✗ Live runtime status / progress → write to runtime progress artifacts
  (see `ai_context/skills_config.md` §Background processes).

### How to update entries

**Common to all segments**: every `### [T-XXX]` block MUST have an
**Updated** timestamp (`YYYY-MM-DD HH:MM` + timezone per
`ai_context/skills_config.md` §Timezone). Set on create; refresh
whenever any body field is changed or the entry moves between
segments. **Refreshing only the Index cache does NOT count** — that
field marks "when the body actually changed".

**Add a new task**: place it in the appropriate segment (Next or
Discussing). New entries must have the fields from "What to record"
plus `**Updated**`. **Do not add directly to "In Progress"** — that
segment is filled only when the task actually starts.

**Task starts (moves to In Progress)**:
1. Move the entire entry from "Next" to "In Progress".
2. Add `**Start time**` (same timestamp format) and **Current state**
   (in-progress / awaiting decision / paused).
3. Refresh `**Updated**` = start time.
4. **Single slot** — if "In Progress" is already occupied, finish or
   explicitly pause-back that task first.
5. Refresh the Index (see "Index maintenance").

**Task completes (committed + verified)**:
1. Move the entry to `docs/todo_list_archived.md` `## Completed`
   (slim entry: title + completion form + 1-line summary + log link);
   delete from this file.
2. If the task produced durable conclusions / new architecture
   decisions / reusable insight, write a
   `logs/change_logs/YYYY-MM-DD_HHMMSS_slug.md`.
3. If completion changes durable facts in `ai_context/` (current_status
   / decisions / next_steps), update those.
4. Refresh the Index.

**Task abandoned**: write a `logs/change_logs/` entry stating why, then
move the entry to `docs/todo_list_archived.md` `## Abandoned` (same
slim format). Refresh the Index.

**Discussion lands**: when a `Discussing` entry reaches a conclusion:
- **Full decision** — move the entry to `Next`, fill in the missing
  fields (Change manifest / Done criteria / Deps). Refresh Index.
- **Partial decision** — split the decided sub-task out as its own
  `Next` entry; the undecided remainder stays in `Discussing` with
  updated context. Refresh Index.
- **Conclusion invalidates an existing `Next` / `In Progress` task**
  — treat as "task abandoned".

### Index maintenance

The top-of-file `## Index (auto-generated; do not hand-edit)` section
caches the three sub-tables. **Refresh after any add / edit /
segment-move / completion / abandonment in the body.** The `/todo`
skill reads only this section.

**Triggers** for refresh — any of:

- Adding a new entry.
- Editing an existing entry's title, context summary, deps, open
  decisions, change-manifest file count, schema/architecture/multi-phase
  reach, or `**Updated**`.
- Segment move: Discussing → Next, Next → In Progress, In Progress →
  archived, any → archived (abandoned).
- "Current state" change inside an `In Progress` entry.

**Column definitions**:

**In Progress**

| Column | Source |
|---|---|
| ID | back-ticked T-XXX slug |
| Title | the human-readable phrase after the bracket |
| Start time | entry's `**Start time**` field, full timestamp |
| Updated | entry's `**Updated**` field, date only (no HH:MM); missing → `—` |
| Status | entry's `**Current state**` value |

**Next**

| Column | Source |
|---|---|
| ID | back-ticked T-XXX slug |
| Brief | first sentence of Context + 1–2 lines of key background. **Total length ≤ 150 chars.** Strip markdown link back-ticks so the table renders, but keep `[text](url)` form. |
| Importance | 🔴 High / 🟡 Medium / 🟢 Med-Low (rules below) |
| Ready | ✅ Ready / 💬 Discuss first / ⏸ Blocked (rules below) |
| Scope | 🟢 Small / 🟡 Medium / 🔴 Large·Arch / — (rules below) |
| Updated | entry's `**Updated**` field, date only |
| Deps | first sentence of the entry's `**Deps**` field |

**Discussing**

| Column | Source |
|---|---|
| ID | back-ticked T-XXX slug |
| Brief | same as Next, ≤ 150 chars |
| Open decisions | count of bullet items under `**Open decisions**`; missing section → 0 |
| Updated | entry's `**Updated**` field, date only |
| Blocked by | first sentence of `**Deps**` |

**Inference rules** (deterministic — don't improvise):

**Importance** (Next only)

| Level | Trigger |
|---|---|
| 🔴 High | User has flagged high priority OR blocks other tasks |
| 🟡 Medium | Default when not flagged High or Med-Low |
| 🟢 Med-Low | Deps blocked OR open decisions ≥ 2 OR user hasn't flagged priority |

**Ready**

| Tag | Trigger |
|---|---|
| ✅ Ready | Deps ready AND open decisions = 0 |
| 💬 Discuss first | Open decisions ≥ 1 |
| ⏸ Blocked | Deps contain a concrete blocker (external CLI, unimplemented module, pending event) |

Priority: ⏸ > 💬 > ✅.

**Scope**

| Size | Trigger |
|---|---|
| 🟢 Small | Change manifest ≤ 2 files AND no schema / interface change |
| 🟡 Medium | Change manifest 3–6 files OR multi-function intra-module refactor; no architecture-layer change |
| 🔴 Large·Arch | Change manifest ≥ 7 files OR touches: new phase / schema field / core interface / cross-module protocol / new dependency |
| — | Missing change manifest (common in undecomposed `Discussing` entries) |

**Brief writing rule**: write in plain language — what problem does
this solve, why is it worth doing. **Avoid code names / function names
/ schema paths / line numbers / decision numbers / jargon** unless
they ARE the problem. Total length ≤ 150 chars; if it overflows, cut
detail until "what + why" remains.

**Summary line**: after the three tables, print one line:
`Total: N — 🟢 In Progress a ｜ 🟡 Next b ｜ ⚪ Discussing c`.

### When to read

- User asks about pending work / what's next → `/todo` skill (reads
  only the Index).
- Before starting any change, **read once** to avoid duplicate
  planning.
- When discussing a topic that may already be tracked here.
- **Not loaded by default** — not part of the `ai_context/`
  session-start reading order.

---

## In Progress

<!-- Single-slot. Filled only when a task is actually started.
     Format: see "How to update entries → Task starts". -->

## Next

<!-- Ordered by user priority. First entry is the next to start.
     Format: see "What to record". -->

## Discussing (Undecided)

<!-- Tasks with open decisions / external deps / unsettled design.
     Don't start; converge the decision first.
     Format: see "What to record" + "Open decisions" section mandatory. -->
