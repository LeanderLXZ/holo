---
description: Project sync check after plugin upgrade — compare the current project against the installed plugin (`.agents/skills/` mirror, template new files / section headers, `CLAUDE.md` / `AGENTS.md` headers + §Language hardcoded values, sentinel-aware drift in marker-bearing `.md` files) and apply fixes. **All detection logic lives in the single script `${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py`**; the skill body does not re-implement rules. Conflict-triggering findings (`heading_drift` / `section_content_drift` / `claude_agents_lang_drift` co-existing with other conflicts / file-body language mismatch) → smart-merge dispatch (4 sub-agent parallel + three-layer ask + `take_snapshot` backup, per `docs/architecture/smart-merge.md`). Other fixable findings (`missing_template` / `missing_section` / `missing_field` / `gitignore_missing_lines` / `lang_mirror_drift` / `agents_sync.stale` / standalone `claude_agents_lang_drift`) → deterministic `--fix`. Display-only by design: `claude_agents.unexpected_diffs` (CLAUDE↔AGENTS asymmetric guidance), `legacy_skip_marker`, `missing_l1_directive` / `l1_directive_drift` (skill-body prose). 0 drift passes silently. No arguments; preserves user-territory content (everything outside sentinel blocks + user-added non-marker sections); does not git add, does not commit. Triggers: /holo:update / plugin upgraded / sync holo update / check whether holo is up to date.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (regenerated `.agents/skills/` mirror files, `_(TODO — added by /holo:update)_` markers appended to `skills_config.md`, any in-place file edits) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / drift-category report / final summary / `Auto-fix all` / `Skip all` confirmations) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, JSON keys returned by `holo_update_check.py` (`missing_section`, `lang_mirror_drift`, `agents_sync.stale`, `legacy_skip_marker`, etc.), and structural prefixes (`Step N:`, `DRIFT:`, `OK:`) stay English regardless.

# /holo:update — project sync check after plugin upgrade

Compare plugin-linked artifacts in the current project (`.agents/skills/` mirror, `templates/project-skeleton/` files + section headers, `CLAUDE.md` / `AGENTS.md` headers) against the currently installed plugin (`${CLAUDE_PLUGIN_ROOT}`), surface drift where "the plugin upgraded but the project did not follow," and apply batch fixes after a single aggregated question.

**Detection rules single source of truth = `${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py`**. The skill body **does not re-implement detection logic**; to adjust rules, edit the script and sync this file + `commands/init.md` Step 3.2 per `ai_context/conventions.md` §Cross-File Alignment. Background in `ai_context/decisions.md` §Skill Implementation #5.

