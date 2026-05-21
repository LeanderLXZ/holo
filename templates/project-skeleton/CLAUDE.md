# <project-name> — Claude Entry Point <!-- holo:heading -->

<!-- holo:section start -->
This file is auto-loaded by Claude at session start. Keep it short —
detailed context lives in `ai_context/`, not here.

> **Plugin-managed sections (sentinel contract).** Headings carrying
> `<!-- holo:heading -->` and bodies wrapped in
> `<!-- holo:section start --> ... <!-- holo:section end -->` are
> plugin canonical content. On plugin upgrade (`/holo:update`), these
> regions are refilled from the new plugin template via extract-and-
> reformat smart-merge — user content (gaps between sentinels) is
> preserved; plugin canonical content (inside sentinels) follows the
> new template. **Escape hatch**: to take permanent ownership of a
> section, delete its `<!-- holo:heading -->` marker — the section
> becomes user-owned and the smart-merge will leave it alone. See
> `docs/architecture/section-version-sentinel.md` for the full design.
<!-- holo:section end -->

## Language <!-- holo:heading -->

<!-- holo:section start -->
- `content_language: en` — disk-bound output (docs / logs / commits /
  skill output / new code comments)
- `conversation_language: auto` — AI ↔ user turns

Applies to **every** turn, not just the first. Code identifiers and
field names stay English regardless.
<!-- holo:section end -->

## Session Start: Read ai_context/ Once <!-- holo:heading -->

<!-- holo:section start -->
At the beginning of **every new session**, read the entire `ai_context/`
folder in the order specified by `ai_context/instructions.md`:

1. `conventions.md`
2. `project_background.md`
3. `requirements.md`
4. `read_scope.md`
5. `current_status.md`
6. `architecture.md`
7. `decisions.md`
8. `next_steps.md`
9. `handoff.md`

After finishing, **stop and wait for the user's instruction.** Do not
start modifying code, schemas, or docs on your own initiative.
<!-- holo:section end -->

## What Not To Load By Default <!-- holo:heading -->

<!-- holo:section start -->
See `ai_context/read_scope.md` for the project-specific list.

General rule: avoid scanning large raw inputs, full conversation
histories, full log directories, generated artifacts, databases, vector
stores, and indexes unless the task explicitly requires them.
<!-- holo:section end -->

## Acting vs. Loading <!-- holo:heading -->

<!-- holo:section start -->
Reading `ai_context/` is context loading, not a task brief. Only act on
explicit user requests. If something looks off while reading, note it
and wait — do not fix proactively.
<!-- holo:section end -->

## Dilution Self-Check <!-- holo:heading -->

<!-- holo:section start -->
Long sessions cause silent forgetting. Before editing code, schema, or
docs — and after any task-type switch — pause and answer:

1. **Scope check**: Am I doing exactly what the user asked, or am I
   expanding into proactive refactor / "while I'm here" fixes? If
   expanding → stop and ask first.
2. **Right layer**: Does the file I'm about to edit sit in the right
   module / layer for this concern? If unsure → re-read
   `ai_context/architecture.md`.
3. **Alignment check**: Before closing a change set, consult the
   Cross-File Alignment table in `ai_context/conventions.md` — did I
   update every downstream file?

If any answer is "I don't remember" or "I'm guessing" → re-read the
relevant `ai_context/` file before proceeding.
<!-- holo:section end -->

## Sync with AGENTS.md <!-- holo:heading -->

<!-- holo:section start -->
This file and `AGENTS.md` are kept **identical** except for the title
line ("Claude Entry Point" vs. "Agent Entry Point"). Any change to one
MUST be mirrored to the other in the same commit.
<!-- holo:section end -->
