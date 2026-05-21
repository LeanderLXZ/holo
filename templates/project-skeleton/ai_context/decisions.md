<!-- holo:section start -->
<!--
MAINTENANCE — read before editing this file.
This file is an index for fast project follow-up, not a detailed manual.
1. Write "what / where to find"; link to authoritative sources (code paths, docs/*.md, schemas, logs).
2. Prefer deletion over addition; check if a new item merges into an existing one before adding.
3. Describe the current design only — no "legacy / deprecated / formerly / renamed from".
4. No real product / customer / private-content names — use structural placeholders.
5. Compactness Requirements:
   - Shorter is better than longer. Each entry is a summary, not a detail dump.
   - Compactness must not sacrifice accuracy or completeness — never drop important information just to fit the length target.
   - Aim for ≤ 5 lines and push longer detail to the linked source (docs/<topic>.md).
   - Do not compress or touch content unrelated to the current edit.
-->
<!-- holo:section end -->

# Key Decisions — Compressed ADRs <!-- holo:heading -->

<!-- holo:section start -->
Compressed log of durable engineering decisions. One entry per
decision: one line of decision text + one line of rationale + a pointer
to the authoritative source (code path, doc section, log file). The
entry records what was decided and why-in-one-sentence; the full
deliberation lives in `logs/change_logs/<slug>.md`, not here. This file
is the index, not the discussion.
<!-- holo:section end -->

## Format <!-- holo:heading -->

<!-- holo:section start -->
Each entry is a numbered block, overall ≤ 5 lines, typically:

```
N. <decision summary>.
   <rationale>.
   → <pointer to authoritative source>
```

Compactness must not sacrifice accuracy or completeness — never drop
important information just to fit the 5-line target.

**Numbering — global append-only across the whole file:**

- Numbers are global, not per-section.
- Before appending, scan the whole file for `max(N)`; new entry = `max + 1`.
- Never renumber existing entries — downstream code / docs / logs cite `#N`.
- Never fill gaps; they are normal under append-only.
- Within-section visual order is NOT numerical (sections cluster by theme).

**Worked example.** File currently ends with `18. Section version sentinel ...`.
To add a new decision: `grep -E '^[0-9]+\. ' decisions.md`, take `max(N) = 18`,
write `19. <decision>...` at the tail of its target theme section — even if
that section's last visible number was `#15`, not `#18`.

**Supersede in place** (decision changed, topic still relevant): replace the
existing entry's content with the new decision. Number stays. Preconditions:
(a) old info confirmed invalid; (b) downstream files referencing the old
decision have been updated to reflect the new one.

**Prune entry** (topic no longer relevant): delete the entry; the gap stays
(never renumber to fill). Preconditions: (a) info confirmed invalid;
(b) `grep -rn "decisions.md #<N>" . --exclude-dir=logs` returns 0 live
references. If invalid but live references exist outside `logs/`, ask the
user to decide.
<!-- holo:section end -->

## Sections (organize by theme) <!-- holo:heading -->

<!-- holo:section start -->
Pick stable thematic headers as the decision log grows — e.g.
"Data Separation", "Runtime Loading", "Schema Bounds". Decisions
within a section stay numbered globally (across the whole file).
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_
