<!--
MAINTENANCE — read before editing this file.
This file is an index for fast project follow-up, not a detailed manual.
1. Write "what / where to find"; link to authoritative sources (code paths, docs/*.md, schemas, logs).
2. Prefer deletion over addition; check if a new item merges into an existing one before adding.
3. Describe the current design only — no "legacy / deprecated / formerly / renamed from".
4. No real product / customer / private-content names — use structural placeholders.
Shorter is better than longer; push detail into the linked source rather than growing this file.
-->

# Operational Conventions

Rules easy to forget during long sessions. Dilution self-check triggers
live in `CLAUDE.md` / `AGENTS.md`.

## Logging

`logs/change_logs/` uses a three-timepoint contract per change:
PRE / POST / REVIEW — one log file spans one full change lifecycle.

- Filename: `YYYY-MM-DD_HHMMSS_slug.md` (HHMMSS mandatory; use the
  timezone command in `skills_config.md` §Timezone).
- **PRE** — context / decision / planned action list / verification
  criteria, written before any file change.
- **POST** — landed changes / diff vs plan / verification results /
  DONE|BLOCKED, written before commit.
- **REVIEW** — review summary + REVIEWED-PASS|PARTIAL|FAIL, written
  after the post-merge review pass.

Rules:

- No PRE log → do not start modifying files.
- Pre-contract single-timepoint logs that pre-date this convention
  stay as-is; don't retroactively rewrite them.

When the project uses the bundled `/go` and `/post-check` skills, those
skills own the exact log format; read their definitions for the source
of truth.

## Cross-File Alignment

When a concept changes, update every file in its row. Start with an
empty table; add a row each time you discover a downstream file that
must move in lockstep with an upstream change.

| Changed | Also update |
|---------|-------------|
| <upstream artifact> | <list of downstream files> |

After any change, grep for the old phrasing to catch stale references.

## Single Source of Truth

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

## Identifier Renames

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

## Generic Placeholders

Canonical docs (this folder, `docs/`, schemas, prompts) stay
project-agnostic in tone:

- No real customer / product / private-content names.
- Examples use structural placeholders.
- No history narration ("legacy", "deprecated", "formerly",
  "renamed from") — describe the current design only.

Exempt (history is the point): `logs/change_logs/`,
`logs/review_reports/`, archived TODOs, this file's `decisions.md`
peer, git commit messages.

## Naming and Identifiers

<Project-specific. Document the ID schemes and language conventions
the project uses — e.g. ID prefix patterns, zero-pad widths, which
files stay in which language, JSON field language rules. Leave empty
until a convention is actually in force.>

## Data Separation

<Project-specific. Document hard schema gates and data boundaries that
must not be crossed — e.g. user-data vs canonical-data separation,
which fields are write-once vs evolving, which directories may not
flow data into which. Leave empty until a real boundary is set.>

## Git

<Project-specific. Document the branch model, push policy, and
do-not-commit rules. If the project uses a non-trivial multi-branch
flow, describe it here; otherwise leave a one-line "single-branch
`main`; commit small, push often." note.>

## Post-Change Checklist

1. All aligned files updated? (Cross-File Alignment table above)
2. PRE log written before the change; POST log written before commit?
3. `ai_context/` updated only if the change is durable?
4. Grepped for stale references to old names / paths / values?
   (For identifier renames, use the 4-form scan from §Identifier Renames.)
5. Smoke test or type check run, if code or schema changed?
