<!-- holo:section start -->
<!--
MAINTENANCE — read before editing this file.
This file is the INDEX of decisions, not the decisions themselves.
1. Each entry is 1–2 lines AND ≤ 200 characters total: decision one-liner + `→ docs/decisions.md #N`. The full entry (rationale / boundaries / pointers) lives in `docs/decisions.md` under the same number.
2. Entry criterion: record only decisions that were genuinely contested — a plausible alternative existed and might be re-proposed. Obvious or unforced choices get no entry.
3. Prefer supersede / prune over addition; check if a new item merges into an existing one before adding.
4. Describe the current design only — no "legacy / deprecated / formerly / renamed from".
5. No real product / customer / private-content names — use structural placeholders.
6. This file + `docs/decisions.md` are one lockstep pair — same numbering, same theme sections; change either and the other moves in the same pass (record the pair as a §Cross-File Alignment row if your project maintains rows there).
7. Sentinel discipline (see CLAUDE.md §Plugin-managed sections): content inside `<!-- holo:section start/end -->` is plugin-canonical and overwritten on `/holo:update`; project-specific additions go in the gap between sentinels.
-->
<!-- holo:section end -->

# Key Decisions — Index <!-- holo:heading -->

<!-- holo:section start -->
Index of durable engineering decisions: one 1–2-line entry per
decision — the decision statement itself plus a pointer to the full
entry in `docs/decisions.md` (same `#N`). This file is read at every
session start, so it stays lightweight by structure: statements live
here, rationale lives in `docs/decisions.md`, full deliberation lives
in `logs/change_logs/<slug>.md`. Never load `docs/decisions.md` at
session start — consult it on demand when the "why" of a specific
decision matters.
<!-- holo:section end -->

## Format <!-- holo:heading -->

<!-- holo:section start -->
Each entry is a numbered block of 1–2 lines, **≤ 200 characters in
total** (statement + pointer, whitespace included):

```
N. <decision statement, one line>.
   → docs/decisions.md #N
```

The decision statement alone must let a reader know what is settled;
the why lives in the archive entry. When one clause of rationale is
load-bearing (it changes what a reader would do), it may share the
first line — but boundaries, measurements, and history never do.

**The character ceiling is the operative bound**, not the line count:
a single arbitrarily long line satisfies "1–2 lines" while turning the
index back into the archive it exists to replace. Over 200 characters
means the surplus belongs in the `docs/decisions.md` entry — distil
here, move the detail there. `/holo:update`'s `decisions_fat_format`
check enforces the same number.

**Entry criterion:** record a decision only when a plausible
alternative existed and might be re-proposed by a future reader.
The test: without this entry, would an informed newcomer plausibly
do it differently? No → no entry.

**Numbering — global append-only, shared with `docs/decisions.md`:**

- Numbers are global, not per-section, and identical across the pair:
  index `#N` ⇔ archive `#N`, always both or neither.
- Before appending, scan this file for `max(N)`; new entry = `max + 1`.
  Append the index line here AND the full entry to `docs/decisions.md`
  in the same pass.
- Never renumber existing entries — downstream code / docs / logs cite `#N`.
- Never fill gaps; they are normal under append-only.
- Within-section visual order is NOT numerical (sections cluster by theme).

**Citation semantics:** `decisions.md #N` cites the index (this file) —
the stable public reference. `docs/decisions.md #N` cites the archive
entry — use it when pointing at rationale or boundaries specifically.

**Supersede in place** (decision changed, topic still relevant): replace
the entry's content — in BOTH files — with the new decision. Number
stays. Preconditions: (a) old info confirmed invalid; (b) downstream
files referencing the old decision have been updated. When the
superseded approach was actually tried and reverted, keep a half-line
trace in the archive entry — `(tried X, reverted, see log)` — so the
failed path is not re-proposed; the index line describes only the
current decision.

**Prune entry** (topic no longer relevant): delete the entry from BOTH
files; the gap stays (never renumber to fill). Preconditions: (a) info
confirmed invalid; (b) `grep -rn "decisions.md #<N>" . --exclude-dir=logs`
returns 0 live references. If invalid but live references exist outside
`logs/`, ask the user to decide.
<!-- holo:section end -->

## Sections (organize by theme) <!-- holo:heading -->

<!-- holo:section start -->
Pick stable thematic headers as the decision log grows — e.g.
"Data Separation", "Runtime Loading", "Schema Bounds". Use the SAME
section headers in `docs/decisions.md`; a decision's index line and
archive entry sit under matching sections. Decisions within a section
stay numbered globally (across the whole file).
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_
