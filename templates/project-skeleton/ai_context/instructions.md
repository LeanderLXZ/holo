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

# Instructions For Future AI Agents <!-- holo:heading -->

## Entry Point <!-- holo:heading -->

<!-- holo:section start -->
`ai_context/` is the handoff entry. Don't re-read full chat history or
large artifact directories by default. Only load the heavier layers
(logs, raw inputs, generated artifacts) when the user's task explicitly
requires them.

After finishing `ai_context/`, **stop and wait** for the next
instruction. Reading `ai_context/` is context loading, not a task brief.
Only act on explicit user requests.
<!-- holo:section end -->

## Reading Order <!-- holo:heading -->

<!-- holo:section start -->
1. `conventions.md`
2. `project_background.md`
3. `requirements.md`
4. `read_scope.md`
5. `current_status.md`
6. `architecture.md`
7. `decisions.md`
8. `next_steps.md`
9. `handoff.md`

Dilution self-check (when to re-read which file) lives in `CLAUDE.md` /
`AGENTS.md`.
<!-- holo:section end -->

## Update Expectations <!-- holo:heading -->

<!-- holo:section start -->
Update `ai_context/` only for **durable repository truth** (long-lived
conventions, architecture, schemas, decisions). Short-lived runtime
state / per-task progress belongs in work-local progress files or the
TODO list, not here.
<!-- holo:section end -->

## Logging <!-- holo:heading -->

<!-- holo:section start -->
Every change outside `ai_context/` → one log entry under
`logs/change_logs/` per the contract in `conventions.md` §Logging.
The skills that own logging format (`/go` / `/do` / `/post-check`,
when this project uses them) write the file directly — do not
duplicate the format here.
<!-- holo:section end -->

## TODO List <!-- holo:heading -->

<!-- holo:section start -->
`docs/todo_list.md` — working queue of planned-but-unfinished tasks.
Read on demand, **not** part of the session-start reading order. Usage
rules live inside the file's own `## File guide` section.
<!-- holo:section end -->

## Project Focus <!-- holo:heading -->

_(none yet — delete this marker once content is added)_
