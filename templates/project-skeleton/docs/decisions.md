# Decisions — Full Entries <!-- holo:heading -->

<!-- holo:section start -->
Long-form, authoritative decision log. This is the source of truth for
each decision's rationale; `ai_context/decisions.md` is its 1–2-line
index.

Two-layer separation:

- **This file** (`docs/decisions.md`) — full entries: decision
  statement, rationale, scope boundaries, and pointers to authoritative
  sources (code paths, doc sections, change logs). Read on demand only —
  never part of the session-start read list.
- **`ai_context/decisions.md`** — 1–2-line index per decision, points
  back here with `→ docs/decisions.md #N`.

The pair moves in lockstep — same global numbering, same theme
sections; change either one and the other must move in the same pass
(append / supersede / prune always hit both files). Record the pair
as an `ai_context/conventions.md` §Cross-File Alignment row if your
project maintains rows there.

Entry format — numbered block, typically ≤ 5 lines (never sacrifice
accuracy for length; push raw deliberation to `logs/change_logs/`):

```
N. <decision statement>.
   <rationale — why this over the alternatives>.
   <scope boundary / measured facts, when load-bearing>.
   → <pointer to authoritative source>
```

Supersede in place / prune per `ai_context/decisions.md` §Format —
numbers never move; a superseded-after-trial entry keeps a half-line
`(tried X, reverted, see log)` trace.
<!-- holo:section end -->

## Sections (organize by theme) <!-- holo:heading -->

<!-- holo:section start -->
Mirror the section headers of `ai_context/decisions.md` exactly; a
decision's archive entry sits under the same section as its index line.
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_