No arguments. **Touches plugin-owned content** (sentinel blocks, plugin canonical sections, mirrored `.agents/skills/`); **preserves user-territory content** (everything outside `<!-- holo:section start/end -->` blocks + user-added non-marker headings — see `docs/architecture/section-version-sentinel.md`). For conflict-triggering findings (sentinel-aware drift or file-body language mismatch) `/holo:update` invokes the smart-merge dispatch flow (`docs/architecture/smart-merge.md`); for deterministic fixable findings it runs `holo_update_check.py --fix`; for display-only findings (`unexpected_diffs` / `legacy_skip_marker` / L1 directives) it surfaces the count without touching the file.

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
  "claude_agents_lang_drift": [{"rel": "CLAUDE.md|AGENTS.md",
                                "axis": "content_language|conversation_language",
                                "expected": "<skills_config value>",
                                "actual": "<file value or null>"}],
  "missing_l1_directive": [{"rel": "commands/<name>.md|skills/<name>/SKILL.md", "reason": "..."}],
  "l1_directive_drift":   [{"rel": "commands/<name>.md|skills/<name>/SKILL.md", "missing_substrings": ["..."]}],
  "lang_mirror_drift":    [{"variant": "project-skeleton.<lang>", "rel": "...", "kind": "MISSING|ORPHAN"}],
  "legacy_skip_marker":   [{"rel": "ai_context/<...>.md", "line": N, "snippet": "..."}],
  "heading_drift":        [{"rel": "...", "kind": "consumer_orphan_heading",
                            "header": "## ...", "source_path": "..."}],
  "section_content_drift": [{"rel": "...", "section": "## ... | preamble",
                             "block_index": N,
                             "plugin_excerpt": "...", "consumer_excerpt": "...",
                             "diff_summary": "..."}]
}
```

**`consumer_content_lang`** = the 2-letter ISO 639-1 value read from the consumer project's `ai_context/skills_config.md §Language`'s `content_language` field; defaults to `"en"` when the file / section / field is absent. Drives the active project-skeleton baseline (canonical `templates/project-skeleton/` when `en`; pre-generated variant `templates/project-skeleton.<lang>/` when non-en and a variant ships in the plugin; canonical fallback when no variant exists). Without this lookup, `missing_section` + `claude_agents` checks would compare a translated consumer file against the canonical EN baseline and falsely flag every translated line as drift, with Auto-fix corrupting the translation.

**`agents_sync.skipped == true`** = the project has no `.agents/skills/` directory, mirror check skipped (consuming projects may opt out of the mirror).

**`missing_section`** scans every `.md` file under the active project-skeleton root (canonical `templates/project-skeleton/` when consumer `content_language: en`; pre-generated variant `templates/project-skeleton.<lang>/` when the consumer's lang differs and a variant ships in the plugin) and reports any `^## ` header present in the template baseline but missing from the consumer's corresponding file. `skills_config.md`'s `## Language` section is one example — older projects that pre-date `## Language` will surface it here and Auto-fix appends a `_(TODO …)_` stub. Consumer-language-awareness in baseline selection prevents Auto-fix from appending canonical-EN headers into a translated consumer file.

**`missing_field`** is `missing_section`'s within-section counterpart, **scoped to `ai_context/skills_config.md` only** (per `ai_context/decisions.md` §Skill Implementation #13). It parses the baseline skills_config and the consumer's skills_config for top-level `<key>: <value>` bullets — both backticked form (`- \`content_language: en\`` under `## Language`) and plain form (`- Main branch: \`main\`` under `## Main branch policy`) — and reports any field key present in the baseline section but missing from the consumer's same section. Catches the upgrade case where a plugin release adds a new field inside an existing section (motivating example: `## Language` gaining `conversation_language` after T-LANG-CONFIG-SYSTEM), which `missing_section`'s `^## ` header scan cannot see. Auto-fix appends `<key>: _(TODO — added by /holo:update; fill via /go or direct edit)_` at the tail of the section's bullet list and **never modifies the value of an existing field** — stale-but-syntactically-valid values stay out of scope (semantic value validation is `/full-review`'s job). Other bullet shapes in skills_config.md (trailing-colon sub-block labels like `- pgrep patterns:` and their indented children, freestanding value-only bullets like `- \`(none)\`` under `## Source directories`) are intentionally not parsed as fields and cannot trigger findings.

