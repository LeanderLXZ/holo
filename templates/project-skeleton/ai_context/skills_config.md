# Skills Config (project instance) <!-- holo:heading -->

<!-- holo:section start -->
Loaded on demand by skills, not at session start. Each `## …` header
is mandatory — a missing header fails loud (per-section exceptions
declare themselves in their body; see `## Timezone`). Body value
`(none)` = skill skips the related step; listed paths that don't
exist on disk fail loud.

Layout (Option A): descriptive prose + contract sentences live
INSIDE `<!-- holo:section start/end -->` (plugin canonical,
overwritten on `/holo:update`). Configurable bullets / field values
live OUTSIDE the sentinel (user-territory, preserved by smart-merge).
When porting to a new project, edit only the gap bullets.
<!-- holo:section end -->

## Background processes <!-- holo:heading -->

<!-- holo:section start -->
Used by skills to detect "is there an in-flight long-running job on this
branch / worktree?", so they don't disturb it.
<!-- holo:section end -->

- pgrep patterns:
  - `(none)`
- Process artifacts:
  - `(none)`
- Process logs:
  - `(none)`

## Protected branch prefixes <!-- holo:heading -->

<!-- holo:section start -->
Used by skills to identify branches that must not be auto-forwarded or
auto-merged.
<!-- holo:section end -->

- Prefixes:
  - `(none)`

## Main branch policy <!-- holo:heading -->

<!-- holo:section start -->
Drives main-branch-related skill decisions (worktree prompts in `/go`,
push defaults, etc.). Skills no longer auto-merge across branches —
cross-branch synchronisation is an explicit user action via `/forward`.
<!-- holo:section end -->

- Main branch: `main`
- Rule: _(none yet — delete this marker once content is added)_

## Do-not-commit paths <!-- holo:heading -->

<!-- holo:section start -->
Project-specific paths that must never be committed, on top of
`.gitignore` defaults.
<!-- holo:section end -->

- `(none)`

## Source directories <!-- holo:heading -->

<!-- holo:section start -->
Used by review skills to scope code-level scans.
<!-- holo:section end -->

- `(none)`

## Data contract directories <!-- holo:heading -->

<!-- holo:section start -->
Project-specific directories holding data-shape contracts —
JSON Schema, Protobuf, OpenAPI, Pydantic models, SQL DDL, Avro,
GraphQL schemas, etc. Many projects don't have a dedicated directory
(contracts inline in code) — leave as `(none)` and the related scans
degrade gracefully.
<!-- holo:section end -->

- `(none)`

## Example artifact directories <!-- holo:heading -->

<!-- holo:section start -->
Used by review skills to scope example-output / fixture-data scans.
<!-- holo:section end -->

- `(none)`

## Core component keywords <!-- holo:heading -->

<!-- holo:section start -->
Used by review skills to locate key architectural components for
alignment audits.
<!-- holo:section end -->

- `(none)`

## Sensitive content placeholder rules <!-- holo:heading -->

<!-- holo:section start -->
Real-world content that must NOT appear in docs / prompts / ai_context;
must be replaced by structural placeholders.
<!-- holo:section end -->

- `(none)`

## Timezone <!-- holo:heading -->

<!-- holo:section start -->
Drives timestamp generation (log filenames, report filenames,
per-cycle timestamps). Section missing or command template fails →
fallback to `date '+%Y-%m-%d_%H%M%S'` with system timezone (part of
the contract).
<!-- holo:section end -->

- Command template: `TZ='UTC' date '+%Y-%m-%d_%H%M%S'`

## Tmp directory <!-- holo:heading -->

<!-- holo:section start -->
Smart-merge transient working space used by the `## Reconcile core`
SOP (`commands/update.md`) for translation template trees and Agent 1
staging. Bullet value joins with `target_root` (repo root, **not**
skill CWD). Section absent or `(none)` → fallback to
`${TMPDIR:-/tmp}/holo-tmp-<YYYY-MM-DD>_<HHMMSS>/`. Distinct from
`## File snapshots` (persistent user-restorable backups). Full
design: `docs/architecture/smart-merge.md`.
<!-- holo:section end -->

- Smart-merge tmp root: `./tmp/holo/`

## File snapshots <!-- holo:heading -->

<!-- holo:section start -->
Persistent user-restorable backups taken by `take_snapshot()` (in
`scripts/holo_update_check.py`) **before any overwrite** —
sentinel-block content drift auto-fix (`/holo:update` Reconcile.Step 5a),
init-time CONFLICT overwrite path (`/holo:init` Reconcile.Step 3),
and `/compress-ai-context` Steps 4a / 7a plan-freeze snapshots all
write here. Layout: `<root>/<YYYY-MM-DD>_<HHMMSS>_<slug>/<original-path>`.
Bullet value joins with `target_root` (repo root, **not** skill CWD);
absolute paths are returned as-is, and relative paths are normalized
post-join (a `../` prefix can escape `target_root` if the user
intentionally configures one — out-of-repo locations are NOT covered
by the repo's `.gitignore`; use at your own risk). Section absent or
`(none)` → graceful fallback to `<target_root>/logs/file_snapshots/`.
Distinct from `## Tmp directory` (transient smart-merge staging,
OS-cleanup-safe). Full design:
`docs/architecture/drift-detection.md` §File snapshot path resolution.
<!-- holo:section end -->

- File snapshot root: `./logs/file_snapshots/`

## Language <!-- holo:heading -->

<!-- holo:section start -->
Two project-wide language axes consumed by every skill that writes
output or asks the user, plus the SessionStart banner.

- `content_language` governs every written artifact (`ai_context/` /
  `docs/` / `logs/` / commits / README / skill output / AI-written
  code comments). Code identifiers and field names stay English
  regardless.
- `conversation_language` governs AI ↔ user turns. `auto` = per-turn
  match the user's last message; an explicit value is a hard rule
  with a single-message escape hatch ("respond in `<other>`" affects
  only that turn).
- Use ISO 639-1 codes (`zh` not `cn`, `en` not `eng`); locale
  variants (`zh-CN`, `zh-TW`) reserved.
<!-- holo:section end -->

- `content_language: en`
- `conversation_language: auto`

## Activity sources <!-- holo:heading -->

<!-- holo:section start -->
Per-source ledger registry consumed by `/recent-activity`,
`/todo-add`, `/go`, `/post-check`, `/full-review`, `/check-review`,
`/fix`, `/run-prompt`. Lists path + filename pattern + per-entry
field names. Git commits are implicit and not listed here.
<!-- holo:section end -->

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
