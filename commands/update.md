---
description: Project sync check after plugin upgrade — thin user-entry shell around the shared `## Reconcile core` SOP defined in this same file (`/holo:update` mode=update and `/holo:init` Step 4 mode=init-post-bootstrap both flow through it; single source of truth). Reconcile core 6 sub-steps: template inventory → language alignment → NEW file copy → drift detection via scripts/holo_update_check.py → 3-bucket dispatch (smart-merge for sentinel_layout_drift / deterministic --fix for missing_template+section+field / gitignore_missing_lines / agents_sync / claude_agents_lang_drift / display-only for the rest) → return. File-body language mismatch is preprocessed by Reconcile.Step 2b, not a smart-merge trigger. 0 drift passes silently. No arguments; preserves user-territory content; does not git add or commit. Triggers: /holo:update / plugin upgraded / sync holo update / check whether holo is up to date.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (regenerated `.agents/skills/` mirror files, `_(TODO — added by /holo:update)_` markers appended to `skills_config.md`, any in-place file edits) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / drift-category report / final summary / `Auto-fix all` / `Skip all` confirmations) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, JSON keys returned by `holo_update_check.py` (`missing_section`, `lang_mirror_drift`, `agents_sync.stale`, `legacy_skip_marker`, etc.), and structural prefixes (`Step N:`, `DRIFT:`, `OK:`) stay English regardless.

# /holo:update — project sync check after plugin upgrade

Thin user-entry shell around the shared **`## Reconcile core`** SOP defined later in this same file. The Reconcile core implements the 6-sub-step per-file landing protocol that both `/holo:update` (this command, `mode="update"`) and `/holo:init` Step 4 (`mode="init-post-bootstrap"`) invoke. `/holo:update`'s shell adds plugin-upgrade-specific framing — print plugin name + version, gate on init-presence — then calls Reconcile core and renders its return values.

**Detection rules single source of truth = `${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py`**. The skill body **does not re-implement detection logic**; to adjust rules, edit the script. Background in `ai_context/decisions.md` §Skill Implementation #5.

No arguments. **Touches plugin-owned content** (sentinel blocks, plugin canonical sections, mirrored `.agents/skills/`); **preserves user-territory content** (everything outside `<!-- holo:section start/end -->` blocks + user-added non-marker headings — see `docs/architecture/section-version-sentinel.md`). Conflict-triggering findings invoke smart-merge dispatch via Reconcile.Step 5a (`docs/architecture/smart-merge.md`); deterministic-fixable findings run via Reconcile.Step 5b's `--fix`; display-only findings surface inline via Reconcile.Step 5c.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`. Sub-task entries `Step 2a:` ~ `Step 2f:` follow the same rule.

The user-entry shell is split into `## Step 0:` ~ `## Step 3:`.

**Before entering Step 0**: call **<progress tool>** to pre-register Step 0 ~ Step 3 (`status` all `pending`). **Do not proceed without calling <progress tool>**.

On entering each step: flip the current step to `in_progress` and mark the previous one `completed`.