**`gitignore_missing_lines`** (per `ai_context/decisions.md` §Skill Implementation #14) compares pattern lines in the active project-skeleton's `.gitignore` (canonical or `.<lang>` variant) against the consumer's `.gitignore`. One finding per missing pattern (mirrors `missing_section`'s one-finding-per-header shape so `total_drift` counts patterns, not files). Comments / section headers in the template are NOT parsed — only patterns; canonical form strips surrounding whitespace and preserves the leading `\#` escape verbatim so the pattern round-trips through `--fix` (a decoded `#foo` would re-parse as a comment on the next check, looping `--fix`; see `gitignore_pattern_lines` docstring in `scripts/holo_update_check.py`). Inline `#` mid-pattern is NOT a comment (git treats the whole line as the pattern). Orphan lines (in consumer but not in template) are intentionally NOT detected: extending `.gitignore` is normal consumer behaviour and reporting it would generate noise. **Auto-fix is append-only Phase 1** — the script invokes `gitignore_compute_union` and writes target verbatim + banner sentinel + missing patterns at the tail. The three-phase smart-merge pipeline's LLM-reorganize and gate stages (Phases 2 + 3) live in `/holo:init` Step 3.1 only; `/holo:update --fix` deliberately stays deterministic to respect the "does not touch user-filled content" philosophy (the LLM step is opt-in via re-running `/holo:init` on a CONFLICT).

**`claude_agents_lang_drift`** (per `ai_context/decisions.md` §Language Configuration #17) compares the hardcoded `content_language` + `conversation_language` bullets in the consumer's `CLAUDE.md` / `AGENTS.md` §Language block against the canonical values in `ai_context/skills_config.md §Language`. One finding per (file, axis) pair: value mismatch (`actual` is the file's hardcoded value) or missing bullet (`actual` is `null`). Source-of-truth model: skills_config canonical, CLAUDE/AGENTS read-cache. **Auto-fix** rewrites the bullet value (when `actual` is not `null`) or inserts a canonical bullet next to the sibling axis bullet (when `actual` is `null` and the sibling bullet exists). If neither axis bullet is present, the §Language block is structurally pre-#17 (pointer-prose format) — fix skips silently and the post-`--check` will keep surfacing the drift, prompting manual upgrade or re-init. Findings counted in `total_drift`. Distinct from `claude_agents.unexpected_diffs` (CLAUDE↔AGENTS line-diff vs the expected `_EN_EXPECTED_PAIRS` / variant-derived pairs — report-only, never auto-fixable); the two checks share the entry-file pair as scope but answer different questions (cross-sync vs canonical-sync).

**`missing_l1_directive`** (per Phase 5 of T-LANG-CONFIG-SYSTEM) scans every `commands/*.md` and `skills/*/SKILL.md` under `plugin_root` for the L1 language directive blockquote pattern `> **Language**:` within 12 lines after the frontmatter close. Missing files surface here. **Report-only — no auto-fix**: inserting prose into a skill body without the maintainer's review is risky enough that the maintainer fixes the file via `/go`.

**`l1_directive_drift`** (per Phase 4 of T-PLUGIN-SPECS-AND-CONFIG-AUDIT) is the structural sibling of `missing_l1_directive`: for every file that *has* an L1 blockquote, verify the blockquote text contains every canonical structural substring declared in `scripts/holo_update_check.py` `_L1_REQUIRED_SUBSTRINGS` (current set: the `§Language` reference path, the `disk-bound` bucket label, the `content_language` axis, the `user-facing` bucket label, the `conversation_language` axis, the `stay English` immutable-identifiers clause). Per-skill parenthetical examples within each bucket legitimately vary by design (Decision #10 anchor — each L1 names the specific disk-bound outputs of *that* skill), so text-equality is intentionally NOT used; required-substring drift catches the failure modes that matter (axis rename, bucket-label drop, immutable-clause omission). Findings list the specific missing substrings per file. **Report-only — no auto-fix**: same rationale as `missing_l1_directive`.

**`lang_mirror_drift`** (per Phase 5 of T-LANG-CONFIG-SYSTEM) scans `templates/project-skeleton.<lang>/` variant directories (any directory matching the pattern) and reports structural drift vs the canonical `templates/project-skeleton/`: `MISSING` (file present in canonical, absent in variant) and `ORPHAN` (file present in variant, absent in canonical). Content drift (`STALE`) is intentionally NOT detected — variant files differ in content by design (they are translations); semantic drift is the four-agent review chain's domain (`/holo:init` existing-directory translation path or a dedicated Phase 6 `/full-review` pass). **Report-only — no auto-fix**: variant content is human translation work; auto-overwrite would destroy it.

When no `.<lang>/` variant exists (current plugin state through Phase 5), `lang_mirror_drift` returns `[]`. Phase 6 of T-LANG-CONFIG-SYSTEM lands the first variants.

**`legacy_skip_marker`** (per T-INIT-SKIP-SEMANTICS / `ai_context/decisions.md` §Skill Implementation #15) scans consumer top-level + `ai_context/` + `docs/` `.md` files for `_(TODO — skipped at /holo:init; fill via later /go or directly edit)_` markers left over from the pre-three-bucket-schema init (the Round 3 Skip path wrote these 13-character short-TODOs; the path was deleted when the three-bucket schema landed). Findings list each marker's `rel` + `line` + `snippet`. **Excluded from `total_drift`** — same rationale as `claude_agents.unexpected_diffs`: historical / report-only items would drown actionable findings; the report surfaces the count separately. **Report-only — no auto-fix**: the correct replacement depends on the section's intent (delete + copy canonical `<...>` guidance back from the plugin template / write real content / leave the section empty via PROGRESSIVE `_(none yet — delete this marker once content is added)_`), which a deterministic script cannot decide. Surfacing it tells the user "this project is initialized under the old schema; here are the spots where template guidance was wiped — fix manually or via `/go`".

**`heading_drift`** (per `ai_context/decisions.md` §Skill Implementation #18) is sentinel-aware: for each plugin template `.md` whose consumer counterpart has at least one `<!-- holo:heading -->` marker, the script compares the consumer's marker-bearing heading list (H1 + H2) against the plugin template's marker-bearing heading list and reports `consumer_orphan_heading` findings (each finding carries `level: 1` for H1 or `level: 2` for H2). The reverse direction (plugin has heading, consumer doesn't) is covered by `missing_section` (for H2) — the two paths intentionally do not double-flag. Pre-sentinel consumers (no markers anywhere) skip silently and `missing_section` handles plugin→consumer alone, preserving backward compatibility. **Report-only — NOT in `total_drift`, NOT auto-fixed by `--fix`.** The script cannot disambiguate rename vs deletion vs stale-marker deterministically; the correct fix path is [T-INIT-UPDATE-SMART-MERGE]'s extract-and-reformat smart-merge, which takes the new plugin template's heading list as authoritative and refills user content from the old consumer file by semantic match. Earlier `apply_heading_rename` helper + Step 3.1.5 LLM rename correlation flow were reverted as over-engineering — that "piecemeal rename + body sync" approach duplicated what smart-merge does correctly in a single pass.

**`section_content_drift`** (per `ai_context/decisions.md` §Skill Implementation #18) is sentinel-aware byte-diff of plugin canonical block bodies. Fires only when BOTH plugin template and consumer carry at least one `<!-- holo:section start -->` marker. For each H2 section + preamble region present in both files, position-aligned blocks are byte-compared after light normalization (trailing whitespace + PROGRESSIVE-marker stripping as defense-in-depth; PROGRESSIVE markers should not appear inside sentinel blocks after the sentinel-design-refinement bootstrap, but the strip stays as a fallback). Plugin blocks that normalize to **empty** skip drift comparison (no canonical content to enforce). Plugin blocks with real prose that differs from the consumer block produce a finding carrying a 3-line excerpt of each side + a 6-line unified-diff summary so the user can eyeball the change without opening the files. **Report-only — NOT in `total_drift`, NOT auto-fixed by `--fix`**: the correct fix path is [T-INIT-UPDATE-SMART-MERGE]'s extract-and-reformat smart-merge (extract user info from old consumer file, refill into new plugin sentinel structure). The earlier "snapshot + overwrite consumer block with plugin canonical" auto-fix wiring was reverted as over-engineering — it loses user-added content inside sentinel blocks; the smart-merge handles this correctly by treating the new plugin template's sentinel structure as authoritative while preserving user values via extract-and-reformat.

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

CLAUDE.md / AGENTS.md cross-sync (report-only — not counted in total_drift):
  first_line_placeholder: <true/false>
  unexpected_diffs:       <up to 10 line summaries> (+<unexpected_diffs_truncated> more truncated)

CLAUDE.md / AGENTS.md §Language hardcoded-value drift:
  CLAUDE_AGENTS_LANG_DRIFT (U): <"<rel>: <axis> expected=<v> actual=<v>" list>

L1 language directive presence:
  MISSING_L1_DIRECTIVE (V): <rel-path list with reason>

Language-variant mirror drift:
  LANG_MIRROR_DRIFT (W): <"<variant>/<rel>: <kind>" list>

Legacy short-TODO marker (report-only — not counted in total_drift):
  LEGACY_SKIP_MARKER (Z): <"<rel>:<line>: <snippet>" list>

Sentinel-aware drift (smart-merge trigger — enters Step 3.2 conflict ask):
  HEADING_DRIFT (HD): <"<rel>: <header> (consumer_orphan_heading, level=N)" list>
  SECTION_CONTENT_DRIFT (SCD): <"<rel>: <section> [block N]" list, with 6-line diff snippet per entry>
```

`total_drift = P + Q + R + S + T + X + Y + U + V + W`. CLAUDE/AGENTS
`unexpected_diffs`, `legacy_skip_marker`, `heading_drift`, and
`section_content_drift` are intentionally NOT in this sum.
CLAUDE/AGENTS cross-sync + legacy markers are by-design report-only
(no script-side fix exists). `heading_drift` + `section_content_drift`
are excluded from `total_drift` because their fix path is the
smart-merge ask flow (`docs/architecture/smart-merge.md`), not the
deterministic `--fix` path that `total_drift` tracks — Step 3.2
classifies each file carrying these findings as a conflict-triggering
file and runs the smart-merge dispatch on it (Agent 1 generates a
full-file rewrite that preserves user content under the new plugin
sentinel structure; Agent 2/3/4 verify; one retry on FAIL then user
surface). Each bucket is still printed separately so the user sees
the count; the script caps `unexpected_diffs` at 10 entries and
reports the truncated count via
`claude_agents.unexpected_diffs_truncated`. `claude_agents_lang_drift`
(U) IS counted in `total_drift` because the lightweight
`fix_claude_agents_lang_drift` auto-fix (field-level bullet sync per
decisions.md §Language Configuration #17) handles it deterministically
when the affected file has NO other conflict-triggering finding;
when `claude_agents_lang_drift` co-exists with `heading_drift` /
`section_content_drift` / file-body language mismatch on the same
file, Step 3.2 routes the file to smart-merge instead and the
lightweight auto-fix is skipped for that file (the merger sub-agent
rewrites the §Language block per skills_config canonical values as
part of the full-file rewrite).

`total_drift == 0` → print `✅ Project is in sync with <name> v<version>; nothing to do.` and exit.

**3.2 Conflict triage**

Before asking the user, classify each finding into one of three buckets so Step 3.3 can route them to the right handler:

1. **Conflict-triggering** (route to smart-merge dispatch) — per file:
   - `heading_drift` finding for that file (consumer-orphan marker-bearing H1 / H2), OR
   - `section_content_drift` finding for that file (plugin canonical block body differs from consumer's at same sentinel position), OR
   - **file-body language mismatch** for that file: run a CJK heuristic pass on each consumer `.md` file in the template manifest (sample first ~200 non-whitespace chars; ≥30% CJK chars → `zh`, else `en`); a file whose detected language ≠ `consumer_content_lang` (from skills_config.md §Language) counts as language-mismatch. Cache the per-file detection result for Step 3.3.
2. **Deterministic auto-fix** (route to `holo_update_check.py --fix`):
   - `agents_sync.stale` / `agents_sync.missing` / `agents_sync.orphan`, `missing_template`, `missing_section`, `missing_field`, `gitignore_missing_lines`, `lang_mirror_drift`, AND
   - `claude_agents_lang_drift` **for files that have NO conflict-triggering finding** (standalone §Language drift goes through the lightweight `fix_claude_agents_lang_drift` field-level sync per decisions.md §Language Configuration #17). When a file has both `claude_agents_lang_drift` AND a conflict-triggering finding (rare but possible if a user manually edits §Language in CLAUDE.md AND breaks the sentinel structure), the file routes to bucket 1 and the merger sub-agent absorbs the §Language fix.
3. **Display-only by design** (no fix, surface to user):
   - `claude_agents.unexpected_diffs` (CLAUDE↔AGENTS asymmetric guidance — script never auto-merges; user resolves manually).
   - `legacy_skip_marker` (out of `--fix` scope per T-INIT-SKIP-SEMANTICS).
   - `missing_l1_directive` / `l1_directive_drift` (skill-body prose; fix via `/go` on the affected skill body).

Build a `<conflict_files>` list = the set of consumer file paths in bucket 1. If `len(<conflict_files>) == 0` and bucket 2 = ∅ and bucket 3 surfaces nothing actionable → equivalent to `total_drift == 0`; print sync-OK and exit (already handled by Step 3.1).

**3.3 Ask (batched, up to 4 questions per `<ask tool>` call)**

Compose the question batch:

- **Q-conflict** (only when `len(<conflict_files>) ≥ 1`) — Layer 1 aggregate ask per `docs/architecture/smart-merge.md`. One question, 5 options:
  1. Smart-merge all — for each file in `<conflict_files>`, dispatch the 4 sub-agents in parallel per smart-merge.md.
  2. Overwrite all with new plugin version — `take_snapshot(target_root=".", slug="holo-update-smart-merge", file_paths=<conflict_files>)` then overwrite each file with the resolved new plugin template content.
  3. Keep all existing files (no merge) — leave each conflict file as-is.
  4. Per-file confirmation → Layer 2 ask per file (4 options each: smart-merge / overwrite with new plugin / keep (no merge) / skip current file). When `len(<conflict_files>) > 3` the Layer 2 fan-out emits ceil(N/4) `<ask tool>` batches.
  5. Skip this step — skip smart-merge entirely.
- **Q-fixable** (only when bucket 2 ≠ ∅) — Auto-fix all / Skip all for the deterministic-fixable findings list (display the categories + counts inline). One question, 2 options.

Dispatch Q-conflict + Q-fixable in **one batched `<ask tool>` call** (max 4 questions per call; both questions fit). Display-only findings (bucket 3) are printed inline above the ask block — no question for them.

Question batch wording template (translated to `conversation_language`):

```
Found <total_drift> drift items, broken down as:
- Conflict files (routed to smart-merge dispatch): <len(<conflict_files>)> — <list of conflict file paths with their trigger types>
- Deterministic auto-fix: <bucket 2 count> — <category counts>
- Display-only (manual handling): <bucket 3 count> — <category counts>

[Q-conflict ask] [Q-fixable ask]
```

**Template source resolution for smart-merge dispatch** — `/holo:update` resolves per `docs/architecture/smart-merge.md` "Template source resolution" section: prefer `${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton.<content_language>/` variant when present; fall back to canonical `templates/project-skeleton/` + on-the-fly 4-agent translation chain (reuse `commands/init.md` Step 2.5's chain) writing to `<system_tmp>/holo-tmp-<YYYY-MM-DD>_<HHMMSS>/templates/...` (plugin is read-only). The tmp path persists until `/holo:update` exits.

**3.4 Apply + verify**

Execute each ask answer independently:

**Q-conflict answer** (if dispatched at Step 3.3):
- Option 1 (Smart-merge all) → for each file in `<conflict_files>`, dispatch the 4 sub-agents in parallel per `docs/architecture/smart-merge.md` "4-sub-agent dispatch" section. Each sub-agent prompt MUST include: paths to consumer file + resolved new plugin template (per Step 3.3 template source resolution) + snapshot file, the sentinel marker rules from `docs/architecture/section-version-sentinel.md`, the smart-merge logic from `docs/architecture/smart-merge.md` (trigger conditions / three-layer ask / Layer 3 orphan-content fallback / edge cases), and the target `content_language` value. **Place the language axes injection at the end of each sub-agent prompt** (recency-favorable position, per Decision #16). Agent 1 (merger+translator) returns merged output to a staging tmp path; Agent 2/3/4 verify (Agent 4 conditional on translation happening); fix-loop = one Agent 1 retry on FAIL; second FAIL surfaces the staging output + outstanding findings with a 3-option user ask per smart-merge.md "Failure surface".
- Option 2 (Overwrite all with new plugin) → call `take_snapshot(target_root=".", slug="holo-update-smart-merge", file_paths=<conflict_files>)`, then write each file with the resolved plugin template content.
- Option 3 (Keep all existing files) → no action.
- Option 4 (Per-file confirmation) → run Layer 2 ask per file (smart-merge.md "Layer 2 — per-file"); execute per per-file choice.
- Option 5 (Skip this step) → no action.

For Layer 1 options 1 and 2 (and Layer 2 options 1 and 2): backup is mandatory; `take_snapshot` runs before any disk write. Surface the snapshot directory path in the Step 4 final print so the user knows where to restore from.

**Q-fixable answer** (if dispatched at Step 3.3):
- `Auto-fix all` → invoke the script:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py" --fix --json
  ```
  `--fix` implicitly runs `--check` first; outputs `fix_counts` JSON. Then invoke `--json` once more (without `--fix`) for a post-fix self-check:
  - `agents_sync.stale / missing / orphan` should all be 0
  - `missing_template` should be 0
  - `missing_section` should be 0
  - `missing_field` should be 0
  - `gitignore_missing_lines` should be 0
  - `claude_agents_lang_drift` should be 0 for files in bucket 2 (standalone §Language drift; lightweight `fix_claude_agents_lang_drift` field-level sync handles it); may remain > 0 for files routed to bucket 1 (smart-merge subsumes that fix) or for structurally pre-#17 §Language blocks (script skips silently — user re-runs /holo:init or manually upgrades)
  - `claude_agents.unexpected_diffs` may still be > 0 (display-only by design, out of `--fix` scope)
  - `legacy_skip_marker` may still be > 0 (display-only by design, out of `--fix` scope per T-INIT-SKIP-SEMANTICS)
  - `heading_drift` may still be > 0 (resolved by Q-conflict path, not by `--fix`)
  - `section_content_drift` may still be > 0 (resolved by Q-conflict path, not by `--fix`)
- `Skip all` → no script invocation.

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
CLAUDE/AGENTS:      lang_fixed=H | <OK / U cross-sync warnings (manual fix needed)>
Smart-merge:        files_merged=M | files_overwritten=N | files_kept=K | files_failed_after_retry=Z
Snapshot:           <snapshot_dir or "(none — no smart-merge writes this run)">

Suggested next steps (only when there are _(TODO)_ appends, manual sync, or smart-merge failures):
  1. Review `_(TODO — added by /holo:update)_` markers and fill in actual content as needed
  2. If CLAUDE.md ↔ AGENTS.md have unexpected diffs, manually sync them and rerun diff to verify
  3. If smart-merge surfaced any failed-after-retry files (Z > 0), inspect the staging output the smart-merge dispatch saved + the snapshot, then resolve manually
  4. `/commit` to land the sync changes
```

## Constraints

- **Single source of truth for detection / fix rules** = `scripts/holo_update_check.py`; the skill body does not re-implement
- **Only touches structural drift introduced by the plugin upgrade** (missing files / missing section headers / stale mirror / orphan mirror); does not touch user-filled content
- **Does not `git add` / does not commit**: consistent with `/holo:init`, the user commits via `/commit`
- **CLAUDE/AGENTS cross-sync not auto-merged**: the script `--fix` is designed not to touch CLAUDE↔AGENTS asymmetric guidance lines (`claude_agents.unexpected_diffs`); it only reports them in check output. Distinct from §Language hardcoded-value sync (`claude_agents_lang_drift`), which IS auto-fixable — the two checks scope the same file pair but answer different questions (cross-sync vs canonical-sync)
- To adjust detection rules → edit `scripts/holo_update_check.py`, then sync the Step 2 JSON contract description in this file + `commands/init.md` Step 3.2 per `ai_context/conventions.md` §Cross-File Alignment (e.g. if `expected_mirror_content` signature changes)
