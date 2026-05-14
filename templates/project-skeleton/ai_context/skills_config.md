# Skills Config (project instance)

Loaded on demand by skills that need project-specific anchors. **Not**
loaded by default at session start — only the specific skill that needs
it reads it.

Each section below has a fixed header. **Section headers (the `## …`
lines) MUST exist** — a missing header means the config is structurally
incomplete; skills will fail loudly and stop. If this project has no
value for a section, write `(none)` in the body and skills will skip
the related step. If a section lists concrete paths but those paths
don't exist on disk, skills will fail loudly and report the drift.

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

Drives main-branch-related skill decisions (worktree locking, branch
sync direction, etc.).

- Main branch: `main`
- Rule: <one sentence — e.g. "changes to code / docs / config land on
  `main` first; other branches sync forward via `git merge main`.">

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

## Activity sources

Used by activity-summary skills to assemble a unified
reverse-chronological timeline of project actions. Git commits are
implicit (always available from the current repo); the entries below
are listed so non-default project layouts can override them.

- Change logs:
  - Path: `logs/change_logs/`
  - Filename time pattern: `{YYYY-MM-DD}_{HHMMSS}_{slug}.md`
- TODO list:
  - Path: `docs/todo_list.md`
  - Per-entry updated-time field: `**Updated**` (or project-chosen
    label; pick one and stay consistent)
