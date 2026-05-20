---
description: Project sync check after plugin upgrade — compare the current project against the installed plugin (`.agents/skills/` mirror, template new files / section headers, `CLAUDE.md` / `AGENTS.md` headers) and find structural drift introduced by the plugin upgrade. **All detection logic lives in the single script `${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py`**; the skill body does not re-implement rules. ≥ 1 drift → single aggregated question asking Auto-fix all / Skip all; 0 drift passes silently. CLAUDE/AGENTS findings are always display-only, never auto-merged. No arguments; whether the current directory is empty or already initialized, both are handled. Does not touch user-filled content, does not git add, does not commit. Triggers: /holo:update / plugin upgraded / sync holo update / check whether holo is up to date.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (regenerated `.agents/skills/` mirror files, `_(TODO — added by /holo:update)_` markers appended to `skills_config.md`, any in-place file edits) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / drift-category report / final summary / `Auto-fix all` / `Skip all` confirmations) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, JSON keys returned by `holo_update_check.py` (`missing_section`, `lang_mirror_drift`, `agents_sync.stale`, `legacy_skip_marker`, etc.), and structural prefixes (`Step N:`, `DRIFT:`, `OK:`) stay English regardless.

# /holo:update — project sync check after plugin upgrade

Compare plugin-linked artifacts in the current project (`.agents/skills/` mirror, `templates/project-skeleton/` files + section headers, `CLAUDE.md` / `AGENTS.md` headers) against the currently installed plugin (`${CLAUDE_PLUGIN_ROOT}`), surface drift where "the plugin upgraded but the project did not follow," and apply batch fixes after a single aggregated question.

**Detection rules single source of truth = `${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py`**. The skill body **does not re-implement detection logic**; to adjust rules, edit the script and sync this file + `commands/init.md` Step 3.2 per `ai_context/conventions.md` §Cross-File Alignment. Background in `ai_context/decisions.md` §Skill Implementation #5.

No arguments. **Only touches structural drift introduced by the plugin upgrade**; **does not touch user-filled content**. CLAUDE/AGENTS findings are always display-only, never auto-merged.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`.

The flow below is split into `## Step 0:` ~ `## Step 4:`.

**Before entering Step 0**: call **<progress tool>** to pre-register Step 0 ~ Step 4 (`status` all `pending`). **Do not proceed without calling <progress tool>**.

On entering each step: flip the current step to `in_progress` and mark the previous one `completed`.

**<progress tool> resolution**: Claude → `TodoWrite`; Codex → `update_plan`; other runtimes → maintain a markdown checkbox list in the response text.

**<ask tool> resolution**: Claude → `AskUserQuestion`; other runtimes → enumerate questions + options in the response text and let the user answer them in one pass.

## Step 0: Load skills config

`Read` `ai_context/skills_config.md`.

- File missing / any section header missing → fail loudly: print the missing items + prompt to complete per plugin template, stop
- Section content `(none)` or empty → skip the related steps for that section (treat as N/A in this project)
- Section lists concrete paths but the path does not exist → fail loudly: report the section drifting to a nonexistent path, stop and wait for the user to fix

