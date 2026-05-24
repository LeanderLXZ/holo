<!-- holo:section start -->
<!--
MAINTENANCE — read before editing this file.
Stable project meta-rules. Keep short; update only when the rule itself changes.
Sentinel discipline (see CLAUDE.md §Plugin-managed sections): content inside `<!-- holo:section start/end -->` is plugin-canonical and overwritten on `/holo:update`; project-specific additions go in the gap between sentinels.
-->
<!-- holo:section end -->

# Read Scope <!-- holo:heading -->

<!-- holo:section start -->
Tells future AI sessions what to read first, what to skip by default,
and when to read deeper. Loaded into context at session start as part
of the `ai_context/` reading order.
<!-- holo:section end -->

## Default Priority <!-- holo:heading -->

<!-- holo:section start -->
Read first when starting a session. `ai_context/` is always read first
regardless. Add project-specific small-but-high-signal directories
below as they emerge — e.g. a top-level `README.md`.
<!-- holo:section end -->

- _(none yet — delete this marker once content is added)_

## Do Not Read By Default <!-- holo:heading -->

<!-- holo:section start -->
Large or write-mostly directories — load only when the task explicitly
requires them:

- `logs/change_logs/` — full history
- `logs/review_reports/` — past audit snapshots
- `logs/file_snapshots/` — smart-merge backup archive
<!-- holo:section end -->

- _(none yet — delete this marker once content is added)_

## When To Read Deeper <!-- holo:heading -->

<!-- holo:section start -->
- User explicitly asks
- Task depends on specific evidence from a heavier source
- Compressed context in `ai_context/` is insufficient for the question
  at hand
- A conflict needs provenance verification
<!-- holo:section end -->

## Practical Rule <!-- holo:heading -->

<!-- holo:section start -->
Prefer targeted reads: specific files, minimal excerpts, summaries
first. Avoid scanning whole large directories, loading all session
history, reading all logs, or bulk-pasting source content into answers.
<!-- holo:section end -->