**Sub-tasks on Step 2 (recommended)**: when Step 2 invokes Reconcile core, expand `Step 2:` into `Step 2a:` ~ `Step 2f:` matching the 6 Reconcile sub-steps (per the `/go` skill's sub-task expansion contract — only the currently active step is fine-grained; Step 0 / 1 / 3 stay collapsed). Fold back into `Step 2:` `completed` when entering Step 3.

**<progress tool> resolution**: Claude → `TodoWrite`; Codex → `update_plan`; other runtimes → maintain a markdown checkbox list in the response text.

**<ask tool> resolution**: Claude → `AskUserQuestion`; other runtimes → enumerate questions + options in the response text and let the user answer them in one pass.

## Step 0: Load skills config

`Read` `ai_context/skills_config.md`.

- File missing / any section header missing → fail loudly: print the missing items + prompt to complete per plugin template, stop
- Section content `(none)` or empty → skip the related steps for that section (treat as N/A in this project)
- Section lists concrete paths but the path does not exist → fail loudly: report the section drifting to a nonexistent path, stop and wait for the user to fix

Subsequent steps referencing "skills_config.md `## XX`" use this config. This command uses:
`## Language` (Step 2 / Reconcile.Step 2 reads the consumer's `content_language` for active project-skeleton baseline selection — the script `holo_update_check.py` does this internally; this Step 0 load is the skill-body anchor confirming the §Language section exists before the script runs).
`## Tmp directory` (Step 2 / Reconcile.Step 2a + Step 5a — smart-merge transient artifact root).

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

## Step 2: Invoke Reconcile core

Call the **`## Reconcile core`** SOP (defined later in this file) with:

```
mode = "update"
target_root = "."                                       # consumer project root (or absolute path if /holo:update ran from a subdir)
plugin_root = "${CLAUDE_PLUGIN_ROOT}"
content_language = <consumer skills_config §Language content_language value>
```

Reconcile core returns:

```
{
  write_counts: { merged: M, overwritten: N, kept: K, failed: Z, new_copied: P, deterministic_fixed: Q },
  fix_counts: { regenerated, created, deleted, template_copied, section_appended, field_appended, gitignore_appended, claude_agents_lang_fixed, orphan_siblings_left },  # raw `holo_update_check.py --fix --json` output verbatim — Step 3 maps these to A/B/C/D/E/F/G/H counters in the final print
  snapshot_dir: "<path or null>",
  remaining_drift: [...],          # findings that still surface after dispatch (display-only bucket + user-skipped conflict-triggering)
  translation_log: [...]
}
```

Carry these return values through to Step 3 for the final print. Mid-Step-2 errors (Reconcile sub-step IO failure / sub-agent dispatch failure / `--fix` non-zero exit) bubble up from Reconcile core with explicit cause; `/holo:update` does not swallow them — surface and stop per Reconcile's own contract.

## Step 3: Final print

> **Language**: user-facing — render the final summary printed to the user (`Update OK` / `Drift remaining` block, the count of fixed-vs-skipped findings, the next-steps suggestion) in `conversation_language` per `ai_context/skills_config.md §Language`. JSON category keys / file paths quoted in the summary stay verbatim; only surrounding prose translates.

Build the final print from Reconcile.Step 6's return values:

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

Mapping: `Reconcile.Step 6.write_counts.merged` → `M`, `.overwritten` → `N`, `.kept` → `K`, `.failed` → `Z`. `Reconcile.Step 6.fix_counts.{regenerated, created, deleted, template_copied, section_appended, field_appended, gitignore_appended, claude_agents_lang_fixed}` → `A / B / C / D / E / F / G / H` directly. `write_counts.new_copied` (Reconcile.Step 3 NEW file count — for `/holo:update` typically 0 since the consumer is already initialized; non-zero only when the plugin upgrade added new template files) → folded into the `Templates` row's `template_copied=D` count for display only (the two counters mean "new from Step 3 NEW-path" and "new from Step 5b deterministic-fix", both display under the same row).

`total_drift = 0` ⇔ `fix_counts` is all-zero AND smart-merge dispatch list was empty AND `remaining_drift` is empty → print `✅ Project is in sync with <name> v<version>; nothing to do.` and exit.

## Reconcile core

> **Language**: this is a SOP block consumed by both `/holo:update` (Step 2 above) and `/holo:init` Step 4. Caller is responsible for loading `skills_config.md §Language`; Reconcile core receives `content_language` as an input parameter and uses it directly. Disk-bound work follows `content_language`; user-facing asks + reports follow `conversation_language` per the L1 directive at the top of this file (and the equivalent L1 in `commands/init.md` when invoked from init).

> **Language (sub-agent dispatch)**: Reconcile.Step 2 dispatches sub-agents for 4-agent translation chains (Phase 1 Semantic fidelity → Phase 2 Glossary / Structure / Back-translation parallel). The parent MUST inject the language axes into each sub-agent's prompt explicitly. Include verbatim: "Reply in `conversation_language`=`<value>`; write any disk artifacts in `content_language`=`<value>`; both values from `ai_context/skills_config.md §Language`." Sub-agents do not inherit the parent's language config — they must be told. **Place this injection at the end of the sub-agent prompt** (recency-favorable position, per `ai_context/decisions.md` §Language Configuration #16). Reconcile.Step 5a smart-merge dispatch follows the same injection pattern (see `docs/architecture/smart-merge.md` 4-sub-agent dispatch section + Decision #16).

**Signature**:

```
Reconcile(target_root, plugin_root, mode, content_language) →
  { write_counts: { merged, overwritten, kept, failed, new_copied, deterministic_fixed },
    snapshot_dir,
    remaining_drift,
    translation_log }
```

**Inputs**:
- `target_root` — consumer project root (absolute path or `.`).
- `plugin_root` — `${CLAUDE_PLUGIN_ROOT}`.
- `mode` — `"update"` (called by `/holo:update`) or `"init-post-bootstrap"` (called by `/holo:init` Step 4). Mode-specific behavior is intentionally minimal: the only difference is that `init-post-bootstrap` mode tolerates a **higher NEW-file count** (caller asserted the project is initialized but allows skeleton gaps) while `update` mode expects most files already present (NEW > 0 indicates the plugin added new files since the last init).
- `content_language` — ISO 639-1 code; consumer's target language read from `skills_config.md §Language`.

**Precondition**: project is initialized (CLAUDE.md / AGENTS.md / `ai_context/` at least one exists on disk). Caller (the user-entry shell) enforces this; Reconcile core may assume it.

**What Reconcile core does NOT do** (caller responsibilities):
- Does NOT load `skills_config.md` (caller does).
- Does NOT do pre-check (caller does).
- Does NOT print the final summary (caller does).
- Does NOT collect user-driven Q&A like project name / Round 1 answers (init's caller shell does this before calling Reconcile).

### Reconcile.Step 1 — Template inventory

Walk `${plugin_root}/templates/project-skeleton/` (canonical EN tree; per-language variants are resolved per-file at Step 2a, not at the inventory step).

For each template file (path relative to `templates/project-skeleton/`):

- Consumer path = `<target_root>/<rel>`.
- Path-only check: status `NEW` (consumer path absent) or `EXISTING` (consumer path present).
- Do NOT read content; do NOT detect language. Content + language analysis runs at Step 2 / Step 4.

Output: an inventory list `[(rel, status, source_canonical_path), ...]`.

### Reconcile.Step 2 — Language alignment (collected then full-parallel dispatch, no batch_size cap)

Translate two sides into the user's target `content_language`:

**Step 2a — plugin template side (per template file)**:

Resolve the language variant for each template file:

1. Prefer `${plugin_root}/templates/project-skeleton.${content_language}/<rel>` when the variant directory exists AND the file is present in the variant.
2. Fallback to canonical `${plugin_root}/templates/project-skeleton/<rel>` when `content_language == "en"` OR when neither variant nor canonical is in the target language (canonical is always EN).
3. When `content_language != "en"` AND no `.${content_language}/` variant ships in the plugin AND the canonical EN file is being used as the source → schedule an **on-the-fly 4-agent translation** work item: run Semantic fidelity (Phase 1) → Glossary / Structure / Back-translation (Phase 2, parallel), all-must-pass. Output is written to `<tmp_root>/<YYYY-MM-DD>_<HHMMSS>/templates/<rel>`, where `<tmp_root>` is resolved per `skills_config.md ## Tmp directory` (default `./tmp/holo/` joined with `target_root`; `(none)` → fallback to `${TMPDIR:-/tmp}/holo-tmp-<YYYY-MM-DD>_<HHMMSS>/` with a one-line warning).

Result per template file: a `resolved-template-path` in `content_language` (canonical, variant, or tmp-translated path).

**Step 2b — consumer existing-file side (per `EXISTING` template manifest file from Step 1)**:

Restrict to the **canonical manifest**: `CLAUDE.md`, `AGENTS.md`, `ai_context/**/*.md`, `docs/todo_list.md`, `docs/architecture/**/*.md`. Do NOT scan user business docs.

For each manifest file present on disk:

- Compute CJK character ratio: `(count of 一-龥 chars) / (count of all non-whitespace chars)`.
- `> 30 %` → file judged as `zh`; `≤ 30 %` → file judged as `en`.
- Compare detected language vs `content_language`. Mismatched files → `mismatch_list`.

If `mismatch_list` is non-empty, **ask once** via `<ask tool>`:

> Detected `N` template-manifest file(s) in language `<detected>` that do not match the target `content_language=<content_language>`. Translate them in place to `<content_language>` before continuing?

Options:

- **`Yes — translate`** (recommended for clean state): proceed to in-place 4-agent translation for each mismatched file (work item).
- **`No — keep existing language`** (mixed-state acceptable): skip; mismatched files keep their original language. Mismatch alone is no longer a smart-merge trigger (see `docs/architecture/smart-merge.md` §Trigger conditions); however, individual files will still surface `sentinel_layout_drift` findings at Step 4 if their sentinel structure drifted independently.
- **`Show files`** (informational): print the file list with detected language + per-file CJK ratios, then re-ask the Yes/No question.

**Dirty-tree enforcement on Yes path**: run `git status --short`. If non-empty → fail loud and stop: "Working tree is dirty. Translation is irreversible without git history rollback. Commit or stash your changes first, then re-run `/holo:update` (or `/holo:init`)." Rationale: in-place translation is irreversible without git as the safety net. No `--force` escape.

**Bilingual CJK heuristic limitation**: en/zh binary only. Other locales (ja / ko / etc.) — when `content_language` is not `en` or `zh`, Step 2b skips silently and the No path's mixed-state acceptance applies; per-file mismatch is surfaced at Step 4 as `sentinel_layout_drift` / `missing_section` for the maintainer to reconcile manually.

**Parallelization A — full-parallel dispatch, no batch_size cap**:

Collect ALL work items from Step 2a (on-the-fly plugin template translations) AND Step 2b Yes-path (consumer in-place translations) into a single pool. Dispatch ALL items in ONE parallel batch — no `batch_size` cap; runtime / quota guards take over if concurrency saturates. Each item is a self-contained 4-agent chain (which itself parallelizes Phase 2 reviewers internally).

**Failure isolation**: single failure does not block siblings (**collect-all-results** pattern, not first-failure abort). Collect every result, then surface the failure set after the batch completes:

- 2a failures (plugin template translation aborted by 4-agent gate) → mark the corresponding `resolved-template-path` as `<canonical-EN-fallback-with-warning>`; the file flows into Step 3 / Step 4 with a `<!-- TRANSLATED BY /holo:update AT YYYY-MM-DD; please run /full-review for quality audit -->` banner header. Reason: canonical EN is the structural authority and the next `/full-review` is the right escalation path.
- 2b failures (consumer in-place translation aborted) → the consumer file is NOT touched (the 4-agent draft was in-memory only; on abort the draft is discarded). The file flows into Step 4 in its original language; sentinel-aware drift findings will surface there for the user to reconcile.

Each work item is logged in `translation_log` (whether success or failure); the log accumulates and is returned in Step 6.

**Glossary best-effort for non-en/non-zh content languages**: Agent 2 (glossary check) degrades to no-op when `translation_glossary.md` doesn't cover the target language. Documented limitation, not blocked by this round; glossary append-only update by the maintainer is the long-term path.

**Progress indicator**: emit one `[lang-translate]` line per minute (or per phase transition / file completion, whichever is shorter) to prevent the user from misinterpreting wait time as a freeze:

```
[lang-translate] processing <rel> phase 1/2: translating (Semantic fidelity) ... elapsed Mm Ss
[lang-translate] processing <rel> phase 2/2: 3 reviewers in flight (glossary / structure / back-translation) ... elapsed Mm Ss
```

### Reconcile.Step 3 — NEW file copy

For each Step 1 `NEW` file:

- Copy from Step 2a's `resolved-template-path` to `<target_root>/<rel>`.
- If the parent directory does not exist, `mkdir -p` first.
- Copied files retain `<...>` REQUIRED placeholders + PROGRESSIVE markers verbatim as in the template — REQUIRED placeholder substitution is the **caller's** post-Reconcile responsibility (`/holo:init` Step 5 fills via Round 1/2 Q&A answers; `/holo:update` does not substitute, since update mode does not collect new Q&A).

Increment `write_counts.new_copied` per file copied.

**Note**: `NEW` count is typically 0 under `mode="update"` (consumer was already initialized) — but plugin upgrades that add new template files (e.g. a future `templates/project-skeleton/docs/architecture/new-topic.md`) will surface here.

### Reconcile.Step 4 — Drift detection

Run `${plugin_root}/scripts/holo_update_check.py --target <target_root> --plugin-root <plugin_root> --json` on the post-Step-2-and-Step-3 state.

**Baseline override**: when Step 2a's `translation_log` is non-empty for this run (consumer's `content_language` had no shipped `templates/project-skeleton.<lang>/` variant, so Step 2a produced an on-the-fly tmp-translated template tree at `<tmp_root>/<YYYY-MM-DD>_<HHMMSS>/templates/`), append `--baseline-root <tmp_root>/<YYYY-MM-DD>_<HHMMSS>/templates/` to the invocation so the script's baseline-aware finding categories compare consumer files against the tmp baseline instead of the canonical EN fallback. When `translation_log` is empty (en/zh consumers — their variants ship in the plugin), omit the flag and the script falls through to its default plugin-tree resolver. Background + completeness contract: see `docs/architecture/drift-detection.md` §Baseline root override.

The script outputs the JSON structure documented as the **interface contract**:

```json
{
  "plugin_root": "...", "target_root": "...",
  "baseline_root": "<path> | null",
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
  "sentinel_layout_drift": [{"rel": "...",
                             "sub_shape": "missing_sentinel | partial_sentinel | heading_drift | block_content_drift",
                             // common: "source_path"
                             // partial_sentinel: + "level": 1|2|null, "header": "...|null", "detail": "..."
                             // heading_drift:    + "level": 1|2, "header": "..."
                             // block_content_drift: + "section": "## ... | preamble", "block_index": N,
                             //                       "plugin_excerpt": "...", "consumer_excerpt": "...",
                             //                       "diff_summary": "..."
                             }]
}
```

**Categorize each finding into one of three buckets**:

1. **Conflict-triggering** (routed to Step 5a smart-merge):
   - `sentinel_layout_drift` (any sub_shape: `missing_sentinel` / `partial_sentinel` / `heading_drift` / `block_content_drift` — smart-merge dispatch is sub_shape-agnostic per `docs/architecture/smart-merge.md`).
   - File-body language mismatch is **NOT** in this bucket — it is handled by Step 2b preprocessing. After Step 2b completes (Yes path translated, No path skipped), Step 4's drift detection runs on post-translation state; mismatched-and-skipped files surface only via `sentinel_layout_drift` if their sentinel structure also drifted.
2. **Deterministic-fixable** (routed to Step 5b `holo_update_check.py --fix`):
   - `agents_sync.stale` / `agents_sync.missing` / `agents_sync.orphan`.
   - `missing_template` (note: for markdown templates that should be NEW, Step 3 already handled them; `missing_template` findings remaining here are for non-markdown templates or markdown gaps the script's check found that Step 3 didn't — both flow through `--fix`'s template copy path).
   - `missing_section`, `missing_field`, `gitignore_missing_lines`.
   - `claude_agents_lang_drift` (always standalone — bullets live in gap territory outside the sentinel block per `ai_context/decisions.md §Language Configuration #17` Layout footer 2026-05-22; the lightweight `fix_claude_agents_lang_drift` field-level sync handles every case deterministically).
3. **Display-only by design** (routed to Step 5c — no ask, no execution):
   - `claude_agents.unexpected_diffs` (CLAUDE↔AGENTS asymmetric guidance; script never auto-merges).
   - `lang_mirror_drift` (variant template directory parity; auto-fix would either delete legitimate translations or copy English canonical content into a translated variant — both unacceptable per script docstring. The maintainer reconciles via a translation pass — Reconcile.Step 2a on-the-fly 4-agent chain or a dedicated `/full-review` round).
   - `legacy_skip_marker` (out of `--fix` scope per T-INIT-SKIP-SEMANTICS).
   - `missing_l1_directive` / `l1_directive_drift` (skill-body prose; fix via `/go` on the affected skill body).

Build `<conflict_files>` = set of file paths in bucket 1. If `len(<conflict_files>) == 0` AND bucket 2 = ∅ AND bucket 3 surfaces nothing actionable → `total_drift == 0`; Step 5 short-circuits and Step 6 returns with all counters zero.

**Important**: this step does NOT allow the skill body to re-author detection rules — no custom grep / Python comparison, no filter / exclusion additions. If a case is mis-detected, edit the script (see `ai_context/decisions.md` §Skill Implementation #5).

### Reconcile.Step 5 — 3-bucket dispatch (Step 5b runs first, then Step 5a; sequential)

> **Language**: user-facing — render the `<ask tool>` prompts, option labels, and the inline display-only finding list in `conversation_language` per the caller's L1 directive. JSON category keys (`missing_section`, `lang_mirror_drift`, `agents_sync.stale`, etc.) and file paths stay verbatim; option-label prose translates.

**Compose the batched ask** (max 4 questions per `<ask tool>` call; both questions fit):

- **Q-conflict** (only when `len(<conflict_files>) ≥ 1`) — Layer 1 aggregate ask per `docs/architecture/smart-merge.md`. One question, 5 options:
  1. Smart-merge all — dispatch the 4-sub-agent chain per `smart-merge.md` for each file in `<conflict_files>`.
  2. Overwrite all with new plugin version — `take_snapshot(target_root, slug="holo-reconcile-smart-merge", file_paths=<conflict_files>)` then overwrite each file with the resolved new plugin template content.
  3. Keep all existing files (no merge) — leave each conflict file as-is.
  4. Per-file confirmation → Layer 2 ask per file (4 options each: smart-merge / overwrite with new plugin / keep (no merge) / skip current file). When `len(<conflict_files>) > 3` the Layer 2 fan-out emits `ceil(N/4)` `<ask tool>` batches.
  5. Skip this step — skip smart-merge entirely.
- **Q-fixable** (only when bucket 2 ≠ ∅) — Auto-fix all / Skip all for the deterministic-fixable findings (display categories + counts inline). One question, 2 options.

Dispatch Q-conflict + Q-fixable in **one batched `<ask tool>` call** (current behavior preserved). Display-only findings (bucket 3) are printed inline above the ask block — no question for them.

**Execution order — Step 5b first, then Step 5a (sequential, not concurrent)**. Reason: Step 5a (smart-merge) and Step 5b (`holo_update_check.py --fix`) can both write to the same consumer file even though the disjoint-lines invariant holds — e.g. a consumer's `CLAUDE.md` may carry both a gap-territory `claude_agents_lang_drift` (deterministic-fixable bucket → 5b territory) and a sentinel-block `sentinel_layout_drift` (conflict-triggering bucket → 5a territory). Concurrent dispatch would last-writer-wins one of them. Running 5b first lets Agent 1 in 5a's smart-merge dispatch see post-5b consumer state (with gap-territory bullets already synced to skills_config canonical, mirror populated, missing sections appended), so its Covered-vs-Preserve decision is anchored on clean structural ground; 5a's writes then layer cleanly on top because Agent 1 only touches sentinel-bracketed content + extracted preserve fragments in user-territory gaps — never the gap-territory bullets 5b just fixed.

**Step 5b — deterministic `--fix`** (executes Q-fixable answer first; runs before Step 5a):

- `Auto-fix all` → invoke:
  ```bash
  python3 "${plugin_root}/scripts/holo_update_check.py" --target <target_root> --plugin-root <plugin_root> --fix --json
  ```
  **When Step 2a's `translation_log` is non-empty for this run, append `--baseline-root <tmp_root>/<YYYY-MM-DD>_<HHMMSS>/templates/` to BOTH this `--fix` invocation AND the post-fix self-check invocation below.** Same condition as Step 4 (see §Baseline override in Step 4 above). Reason: `--fix` reads `source_path` values from the check pass it runs implicitly, which must use the same baseline that Step 4 used; the post-fix `--json` self-check must do the same so its pass/fail signal compares against the same baseline. Skipping the flag on either would re-resolve `_skeleton_root` to canonical EN, producing a different finding set than Step 4 — the user would see a spurious "post-fix drift remains" anomaly.

  `--fix` implicitly runs `--check` first; outputs `fix_counts` JSON. Capture this JSON object verbatim and return it as part of Reconcile.Step 6's `fix_counts` field. Then invoke `--json` once more (without `--fix`) for a post-fix self-check:
  - `agents_sync.stale / missing / orphan` should all be 0.
  - `missing_template` should be 0.
  - `missing_section`, `missing_field`, `gitignore_missing_lines` should all be 0.
  - `claude_agents_lang_drift` should be 0 (always standalone per the 2026-05-22 Layout footer; lightweight `fix_claude_agents_lang_drift` handles every case); may remain > 0 only for structurally pre-#17 §Language sections (script skips silently when both axis bullets absent — user re-runs `/holo:init` or manually upgrades).
  - `claude_agents.unexpected_diffs` may still be > 0 (display-only by design).
  - `lang_mirror_drift` may still be > 0 (display-only by design — per-language variant content is human translation work that `--fix` deliberately does not touch).
  - `legacy_skip_marker` may still be > 0 (display-only by design).
  - `sentinel_layout_drift` (any sub_shape) may still be > 0 (resolved by Step 5a smart-merge, not by `--fix`).
- `Skip all` → no script invocation; `fix_counts` in the Step 6 return is set to an all-zero object.

**Orphan sibling cleanup**: if `fix_counts.orphan_siblings_left` is non-empty, the script removed each orphan's `SKILL.md` but kept other files under the parent directory (per the "no silent overwrite" rule). Add each entry to `remaining_drift` so Step 3's final print surfaces them to the user (`⚠️ kept sibling files under <parent>: <sibling list> (manual cleanup required)`).

Any of the post-fix items unexpectedly > 0 → record the anomaly in `remaining_drift` and stop the dispatch (indicates a script bug or permission issue).

**Step 5a — smart-merge dispatch** (executes Q-conflict answer after Step 5b completes):

- Option 1 (Smart-merge all) → for each file in `<conflict_files>`, dispatch the 4 sub-agents per `docs/architecture/smart-merge.md` "4-sub-agent dispatch". Each sub-agent prompt MUST include: paths to consumer file (post-Step-5b state — gap-territory bullets / mirror / section headers already in sync) + resolved new plugin template (from Step 2a) + snapshot file, the sentinel marker rules from `docs/architecture/section-version-sentinel.md`, the smart-merge logic from `docs/architecture/smart-merge.md` (trigger condition / three-layer ask / Layer 3 orphan-content fallback / edge cases / Covered vs Preserve), and the target `content_language`. **Place the language axes injection at the end of each sub-agent prompt** (recency-favorable, per Decision #16). Agent 1 (merger+translator) returns merged output to a staging tmp path; Agent 2/3/4 verify (Agent 4 conditional on translation happening); fix-loop = one Agent 1 retry on FAIL; second FAIL surfaces the staging output + outstanding findings with a 3-option user ask per smart-merge.md "Failure surface".
- Option 2 (Overwrite all) → `take_snapshot(target_root, slug="holo-reconcile-smart-merge", file_paths=<conflict_files>)` first, then write each file with the resolved plugin template content.
- Option 3 (Keep all) → no action.
- Option 4 (Per-file) → Layer 2 ask + execute per per-file choice (option 1 = smart-merge for this file; option 2 = overwrite for this file; options 3/4 leave the file unchanged).
- Option 5 (Skip) → no action.

For Layer 1 options 1 and 2 (and Layer 2 options 1 and 2): `take_snapshot` runs before any disk write; the snapshot directory path is surfaced in the Step 6 return value (`snapshot_dir`) for the caller's final print.

**Special case — non-target-language consumer file reaches Step 5a**: when Reconcile.Step 2b's Yes-path translated all mismatched files this case does not arise. When the user picked No on Step 2b, a consumer file in a non-target language whose sentinel structure also drifted from the plugin template DOES enter `<conflict_files>` here. Agent 1 receives the wrong-language consumer file; per `docs/architecture/smart-merge.md` §Edge cases §Covered vs Preserve translation interaction, Agent 1 translates extracted preserve fragments en route to the merged output (Agent 4 reviews each `translation_log` entry). This is **not a regression** vs the retired smart-merge trigger 2 (file-body language mismatch): the previous mechanism routed the same case through a less-rigorous file-body translation by Agent 1; the current path routes it through Agent 1's preserve-content translation, which has the same translation chain semantics scoped to the user-content fragments that actually need translation.

**Step 5c — display-only**:

No ask, no execution. Append every bucket-3 finding to `remaining_drift` with its category + per-finding detail so Step 3's final print can surface the count + list inline.

### Reconcile.Step 6 — Return

Build the structured return value:

```
{
  write_counts: {
    merged:               <Step 5a Option 1/4 success count>,
    overwritten:          <Step 5a Option 2/4 success count>,
    kept:                 <Step 5a Option 3/4/5 file count>,
    failed:               <Step 5a Option 1/4 retry-still-FAIL count>,
    new_copied:           <Step 3 count>,
    deterministic_fixed:  <Step 5b fix_counts total (sum of all categories)>
  },
  fix_counts: {                       # raw Step 5b output verbatim from `holo_update_check.py --fix --json`
    regenerated: A,                   # .agents/skills/ mirror regen
    created: B,                       # .agents/skills/ mirror new create
    deleted: C,                       # .agents/skills/ mirror orphan deletion
    template_copied: D,               # missing_template auto-fix
    section_appended: E,              # missing_section auto-fix
    field_appended: F,                # missing_field auto-fix
    gitignore_appended: G,            # gitignore_missing_lines auto-fix
    claude_agents_lang_fixed: H,      # claude_agents_lang_drift auto-fix
    orphan_siblings_left: [...]       # paths the orphan-cleanup retained
  },
  snapshot_dir: "<path or null>",     # set iff take_snapshot() fired (Step 5a Option 1 / 2 / Layer 2 1 / 2)
  remaining_drift: [...],             # bucket 3 + user-skipped bucket 1 entries + Step 5b post-fix anomalies
  translation_log: [...]              # all Step 2 work items (success + failure)
}
```

Return to caller. Reconcile core does not print anything user-facing on return (caller renders the final summary).

## Constraints

- **Single source of truth for detection / fix rules** = `scripts/holo_update_check.py`; the skill body does not re-implement.
- **Reconcile core is single source of truth for per-file landing logic** — both `/holo:update` (this command) and `/holo:init` Step 4 flow through it. To change file-update behavior, edit `## Reconcile core` above; do NOT duplicate the logic into init's user-entry shell.
- **Only touches structural drift introduced by the plugin upgrade** (missing files / missing section headers / stale mirror / orphan mirror / sentinel-aware drift); does not touch user-territory content.
- **Does not `git add` / does not commit**: consistent with `/holo:init`; the user commits via `/commit`.
- **CLAUDE/AGENTS cross-sync not auto-merged**: the script `--fix` is designed not to touch CLAUDE↔AGENTS asymmetric guidance lines (`claude_agents.unexpected_diffs`); it only reports them. Distinct from §Language hardcoded-value sync (`claude_agents_lang_drift`), which IS auto-fixable.
- To adjust detection rules → edit `scripts/holo_update_check.py`, then sync the Reconcile.Step 4 JSON contract description in this file per `ai_context/conventions.md` §Cross-File Alignment.
