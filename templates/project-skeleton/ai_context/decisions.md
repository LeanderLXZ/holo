<!--
MAINTENANCE — read before editing this file.
This file is an index for fast project follow-up, not a detailed manual.
1. Write "what / where to find"; link to authoritative sources (code paths, docs/*.md, schemas, logs).
2. Prefer deletion over addition; check if a new item merges into an existing one before adding.
3. Describe the current design only — no "legacy / deprecated / formerly / renamed from".
4. No real product / customer / private-content names — use structural placeholders.
Shorter is better than longer; push detail into the linked source rather than growing this file.
-->

# Key Decisions — Compressed ADRs

Compressed log of durable engineering decisions. One entry per
decision: one line of decision text + one line of rationale + a pointer
to the authoritative source (code path, doc section, log file).

Long discussion chains and the reasoning behind each decision live in
`logs/change_logs/` — this file is the index, not the discussion.

## Format

```
N. <one-line decision statement>.
   <one-line rationale>.
   → <pointer to authoritative source>
```

Entries are append-only and numbered in the order they landed.
**Do not renumber** — downstream references (in code comments, change
logs, other ai_context files) cite the number. When a later decision
supersedes an earlier one, add the new entry and add a one-line
"superseded by #N" note to the older entry; do not delete it.

## Sections (organize by theme)

Pick stable thematic headers as the decision log grows — e.g.
"Data Separation", "Runtime Loading", "Schema Bounds". Decisions
within a section stay numbered globally (across the whole file).

_(none yet — delete this marker once content is added)_
