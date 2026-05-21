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

# Read Scope <!-- holo:heading -->

<!-- holo:section start -->
Tells future AI sessions what to read first, what to skip by default,
and when to read deeper. Loaded into context at session start as part
of the `ai_context/` reading order.
<!-- holo:section end -->

## Default Priority <!-- holo:heading -->

<!-- holo:section start -->
Read first when starting a session:

- `ai_context/`
- <add project-specific small-but-high-signal directories here as they
  emerge — e.g. a `docs/architecture/` index, a top-level `README.md`>
<!-- holo:section end -->

## Do Not Read By Default <!-- holo:heading -->

<!-- holo:section start -->
Large or write-mostly directories — load only when the task explicitly
requires them:

- `logs/change_logs/` — full history
- `logs/review_reports/` — past audit snapshots
<!-- holo:section end -->

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
