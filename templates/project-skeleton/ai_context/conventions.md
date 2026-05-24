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
   - Aim for ≤ 5 lines per entry, and push longer detail to the linked source (docs/<topic>.md).
   - Do not compress or touch content unrelated to the current edit.
6. Sentinel discipline (see CLAUDE.md §Plugin-managed sections): content inside `<!-- holo:section start/end -->` is plugin-canonical and overwritten on `/holo:update`; project-specific additions go in the gap between sentinels.
-->
<!-- holo:section end -->

# Operational Conventions <!-- holo:heading -->

<!-- holo:section start -->
Rules easy to forget during long sessions. Dilution self-check triggers
live in `CLAUDE.md` / `AGENTS.md`.
<!-- holo:section end -->

## Logging <!-- holo:heading -->

<!-- holo:section start -->
`logs/change_logs/` carries per-change activity logs. Two log shapes
coexist, distinguished by the `Type` field in the file header:

- **`Type: GO`** — owned by `/go`; three-timepoint contract per change
  (PRE / POST / REVIEW), one log file spans one full change
  lifecycle.
- **`Type: DO`** — owned by `/do`; single-segment log for quick edits
  with no PRE phase, written after the modification, no REVIEW.

Shared:

- Filename: `YYYY-MM-DD_HHMMSS_slug.md` (HHMMSS mandatory; use the
  timezone command in `skills_config.md` §Timezone).
- Header carries `Type` + `Status` fields (see the owner skill for
  the exact token set).

`Type: GO` rules:

- **PRE** — context / decision / planned action list / verification
  criteria, written before any file change.
- **POST** — landed changes / diff vs plan / verification results /
  DONE|BLOCKED, written before commit.
- **REVIEW** — review summary + REVIEWED-PASS|PARTIAL|FAIL, written
  after the post-merge review pass.
- No PRE log → do not start modifying files.

`Type: DO` rules:

- Single segment written after the modification, before optional
  commit. Subsections: `## Motivation` / `## Change list` /
  `## Verification summary` / `## Execution deviations`.
- No PRE required (this is the explicit exception to the "no PRE →
  no modification" rule above); discipline shifts to the user
  briefing the edit set verbally before invoking `/do`.
- `/do` is not allowed to mid-flight escalate to `/go`; if the change
  surface widens past `/do`'s scope (≥ 3 files / cross-file alignment
  needed), exit and re-enter via `/go`.

Pre-contract logs (single-timepoint, predating this convention) stay
as-is; do not retroactively rewrite or backfill the `Type` field.

When the project uses the bundled `/go` / `/do` / `/post-check`
skills, those skills own the exact log format; read their definitions
for the source of truth.
<!-- holo:section end -->

## Cross-File Alignment <!-- holo:heading -->

<!-- holo:section start -->
When a concept changes, update every file in its row. Start with an
empty table; add a row each time you discover a downstream file that
must move in lockstep with an upstream change. Table cells list lockstep
files only — a comma-separated file list (with anchors when useful), not
an inline how-to; implementation detail belongs in the target file's
own maintenance comments.

Table shape (header only — fill rows in the gap below):

| Changed | Also update |
|---------|-------------|

After any change, grep for the old phrasing to catch stale references.
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_

## Single Source of Truth <!-- holo:heading -->

<!-- holo:section start -->
When the same value (a numeric bound, a path prefix, an enum, a regex
pattern) appears in multiple places, write it in **one canonical
location** and have every other place reference or derive from it.
Common canonical locations by project type:

- **Schemas** (`*.schema.json`, Pydantic, Protobuf, SQL DDL) for
  data-shape bounds: `maxLength`, `maxItems`, `required`, enum values.
- **Config files** (TOML / YAML / `.env`) for runtime constants.
- **Code constants** for shared behavior thresholds.

Anti-pattern: hardcoded "150–200 chars" prose in a prompt template AND
`maxLength: 200` in a schema. The two will silently drift — someone
edits one, forgets the other, and the inconsistency surfaces months
later as a confusing bug.

When the duplication can't be eliminated mechanically (e.g. a prose
example in a doc), record the linkage as a row in §Cross-File
Alignment so the mirror update becomes a checklist item, not memory.
<!-- holo:section end -->

## Identifier Renames <!-- holo:heading -->

<!-- holo:section start -->
When renaming an identifier across a repo, a single literal grep is
**not enough** — identifiers leak into multiple syntactic forms.
Before declaring "no residue", run all four scans:

1. **Literal name** — the old name in every casing the project uses
   (`old_name`, `OldName`, `OLD_NAME`).
2. **Pattern-embedded references** — regex strings, schema `pattern`
   fields, glob patterns, route paths, or any string that hardcodes
   the old name or its prefix. Zero-padded numeric IDs often hide in
   regex like `"^\\d{4}$"`.
3. **Format-string templates** — `f"...{var:fmt}..."` (Python),
   template literals (JS), `printf` / `format!` (Rust). Grep with a
   **generic** regex that catches any variable name binding (e.g.
   `\{[a-z_]+:04d\}` for zero-padded ints) — never the specific
   variable name. Sibling code using a different variable name will
   silently slip through otherwise.
4. **Prose / example mentions** — docs, READMEs, ai_context entries,
   commit-message examples that reference the old name in running text.

Exclude history-frozen directories from the scan: `logs/change_logs/`,
`logs/review_reports/`, archived todos, git history itself.

Codify the four scans into the PRE log's verification criteria section
when planning a rename, so the post-change review can verify each
independently.
<!-- holo:section end -->

## Generic Placeholders <!-- holo:heading -->

<!-- holo:section start -->
Canonical docs (this folder, `docs/`, schemas, prompts) stay
project-agnostic in tone:

- No real customer / product / private-content names.
- Examples use structural placeholders.
- No history narration ("legacy", "deprecated", "formerly",
  "renamed from") — describe the current design only.

Exempt (history is the point): `logs/change_logs/`,
`logs/review_reports/`, archived TODOs, this file's `decisions.md`
peer, git commit messages.
<!-- holo:section end -->

## Naming and Identifiers <!-- holo:heading -->

_(none yet — delete this marker once content is added)_

## Data Separation <!-- holo:heading -->

_(none yet — delete this marker once content is added)_

## Git <!-- holo:heading -->

_(none yet — delete this marker once content is added)_

## Post-Change Checklist <!-- holo:heading -->

<!-- holo:section start -->
1. All aligned files updated? (Cross-File Alignment table above)
2. PRE log written before the change; POST log written before commit?
3. `ai_context/` updated only if the change is durable?
4. Grepped for stale references to old names / paths / values?
   (For identifier renames, use the 4-form scan from §Identifier Renames.)
5. Smoke test or type check run, if code or schema changed?
<!-- holo:section end -->