Subsequent steps referencing "skills_config.md `## XX`" use this config. This command uses:
`## Language` (Step 2 reads the consumer's `content_language` for active project-skeleton baseline selection — the script `holo_update_check.py` does this internally; this Step 0 load is the skill-body anchor confirming the §Language section exists before the script runs).

## Step 1: Pre-check

**1.1 Plugin info**

- Resolve `${CLAUDE_PLUGIN_ROOT}` (if unset, the script derives it from its own path; fail loudly and stop on failure)
- Read `name` + `version` from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`, print `Checking project against <name> v<version>...`

**1.2 Whether the project has been initialized by /holo:init**

Initialization detected if any of the following exist:

- `CLAUDE.md` at top level
- `AGENTS.md` at top level
- `ai_context/` directory

None present → print `Project has not been initialized — run /holo:init first` and exit (no error, normal return).

**1.3 Working tree status**

- `test -d .git && git status --short`; dirty → print warning but do not stop (`/holo:update` does not commit, consistent with `/holo:init`)

## Step 2: Run the detection script

> **Language**: user-facing — render the drift-detection report listing the categories of findings (`missing_section`, `lang_mirror_drift`, `agents_sync.stale`, `missing_l1_directive`, `l1_directive_drift`, `template_new_files`, etc.) in `conversation_language` per `ai_context/skills_config.md §Language`. JSON category keys / file paths stay verbatim; only descriptive prose translates.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py" --json
```

The script outputs a JSON structure (**interface contract**; the skill body parses by these key names; changes go through conventions.md §Cross-File Alignment):

```json
{
  "plugin_root": "...", "target_root": "...",
  "consumer_content_lang": "en|zh|<ISO 639-1>",
  "agents_sync": {
    "skipped": false,
    "stale":   [{"name": "...", "source_path": "...", "source_type": "command|skill", "target_path": "..."}],
    "missing": [/* same as stale */],
    "orphan":  [{"name": "...", "target_path": "..."}]
  },
  "missing_template": [{"rel": "...", "source_path": "...", "target_path": "..."}],
  "missing_section":  [{"rel": "...", "header": "## ...", "source_path": "..."}],
  "missing_field":    [{"rel": "ai_context/skills_config.md",
                        "section": "## ...", "key": "...",
                        "form": "backticked|plain",
                        "source_path": "..."}],
  "gitignore_missing_lines": [{"rel": ".gitignore", "pattern": "...",
                              "source_path": "...", "target_path": "..."}],
  "claude_agents": {
    "present": true,
    "first_line_placeholder": false,
    "unexpected_diffs": [{"line": N, "CLAUDE": "...", "AGENTS": "..."}],
    "unexpected_diffs_truncated": 0
  },
  "missing_l1_directive": [{"rel": "commands/<name>.md|skills/<name>/SKILL.md", "reason": "..."}],
  "l1_directive_drift":   [{"rel": "commands/<name>.md|skills/<name>/SKILL.md", "missing_substrings": ["..."]}],
  "lang_mirror_drift":    [{"variant": "project-skeleton.<lang>", "rel": "...", "kind": "MISSING|ORPHAN"}],
  "legacy_skip_marker":   [{"rel": "ai_context/<...>.md", "line": N, "snippet": "..."}]
}
```

**`consumer_content_lang`** = the 2-letter ISO 639-1 value read from the consumer project's `ai_context/skills_config.md §Language`'s `content_language` field; defaults to `"en"` when the file / section / field is absent. Drives the active project-skeleton baseline (canonical `templates/project-skeleton/` when `en`; pre-generated variant `templates/project-skeleton.<lang>/` when non-en and a variant ships in the plugin; canonical fallback when no variant exists). Without this lookup, `missing_section` + `claude_agents` checks would compare a translated consumer file against the canonical EN baseline and falsely flag every translated line as drift, with Auto-fix corrupting the translation.

**`agents_sync.skipped == true`** = the project has no `.agents/skills/` directory, mirror check skipped (consuming projects may opt out of the mirror).

**`missing_section`** scans every `.md` file under the active project-skeleton root (canonical `templates/project-skeleton/` when consumer `content_language: en`; pre-generated variant `templates/project-skeleton.<lang>/` when the consumer's lang differs and a variant ships in the plugin) and reports any `^## ` header present in the template baseline but missing from the consumer's corresponding file. `skills_config.md`'s `## Language` section is one example — older projects that pre-date `## Language` will surface it here and Auto-fix appends a `_(TODO …)_` stub. Consumer-language-awareness in baseline selection prevents Auto-fix from appending canonical-EN headers into a translated consumer file.

**`missing_field`** is `missing_section`'s within-section counterpart, **scoped to `ai_context/skills_config.md` only** (per `ai_context/decisions.md` §Skill Implementation #13). It parses the baseline skills_config and the consumer's skills_config for top-level `<key>: <value>` bullets — both backticked form (`- \`content_language: en\`` under `## Language`) and plain form (`- Main branch: \`main\`` under `## Main branch policy`) — and reports any field key present in the baseline section but missing from the consumer's same section. Catches the upgrade case where a plugin release adds a new field inside an existing section (motivating example: `## Language` gaining `conversation_language` after T-LANG-CONFIG-SYSTEM), which `missing_section`'s `^## ` header scan cannot see. Auto-fix appends `<key>: _(TODO — added by /holo:update; fill via /go or direct edit)_` at the tail of the section's bullet list and **never modifies the value of an existing field** — stale-but-syntactically-valid values stay out of scope (semantic value validation is `/full-review`'s job). Other bullet shapes in skills_config.md (trailing-colon sub-block labels like `- pgrep patterns:` and their indented children, freestanding value-only bullets like `- \`(none)\`` under `## Source directories`) are intentionally not parsed as fields and cannot trigger findings.

**`gitignore_missing_lines`** (per `ai_context/decisions.md` §Skill Implementation #14) compares pattern lines in the active project-skeleton's `.gitignore` (canonical or `.<lang>` variant) against the consumer's `.gitignore`. One finding per missing pattern (mirrors `missing_section`'s one-finding-per-header shape so `total_drift` counts patterns, not files). Comments / section headers in the template are NOT parsed — only patterns; canonical form strips surrounding whitespace and preserves the leading `\#` escape verbatim so the pattern round-trips through `--fix` (a decoded `#foo` would re-parse as a comment on the next check, looping `--fix`; see `gitignore_pattern_lines` docstring in `scripts/holo_update_check.py`). Inline `#` mid-pattern is NOT a comment (git treats the whole line as the pattern). Orphan lines (in consumer but not in template) are intentionally NOT detected: extending `.gitignore` is normal consumer behaviour and reporting it would generate noise. **Auto-fix is append-only Phase 1** — the script invokes `gitignore_compute_union` and writes target verbatim + banner sentinel + missing patterns at the tail. The three-phase smart-merge pipeline's LLM-reorganize and gate stages (Phases 2 + 3) live in `/holo:init` Step 3.1 only; `/holo:update --fix` deliberately stays deterministic to respect the "does not touch user-filled content" philosophy (the LLM step is opt-in via re-running `/holo:init` on a CONFLICT).

**`missing_l1_directive`** (per Phase 5 of T-LANG-CONFIG-SYSTEM) scans every `commands/*.md` and `skills/*/SKILL.md` under `plugin_root` for the L1 language directive blockquote pattern `> **Language**:` within 12 lines after the frontmatter close. Missing files surface here. **Report-only — no auto-fix**: inserting prose into a skill body without the maintainer's review is risky enough that the maintainer fixes the file via `/go`.

**`l1_directive_drift`** (per Phase 4 of T-PLUGIN-SPECS-AND-CONFIG-AUDIT) is the structural sibling of `missing_l1_directive`: for every file that *has* an L1 blockquote, verify the blockquote text contains every canonical structural substring declared in `scripts/holo_update_check.py` `_L1_REQUIRED_SUBSTRINGS` (current set: the `§Language` reference path, the `disk-bound` bucket label, the `content_language` axis, the `user-facing` bucket label, the `conversation_language` axis, the `stay English` immutable-identifiers clause). Per-skill parenthetical examples within each bucket legitimately vary by design (Decision #10 anchor — each L1 names the specific disk-bound outputs of *that* skill), so text-equality is intentionally NOT used; required-substring drift catches the failure modes that matter (axis rename, bucket-label drop, immutable-clause omission). Findings list the specific missing substrings per file. **Report-only — no auto-fix**: same rationale as `missing_l1_directive`.

**`lang_mirror_drift`** (per Phase 5 of T-LANG-CONFIG-SYSTEM) scans `templates/project-skeleton.<lang>/` variant directories (any directory matching the pattern) and reports structural drift vs the canonical `templates/project-skeleton/`: `MISSING` (file present in canonical, absent in variant) and `ORPHAN` (file present in variant, absent in canonical). Content drift (`STALE`) is intentionally NOT detected — variant files differ in content by design (they are translations); semantic drift is the four-agent review chain's domain (`/holo:init` existing-directory translation path or a dedicated Phase 6 `/full-review` pass). **Report-only — no auto-fix**: variant content is human translation work; auto-overwrite would destroy it.

When no `.<lang>/` variant exists (current plugin state through Phase 5), `lang_mirror_drift` returns `[]`. Phase 6 of T-LANG-CONFIG-SYSTEM lands the first variants.

**`legacy_skip_marker`** (per T-INIT-SKIP-SEMANTICS / `ai_context/decisions.md` §Skill Implementation #15) scans consumer top-level + `ai_context/` + `docs/` `.md` files for `_(TODO — skipped at /holo:init; fill via later /go or directly edit)_` markers left over from the pre-three-bucket-schema init (the Round 3 Skip path wrote these 13-character short-TODOs; the path was deleted when the three-bucket schema landed). Findings list each marker's `rel` + `line` + `snippet`. **Excluded from `total_drift`** — same rationale as `claude_agents.unexpected_diffs`: historical / report-only items would drown actionable findings; the report surfaces the count separately. **Report-only — no auto-fix**: the correct replacement depends on the section's intent (delete + copy canonical `<...>` guidance back from the plugin template / write real content / leave the section empty via PROGRESSIVE `_(none yet — delete this marker once content is added)_`), which a deterministic script cannot decide. Surfacing it tells the user "this project is initialized under the old schema; here are the spots where template guidance was wiped — fix manually or via `/go`".

**Important**: this step **does not allow the skill body to re-author detection rules** — no custom grep / Python comparison, no filter / exclusion additions. If a case is mis-detected, missed, or falsely flagged, **edit the script, not the skill body**. The constraint is operative here in this skill body; `ai_context/decisions.md` §Skill Implementation #5 carries the rationale (real incident: an LLM running `/holo:update` translated prose rules into ad-hoc filters and masked a real MISSING drift — moving detection into the executable script removes the LLM's runtime degree of freedom).

## Step 3: Report + ask + auto-fix

> **Language**: disk-bound — write the fix-pass file changes (regenerating `.agents/skills/` mirror files, appending `_(TODO — added by /holo:update; fill via /go or direct edit)_` stub markers to `skills_config.md`) in `content_language` per `ai_context/skills_config.md §Language`. The `_(TODO …)_` marker text is structural and stays English. Code identifiers, file paths, field names stay English regardless.

> **Language**: user-facing — render the `Auto-fix all` / `Skip all` `<ask tool>` question, option labels, and the post-fix delta print in `conversation_language` per `ai_context/skills_config.md §Language`. JSON category keys (`missing_section`, `lang_mirror_drift`, `agents_sync.stale`, etc.) and file paths stay English (structural identifiers); the option-label prose `Auto-fix all` / `Skip all` translates to `conversation_language` like any other USER surface — there is no English-only requirement on the option labels themselves.

**3.1 Aggregated print**

Translate the script's JSON output into a natural-language report:

```
Plugin: <name> v<version>

.agents/skills/:    STALE=<P> | MISSING=<Q> | ORPHAN=<R>   <or "skipped (not present)">
  STALE   (P): <name list>
  MISSING (Q): <name list>
  ORPHAN  (R): <name list>

Templates:
  MISSING_TEMPLATE (S): <rel-path list>
  MISSING_SECTION  (T): <"<rel>: <header>" list>
  MISSING_FIELD    (X): <"<rel>: <section> → <key>" list>

Gitignore:
  GITIGNORE_MISSING_LINES (Y): <"<rel>: <pattern>" list>

CLAUDE.md / AGENTS.md (report-only — not counted in total_drift):
  first_line_placeholder: <true/false>
  unexpected_diffs:       <up to 10 line summaries> (+<unexpected_diffs_truncated> more truncated)

L1 language directive presence:
  MISSING_L1_DIRECTIVE (V): <rel-path list with reason>

Language-variant mirror drift:
  LANG_MIRROR_DRIFT (W): <"<variant>/<rel>: <kind>" list>

Legacy short-TODO marker (report-only — not counted in total_drift):
  LEGACY_SKIP_MARKER (Z): <"<rel>:<line>: <snippet>" list>
```

`total_drift = P + Q + R + S + T + X + Y + V + W`. CLAUDE/AGENTS
`unexpected_diffs` and `legacy_skip_marker` are intentionally NOT in
this sum — both buckets are report-only (never auto-fixable) and a
consumer with legitimate asymmetric guidance / pre-three-bucket-schema
legacy markers would drown actionable findings (STALE / MISSING) if
counted. Each bucket is still printed separately so the user sees the
count; the script caps `unexpected_diffs` at 10 entries and reports
the truncated count via `claude_agents.unexpected_diffs_truncated`.

`total_drift == 0` → print `✅ Project is in sync with <name> v<version>; nothing to do.` and exit.

**3.2 Ask (single aggregated question)**

`total_drift ≥ 1` → use **<ask tool>** to ask **one** question, showing all findings + the action for each category:

```
Found <total_drift> drift items (plugin: <name> v<version>):

.agents/skills/:
  STALE   (P): <names>   → script will regenerate via expected_mirror_content()
  MISSING (Q): <names>   → script will create
  ORPHAN  (R): <names>   → script will rm -rf .agents/skills/<name>/   ⚠️ deletion

Templates:
  MISSING_TEMPLATE (S): <paths>   → script will cp from templates/project-skeleton/
  MISSING_SECTION  (T): <list>    → script will append `## <header>` + _(TODO)_ marker
  MISSING_FIELD    (X): <list>    → script will append `<key>: _(TODO)_` marker inside the owning section

Gitignore:
  GITIGNORE_MISSING_LINES (Y): <list>   → script will append the missing pattern lines at the file tail with a banner separator (append-only Phase 1; no LLM, no orphan-line deletion — three-phase smart-merge pipeline runs only at /holo:init CONFLICT)

CLAUDE.md / AGENTS.md:
  <findings>   → never auto-merged (display only, manual handling required)

L1 language directive presence:
  <findings>   → report-only (display only, fix via /go on the affected skill body)

Language-variant mirror drift:
  <findings>   → report-only (display only, manual translation work via Phase 6 review chain)

Legacy short-TODO marker:
  <findings>   → report-only (display only; fix manually or via /go — delete + copy canonical `<...>` guidance back from plugin template, or write real content)

[Auto-fix all] / [Skip all]
```

Options:

- **`Auto-fix all`** (recommended):
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py" --fix --json
  ```
  CLAUDE/AGENTS findings are out of `--fix` scope (the script skips them by design); these two files are not touched
- **`Skip all`**: no modifications

**3.3 Apply + verify**

Pick `Auto-fix all` → invoke the script in `--fix --json` mode (note `--fix` implicitly runs `--check` first); it outputs `fix_counts` JSON. Then invoke `--json` once more (without `--fix`) for a post-fix self-check:

- `agents_sync.stale / missing / orphan` should all be 0
- `missing_template` should be 0
- `missing_section` should be 0
- `missing_field` should be 0
- `gitignore_missing_lines` should be 0
- `claude_agents.unexpected_diffs` may still be > 0 (out of `--fix` scope)
- `legacy_skip_marker` may still be > 0 (report-only; out of `--fix` scope per T-INIT-SKIP-SEMANTICS)

**Orphan sibling cleanup**: if `fix_counts.orphan_siblings_left` is non-empty, the script removed the `SKILL.md` of each orphan but kept other files under the parent directory (per the "no silent overwrite" rule). Print each entry to the user — e.g. `⚠️ kept sibling files under <parent>: <sibling list> (manual cleanup required)` — so the user knows to inspect and delete them.

Any of the first five post-fix items > 0 → report the anomaly and stop (indicates a script bug or permission issue; let the user decide).

## Step 4: Final print

> **Language**: user-facing — render the final summary printed to the user (`Update OK` / `Drift remaining` block, the count of fixed-vs-skipped findings, the next-steps suggestion) in `conversation_language` per `ai_context/skills_config.md §Language`. JSON category keys / file paths quoted in the summary stay verbatim; only surrounding prose translates.

```
✅ /holo:update complete

Plugin: <name> v<version>
.agents/skills/:    regenerated=A | created=B | deleted=C
Templates:          template_copied=D | section_appended=E | field_appended=F
Gitignore:          gitignore_appended=G
CLAUDE/AGENTS:      <OK / U warnings (manual fix needed)>

Suggested next steps (only when there are _(TODO)_ appends or manual sync):
  1. Review `_(TODO — added by /holo:update)_` markers and fill in actual content as needed
  2. If CLAUDE.md ↔ AGENTS.md have unexpected diffs, manually sync them and rerun diff to verify
  3. `/commit` to land the sync changes
```

## Constraints

- **Single source of truth for detection / fix rules** = `scripts/holo_update_check.py`; the skill body does not re-implement
- **Only touches structural drift introduced by the plugin upgrade** (missing files / missing section headers / stale mirror / orphan mirror); does not touch user-filled content
- **Does not `git add` / does not commit**: consistent with `/holo:init`, the user commits via `/commit`
- **CLAUDE/AGENTS not auto-merged**: the script `--fix` is designed not to touch these two files; it only reports them in check output
- To adjust detection rules → edit `scripts/holo_update_check.py`, then sync the Step 2 JSON contract description in this file + `commands/init.md` Step 3.2 per `ai_context/conventions.md` §Cross-File Alignment (e.g. if `expected_mirror_content` signature changes)
