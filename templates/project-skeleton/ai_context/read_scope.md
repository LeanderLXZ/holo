<!--
MAINTENANCE — read before editing this file.
This file is an index for fast project follow-up, not a detailed manual.
1. Write "what / where to find"; link to authoritative sources (code paths, docs/*.md, schemas, logs).
2. Prefer deletion over addition; check if a new item merges into an existing one before adding.
3. Describe the current design only — no "legacy / deprecated / formerly / renamed from".
4. No real product / customer / private-content names — use structural placeholders.
Shorter is better than longer; push detail into the linked source rather than growing this file.
-->

# Read Scope

Tells future AI sessions what to read first, what to skip by default,
and when to read deeper. Loaded into context at session start as part
of the `ai_context/` reading order.

## Default Priority

Read first when starting a session:

- `ai_context/`
- <add project-specific small-but-high-signal directories here as they
  emerge — e.g. a `docs/architecture/` index, a top-level `README.md`>

## Do Not Read By Default

Large or write-mostly directories — load only when the task explicitly
requires them:

- `logs/change_logs/` — full history
- `logs/review_reports/` — past audit snapshots
- <add project-specific large directories here as they emerge —
  e.g. raw inputs, generated artifacts, databases, vector stores,
  full conversation histories>

## When To Read Deeper

- User explicitly asks
- Task depends on specific evidence from a heavier source
- Compressed context in `ai_context/` is insufficient for the question
  at hand
- A conflict needs provenance verification

## Practical Rule

Prefer targeted reads: specific files, minimal excerpts, summaries
first. Avoid scanning whole large directories, loading all session
history, reading all logs, or bulk-pasting source content into answers.
