# Skills Config (project instance)

Loaded on demand by skills that need project-specific anchors. **Not**
loaded by default at session start — only the specific skill that needs
it reads it.

Each section below has a fixed header. **Section headers (the `## …`
lines) MUST exist by default** — a missing header means the config is
structurally incomplete; skills will fail loudly and stop. Exceptions
are documented in the section body itself (currently only `## Timezone`
declares a system-timezone `date` fallback; see that section). If this
project has no value for a section, write `(none)` in the body and
skills will skip the related step. If a section lists concrete paths
but those paths don't exist on disk, skills will fail loudly and
report the drift.

When porting to another project, edit only this file — skill bodies
stay untouched.

## Background processes

Used by skills to detect "is there an in-flight long-running job on this
branch / worktree?", so they don't disturb it.

- pgrep patterns:
  - `(none)`
- Process artifacts:
  - `(none)`
- Process logs:
  - `(none)`

## Protected branch prefixes

Used by skills to identify branches that must not be auto-forwarded or
auto-merged.

- Prefixes:
  - `(none)`

## Main branch policy

Drives main-branch-related skill decisions (worktree prompts in `/go`,
push defaults, etc.). Skills no longer auto-merge across branches —
cross-branch synchronisation is an explicit user action via `/forward`.

- Main branch: `main`
- Rule: _(none yet — delete this marker once content is added)_

## Do-not-commit paths

Project-specific paths that must never be committed, on top of
`.gitignore` defaults.

- `(none)`

## Source directories

Used by review skills to scope code-level scans.

- `(none)`

## Data contract directories

Project-specific directories holding data-shape contracts —
JSON Schema, Protobuf, OpenAPI, Pydantic models, SQL DDL, Avro,
GraphQL schemas, etc. Many projects don't have a dedicated directory
(contracts inline in code) — leave as `(none)` and the related scans
degrade gracefully.

- `(none)`

## Example artifact directories

Used by review skills to scope example-output / fixture-data scans.

- `(none)`

## Core component keywords

Used by review skills to locate key architectural components for
alignment audits.

- `(none)`

## Sensitive content placeholder rules

Real-world content that must NOT appear in docs / prompts / ai_context;
must be replaced by structural placeholders.

- `(none)`

## Timezone

Drives timestamp generation across skills (log filenames, report
filenames, per-cycle timestamps).

- Command template: `TZ='UTC' date '+%Y-%m-%d_%H%M%S'`
- Fallback: If this section is missing or the command template fails,
  skills fall back to `date '+%Y-%m-%d_%H%M%S'` using the system
  timezone. This fallback is part of the contract (see top-of-file
  rule) — skills do not need to encode bespoke `try / except` per
  caller.

## Language

Two project-wide language axes consumed by every skill that writes
output or asks the user a question, plus the SessionStart hook
banner.

- `content_language: en`
- `conversation_language: auto`

Notes:

- `content_language` governs every written artifact the AI produces
  or maintains in this project: `ai_context/` / `docs/` / `logs/` /
  commit messages / README / skill console output / error messages /
  code comments the AI writes. Code identifiers and field names
  stay English regardless. Accepts any ISO 639-1 code.
- `conversation_language` governs AI ↔ user turns (`AskUserQuestion`
  prompts, free-form replies, confirmations). Accepts
  `auto | <ISO 639-1>`. `auto` = per-turn match the user's most
  recent message language. Any explicit value is a hard rule with a
  single-message escape hatch (user says "respond in `<other>`" →
  that turn replies in `<other>`, next turn returns to config).
- Language codes follow ISO 639-1 (`zh`, not the country code `cn`;
  `en`, not `eng`). Locale variants (`zh-CN`, `zh-TW`) are reserved
  for future regional splits.
- Defaults above (`en` / `auto`) are the template's starting point;
  edit to your project's preferred values, or let `/holo:init` set
  them interactively when the project is initialised.

## Activity sources

Per-source registry consumed by `/recent-activity`, `/todo-add`, `/go`,
`/post-check`, `/full-review`, `/check-review`, and `/run-prompt`.
Lists path + filename pattern + per-entry field names for each ledger
the workflow skills touch. Git commits are implicit (always available
from the current repo); the entries below are listed so non-default
project layouts can override them. Sections whose body is `(none)` are
treated as "not configured" — the consuming skill skips the related
scan (graceful skip per top-of-file rule).

- Change logs:
  - Path: `logs/change_logs/`
  - Filename time pattern: `{YYYY-MM-DD}_{HHMMSS}_{slug}.md`
- TODO list:
  - Path: `docs/todo_list.md`
  - Per-entry updated-time field: `**Updated**` (or project-chosen
    label; pick one and stay consistent)
- Archived TODO list:
  - Path: `docs/todo_list_archived.md`
- Review reports:
  - Path: `logs/review_reports/`
  - Filename pattern: `{YYYY-MM-DD_HHMMSS}_{model}_{slug}.md`
- Prompt sources:
  - Path: `(none)`
