---
description: Project skeleton initialization — drop the standard skeleton from the plugin's templates/project-skeleton/ (CLAUDE.md / AGENTS.md / ai_context/ / docs/todo_list.md / logs/) into the current working directory, then based on repo probing + user questioning fill `<...>` placeholders with the project's actual values. Three rounds of questioning: Round 1 (project name / description / main branch / timezone) / Round 2 (top-level directory classification) / Round 3 (project background / current status / next steps / handoff; each question may Skip → marked `_(TODO)_`, no `<...>` residue). Optional generation of `.agents/skills/` mirror. No arguments; whether the current directory is empty or already initialized, both are handled. Never silently overwrites — conflicts ask file-type-dispatched options (`.gitignore` → keep / overwrite / smart-merge with three-phase LLM-reorganize pipeline; markdown → keep / overwrite / merge mechanical append; other non-markdown → keep / overwrite). Does not touch non-template files, does not git add, does not commit. Triggers: /holo:init / initialize project / install skeleton / create an empty project.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (template files landed in the project, the filled-in placeholder values, the `skills_config.md §Language` values written by Step 1.5, any in-place translation result) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / `[lang-translate]` progress lines / planned-actions print / `Step N skipped` lines) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, ISO 639-1 codes (`zh`, `en`, etc.), and structural prefixes (`Step N:`, `NEW`, `SAME`, `CONFLICT`, `SAME-after-translate`, `CONFLICT-after-translate`) stay English regardless. **Note on the bootstrap edge case**: until Step 1.5 settles `<conversation_language>` (Steps 0, 1, 1.1-1.4 precede it), the AI follows `auto` semantics (per-turn match the user's most recent message language); from Step 1.5 onward the chosen value governs all subsequent user-facing output in this init run.

# /holo:init — project skeleton initialization

Drop the templates under `${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton/` into the current working directory, then based on repo probing + user questioning fill the `<...>` placeholders in the templates with the project's actual values. **Does not touch existing non-template files**; template conflicts always stop and ask the user, no silent overwrite.

No arguments. The repo's current state is probed automatically (empty directory / existing code / previously initialized all handled); no mode flag needed.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`. Until Step 1.5 settles `<conversation_language>` (Steps 0 + 1 + 1.1-1.4), follow `auto` semantics — match the user's most recent message language for entries written then.

The flow below is split into `## Step 0:` ~ `## Step 5:`.

**Before entering Step 0**: call **<progress tool>** to pre-register Step 0 ~ Step 5 (one entry per step, `content` as `Step N: <sub-section title>`, all `status` = `pending`). This is a hard requirement — **do not proceed without calling <progress tool>**.

On entering each step: flip the current step to `in_progress` and mark the previous one `completed`, then do the actual work. Skipping a step: mark it `completed` directly and print one line in the conversation `Step N skipped (reason: …)`.

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block before each state change. Semantic alignment: pre-register + flip state + mark complete.

## Step 0: Load skills config

`Read` `ai_context/skills_config.md`.

- File missing / any section header missing → fail loudly: print the missing items + prompt to complete per plugin template, stop
- Section content `(none)` or empty → skip the related steps for that section (treat as N/A in this project)
- Section lists concrete paths but the path does not exist → fail loudly: report the section drifting to a nonexistent path, stop and wait for the user to fix

Subsequent steps referencing "skills_config.md `## XX`" use this config. This command uses:
`## Timezone` (filename timestamps for `_(TODO …)_` markers if Step 4 writes them),
`## Language` (Step 1.5 reads it to seed the bootstrap defaults; Step 4.2 writes back the user's chosen values).

## Step 1: Probe repo state

Purpose: before touching any file, paint a clear picture of "what the target directory looks like" so subsequent steps have an accurate basis.

**1.1 Working directory basic state**

- `pwd` to confirm the absolute path of the current working directory
- `ls -la` to view the top-level file / directory listing
- `test -d .git && git status --short` to check whether it is a git repo + working-tree state. dirty → print a warning (do not stop, because `/holo:init` does not commit; but advise the user to stash / commit existing changes first to keep the git history cleaner)

**1.2 Template inventory + conflict pre-scan**

- Template source directory: `${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton/` (if `${CLAUDE_PLUGIN_ROOT}` is unset, derive from this command's path back to the plugin root + `templates/project-skeleton/`)
- `find "${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton" -type f` to list all template files (including `.gitkeep`)
- For each template file, relative path mapped to the target directory:
  - Target does not exist → status `NEW`
  - Target exists and content is **identical** to the template (`diff -q`) → status `SAME`
  - Target exists but content differs → status `CONFLICT`
- Output a table (grouped by status): each row `status | relative path | byte size comparison`

**1.3 Repo content probing** (pre-fills values for Step 4 questioning)

- Project name candidates (take the first non-empty in priority order):
  1. `name` field in `package.json`
  2. `[project] name` or `[tool.poetry] name` in `pyproject.toml`
  3. `[package] name` in `Cargo.toml`
  4. last segment of module path in `go.mod`
  5. repo root directory name
- One-line description candidates: `description` field of the above manifests; if none → take the first sentence of the existing `README.md` opening paragraph
- Git remote URL: `git remote get-url origin 2>/dev/null`
- Main branch: `git symbolic-ref --short HEAD 2>/dev/null` + `git branch --list main master` (default `main`)
- Top-level directory inventory (excluding obvious noise like `.git/` / `node_modules/` / `__pycache__/` / `.venv/`): as candidates for the Top-Level Structure of `architecture.md` + the Source / Data contract / Example artifact candidates of `skills_config.md`
- Timezone: local `date +%Z` as the default for `skills_config.md` §Timezone

**1.4 Ask whether to generate `.agents/skills/` mirror**

Use **<ask tool>** to ask one question:

> Generate `.agents/skills/` mirror? (Converts all plugin commands/ + skills/ into `.agents/skills/<name>/SKILL.md`. Purpose: let Codex / other non-Claude runtimes also recognize this set of commands / skills for cross-validation — they do not recognize slash commands, only SKILL.md. Pick No if not needed — if this repo invokes the plugin only via Claude / Claude Code, a local duplicate is redundant.)

Options:

- `No` (recommended default): skip `.agents/` generation
- `Yes`: Step 3.2 dual-source mirror generation (commands/ converted with `name:` field injected; skills/ copied as-is), Step 5.4 adds mirror verification

Record the user's choice (referenced below as `<.agents-opt>`).

**1.5 Ask language axes (2 questions)**

> **Language**: user-facing — render both language questions and their option descriptions in `conversation_language` per `ai_context/skills_config.md §Language`. Bootstrap edge case: until question 2 settles `<conversation_language>`, follow `auto` semantics — match the user's most recent message language for the questions themselves; from this point on, the chosen value governs all subsequent user-facing output. ISO 639-1 codes (`en`, `zh`, etc.) and the `auto` keyword stay English in option text.

Use **<ask tool>** to ask 2 questions covering the project-level language config (later written into `ai_context/skills_config.md §Language`):

1. **Project content language?** — the language of every written artifact the AI produces or maintains in this project: `ai_context/` / `docs/` / `logs/` / commits / README / skill output / new code comments. Accepts any ISO 639-1 code. Default suggestion: `en` (or the conversation language if that is a single ISO 639-1 code).
2. **AI conversation language?** — the language of AI ↔ user turns (`AskUserQuestion` / replies / confirmations). Accepts `auto | <ISO 639-1>`. `auto` follows the user's current-message language per turn. Any explicit value is a hard rule with a single-message escape hatch ("respond in `<other>`"). Default suggestion: `auto`.

Record the user's choices as `<content_language>` and `<conversation_language>` — referenced below by Step 2 (existing-directory translation detection), Step 3.1 (template variant lookup), and Step 4 (write into `skills_config.md §Language` replacing the template defaults).

ISO 639-1 lock: `zh`, not `cn` (country code). Locale variants (`zh-CN`, `zh-TW`) reserved for future regional split — current phase rejects them.

**1.6 Print plan**

Aggregate the above into a "planned actions" print:

```
Template files: NEW=X | SAME=Y | CONFLICT=Z
Conflict files (user decision required): <list>
.agents/skills/ mirror: <yes / no>
Language config:
  - content_language:      <value>
  - conversation_language: <value>
Probed pre-fill values:
  - Project name candidate: <value>
  - One-line description:   <value>
  - Main branch:            <value>
  - Timezone:               <value>
  - Top-level directories:  <list>
```

If the pre-scan shows the project is already initialized (`NEW` count is small and most template files land as `SAME` / `CONFLICT`), print one extra hint line **before** the conflict-handling regime kicks in:

```
Hint: this project is already initialized. If you only want non-destructive
structural sync after a plugin upgrade (add missing template files / section
headers / skills_config fields with `_(TODO)_` stubs, regenerate
.agents/skills/ mirror), `/holo:update` is the lighter tool — it bypasses
the placeholder Q&A and skips the conflict prompts. Continue with /holo:init
only if you intend to re-walk the bootstrap questions.
```

This is informational only — Step 1.6 still proceeds with the user's chosen `/holo:init` invocation. The hint surfaces the existence of `/holo:update` for users who launched `/holo:init` reflexively without realizing the upgrade path exists.

## Step 2: Existing-directory language detection (conditional)

> **Language**: disk-bound — write any translated template files (in-place rewrites of existing on-disk files) in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names, structural prefixes (`SAME`, `CONFLICT`, `SAME-after-translate`, `CONFLICT-after-translate`) stay English.

> **Language**: user-facing — render the single Yes / No translation question, the dirty-tree fail-loud line, the `[lang-translate]` progress lines, the post-translation summary, and the No-path warning block in `conversation_language` per `ai_context/skills_config.md §Language`. File paths quoted in messages stay verbatim; only surrounding prose translates.

> **Language (sub-agent dispatch)**: the 2.5 two-phase four-agent review chain dispatches sub-agents in both phases (Phase 1: Semantic fidelity; Phase 2: glossary / structure / back-translation in parallel). The parent MUST inject the language axes into each sub-agent's prompt explicitly. Include verbatim: "Reply in `conversation_language`=`<value>`; write any disk artifacts in `content_language`=`<value>`; both values from `ai_context/skills_config.md §Language`." Sub-agents do not inherit the parent's language config — they must be told. Sub-agent report-back (review verdicts) to the parent is a USER surface; the translated file landed on disk is DISK surface.

**Runs only if Step 1.2 detected ≥ 1 `SAME` or `CONFLICT` file** (an "existing directory" — files already on disk that look like template-manifest content). If 1.2 returned all `NEW` (empty-directory init), skip this entire sub-step and proceed to Step 3.1.

Purpose: catch the case where the directory already has template-manifest files in a language different from the user's chosen `<content_language>`, and translate them in place before Step 3.1's keep/overwrite/merge regime runs (so the merge runs against the user's chosen language).

**2.1 CJK-ratio heuristic per existing file**

For each template-manifest file present on disk (the `SAME` and `CONFLICT` entries from Step 1.2 — restrict to the canonical manifest: `CLAUDE.md`, `AGENTS.md`, `ai_context/**/*.md`, `docs/todo_list.md`, `docs/architecture/**/*.md` — do NOT scan the user's business docs):

- Compute CJK character ratio: (count of `一`-`龥` chars) / (count of all non-whitespace chars).
- > 30 % → file judged as `zh`.
- ≤ 30 % → file judged as `en`.

Limitations: en/zh binary only. Other locales (ja / ko / etc.) require LLM-based detection or an explicit user question — out of scope for the current phase; if `<content_language>` is not `en` or `zh`, **skip Step 2** entirely and proceed to Step 3.1. Step 3.1 branch (c) runs the on-the-fly 4-agent translation chain (landed Phase 6) on the canonical EN template source; existing-directory files in any non-en/non-zh language remain unchanged in this init run and surface later as `lang_mirror_drift` / `missing_section` findings from `/holo:update` for the maintainer to reconcile manually or via `/full-review`.

**2.2 Compute mismatch set**

Compare each scanned file's detected language vs `<content_language>`:

- Match → no action.
- Mismatch → add to the `<mismatched-files>` set.

If `<mismatched-files>` is empty → print `No language mismatch detected; proceeding to Step 3.1.` and skip the rest of Step 2.

**2.3 Single aggregate prompt (one question)**

Use **<ask tool>** to ask one question (placed BEFORE Step 3.1's per-CONFLICT keep/overwrite/merge regime — translation is preprocessing):

> Detected `N` template-manifest file(s) in language `<detected>` that do not match the chosen `content_language=<content_language>`. Translate them in place to `<content_language>` before continuing?

Options:

- **`Yes — translate`** (recommended for clean state): enforce dirty-tree check (1.0.4), then run the four-agent review chain (1.0.5).
- **`No — keep existing language`** (mixed-state acceptable): skip translation; print warning (1.0.6) and proceed to Step 3.1.
- **`Show files`** (informational): print the file list with their detected language + per-file CJK ratios, then re-ask the Yes/No question.

**2.4 Dirty-tree enforcement (Yes path only)**

Run `git status --short`. If non-empty → **fail loud and stop**: print `Working tree is dirty. Translation is irreversible without git history rollback. Commit or stash your changes first, then re-run /holo:init.` Do NOT proceed.

Rationale: in-place translation is irreversible without git as the safety net. The dirty check is non-negotiable; no `--force` flag.

**2.5 Four-agent two-phase review chain (Yes path only)**

For each file in `<mismatched-files>`, run the four-agent review chain in **two phases**:

**Phase 1 — translate (sequential, blocks Phase 2)**:

1. **Semantic fidelity agent** — translate the file; compare each paragraph against the original to verify no meaning is dropped. Output is the translation draft consumed by Phase 2; held in-memory, never written to disk until the full chain passes.

**Phase 2 — review Phase 1's output (3 agents in parallel)**:

2. **Glossary consistency agent** — verify every translated term against `${CLAUDE_PLUGIN_ROOT}/scripts/translation_glossary.md` (Phase 4 canonical glossary); flag any term that conflicts with the canonical mapping.
3. **Structure preservation agent** — verify markdown structure (heading levels, list indentation, code-fence count, frontmatter, tables, blockquotes) is byte-for-byte equivalent in shape.
4. **Back-translation agent** — translate the Phase 1 draft back to the original language and diff against the source; flag any drift in meaning.

The parent dispatches agents 2/3/4 concurrently (single sub-agent batch) and waits for **all three** verdicts before deciding. **All-must-pass gate**: the file's translation is accepted only when all four agents complete without blocking findings. Runtimes without parallel sub-agent dispatch fall back to sequential 1 → 2 → 3 → 4 (functionally equivalent, just slower). **Sequential fallback implementations must still run all four agents and collect every verdict before deciding abort (not first-failure early exit), so the "all reasons surfaced" guarantee is runtime-independent.**

If any agent reports a blocking finding (Phase 1 semantic loss, or any Phase 2 reviewer's glossary conflict / structure drift / back-translation drift) → **abort init for the current file**. When more than one Phase 2 reviewer reports blocking findings, all are surfaced in the per-file fail block (parent collects every Phase 2 verdict before deciding abort, so the user sees the full set of issues rather than just the first failure).

**Mid-loop abort cleanup policy** (executable invariants — this skill body owns the spec):

- The current file's Phase 1 draft lives **in memory only** — the on-disk file is never written until all four agents pass. On abort the draft is discarded; the dirty-tree enforcement at 2.4 guarantees the working tree is in a known-good state for that file.
- Sibling files in the same `<mismatched-files>` batch that **already finished the full four-agent chain successfully BEFORE this abort point** are kept on disk — they passed review and form valid committed state under the user's pending commit.
- Init halts with a per-file fail block listing each aborted file's path, the failing agent (semantic / glossary / structure / back-translation), and the agent's reason string. When Phase 2 reviewers run in parallel and more than one reports a blocking finding, all are listed (parent collects every Phase 2 verdict before deciding abort, so the user sees the full set of issues rather than just the first failure). The 2.8 wrap-up summary uses this on-disk state to print translated-vs-aborted file counts and paths explicitly so the user knows the exact state without re-running detection.
- Recovery: the user can either fix the source then re-run `/holo:init` (which re-detects mismatch and resumes — already-translated files now match `<content_language>` and won't re-enter the chain), or pick the "No — keep existing language" option on re-run to accept the mixed state.

**Post-translation `SAME` / `CONFLICT` reclassification**. After a file finishes the chain successfully, byte-compare it against the corresponding template-manifest entry (the same baseline used to classify it as `SAME` / `CONFLICT` at the pre-scan stage):

- `byte-equal` after translation → reclassify as `SAME-after-translate`; the keep / overwrite / merge prompt is skipped for this file (translated content already matches the template, no further user choice needed).
- `byte-diff` after translation → tag as `CONFLICT-after-translate`; the keep / overwrite / merge prompt fires using this label so the user sees that the diff arose post-translation rather than from the pre-translation source state.

This reclassification ensures the user isn't asked redundant keep / overwrite questions when translation alone resolved the diff.

**No `--skip-review` escape hatch.** The four-agent review chain is non-optional; there is no flag that lets the user bypass any of the four agents. Safety priority — the chain exists because in-place translation is irreversible without git history rollback, and the all-must-pass gate is the only programmatic protection against silent meaning loss / structural drift / glossary inconsistency.

**2.6 Progress indicator (Yes path only)**

The two-phase chain still takes minutes per manifest. Print one line per minute (or per phase transition / file completion, whichever is shorter), labelling the current phase:

```
[lang-translate] processing <rel> phase 1/2: translating (Semantic fidelity) ... elapsed Mm Ss
[lang-translate] processing <rel> phase 2/2: 3 reviewers in flight (glossary / structure / back-translation) ... elapsed Mm Ss
```

This prevents the user from misinterpreting wait time as a freeze. Sequential-fallback runtimes (no parallel sub-agent dispatch) keep the phase 2 line but emit it once per reviewer instead of once per phase entry.

**2.7 No-path warning (No path only)**

Print:

```
⚠️ Mixed-language state: existing template-manifest files in <detected> will remain untranslated.
   content_language = <content_language>; you can re-run /holo:update later to retry translation
   detection (it will surface `lang_mirror_drift` and `missing_section` findings as applicable).
```

Proceed to Step 3.1.

**2.8 Wrap-up**

Print summary:

```
Existing-dir translation: <translated N | skipped — no mismatch | skipped — user declined | aborted at agent X>
```

## Step 3: Copy templates (including conflict handling)

> **Language**: disk-bound — write the template files copied into the project (canonical EN copy, pre-generated variant copy, or on-the-fly translation output per branch (a) / (b) / (c)) in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names, `<placeholder>` literal markers, and structural prefixes (`NEW`, `OVERWRITE`, `CONFLICT`) stay English.

> **Language**: user-facing — render the per-`CONFLICT` keep / overwrite / merge `<ask tool>` prompt and option labels, the `Source:` line, the `Using pre-generated variant:` line, and the aborted-file aggregate retry / fallback / abort question in `conversation_language` per `ai_context/skills_config.md §Language`. File paths and ISO 639-1 codes in the prompts stay verbatim; only surrounding prose translates.

> **Language (sub-agent dispatch)**: branch (c)'s on-the-fly two-phase four-agent translation chain dispatches sub-agents in both phases (Phase 1: Semantic fidelity; Phase 2: glossary / structure / back-translation in parallel). The parent MUST inject the language axes into each sub-agent's prompt explicitly. Include verbatim: "Reply in `conversation_language`=`<value>`; write any disk artifacts in `content_language`=`<value>`; both values from `ai_context/skills_config.md §Language`." Sub-agents do not inherit the parent's language config — they must be told. The translated `.md` content the sub-agents write is DISK surface; their per-file review verdicts returned to the parent are USER surface.

Purpose: land template files in the target directory.

**3.1 Template file copy**

**Source selection — three branches by `<content_language>`**. Before copying, decide the source root:

**Branch (a) — `<content_language> = en` (canonical)**: use the canonical `${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton/` directly. No translation needed. Print `Source: canonical templates/project-skeleton/ (content_language = en)`.

**Branch (b) — variant hit**: when `${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton.<content_language>/` exists (e.g. `templates/project-skeleton.zh/` when `<content_language>=zh`; Phase 6 of T-LANG-CONFIG-SYSTEM lands the `.zh/` variant; future locales added on demand by maintainer). Use that directory as the source root. Pre-generated variants are content-aligned with the consumer's chosen language, deterministic, and require no runtime translation. Print `Using pre-generated variant: project-skeleton.<content_language>/`.

**Branch (c) — non-en, no pre-generated variant**: invoke the **on-the-fly four-agent translation chain** at init time. This is the path for any ISO 639-1 `<content_language>` that does not yet have a `templates/project-skeleton.<lang>/` variant in plugin source.

Chain semantics (mirrors Step 2.5's two-phase chain, but operates on the canonical EN template source rather than existing user files):

1. For each `.md` file under `templates/project-skeleton/` slated to land in this run (`NEW` (file absent on disk) or `OVERWRITE` (file present, user opted in via Step 1.2 keep/overwrite/merge prompt) per Step 1.2's classification — `SAME` / `keep` files are unchanged; `merge` is handled by Step 3.1 default behavior post-translation), run the two-phase four-agent chain:

   **Phase 1 — translate (sequential, blocks Phase 2)**:
   - **Semantic fidelity agent**: translate the file English → `<content_language>`; verify each paragraph against the source for no meaning loss. Output is the translation draft consumed by Phase 2; held in-memory, never written to disk until the full chain passes.

   **Phase 2 — review Phase 1's output (3 agents in parallel)**:
   - **Glossary consistency agent**: verify every translated term against `${CLAUDE_PLUGIN_ROOT}/scripts/translation_glossary.md` (Phase 4 canonical glossary); flag any term that conflicts with the canonical mapping.
   - **Structure preservation agent**: verify markdown structure (heading levels, list indentation, code-fence count, frontmatter, tables, blockquotes, `<placeholder>` literal markers preserved) is byte-equivalent in shape.
   - **Back-translation agent**: translate the Phase 1 draft back to English; diff against the source for semantic drift.

   The parent dispatches the three Phase 2 agents concurrently (single sub-agent batch) and waits for **all three** verdicts before deciding. **All-must-pass gate**: the file is accepted only when all four agents complete without blocking findings. Runtimes without parallel sub-agent dispatch fall back to sequential 1 → 2 → 3 → 4 (functionally equivalent, just slower). **Sequential fallback implementations must still run all four agents and collect every verdict before deciding abort (not first-failure early exit), so the "all reasons surfaced" guarantee is runtime-independent.**
2. If any agent reports a blocking finding for a given file → that file's translation is aborted. When more than one Phase 2 reviewer reports blocking findings, all are surfaced in the per-file fail block (parent collects every Phase 2 verdict before deciding abort). The init flow then asks the user (single aggregate question covering all aborted files): retry the chain / fall back to copying the canonical English file with a `<!-- TRANSLATED BY /holo:init AT YYYY-MM-DD; please run /full-review for quality audit -->` marker prepended (passive fallback retained as the safety net) / abort the entire init.
3. On success, write the translated content to the target directory; the standard Step 3.1 keep / overwrite / merge regime then runs against the translated files (same as branch (b)).
4. Print periodic progress lines (cadence: every minute or every phase transition / file completion, whichever is shorter):

   ```
   [lang-translate] processing <rel> phase 1/2: translating (Semantic fidelity) ... elapsed Mm Ss
   [lang-translate] processing <rel> phase 2/2: 3 reviewers in flight (glossary / structure / back-translation) ... elapsed Mm Ss
   ```

   This prevents the user from misinterpreting wait time as a freeze. Sequential-fallback runtimes keep the phase 2 line but emit it once per reviewer.
5. No `--skip-review` escape hatch — safety priority, matching Step 2.

Glossary reference: `${CLAUDE_PLUGIN_ROOT}/scripts/translation_glossary.md` is the canonical zh↔en mapping; for non-zh `<content_language>` the glossary is a structural reference (term mappings, naming conventions, NOT-to-translate literals) — the translation agents extend it per their judgement and report newly coined terms in the post-run summary (these are picked up by the maintainer for glossary append-only update per the glossary's maintenance contract).

(Phases 5 + 6 of T-LANG-CONFIG-SYSTEM together cover this Source selection block. Phase 5 implemented branches (a) + (b) + the passive-marker variant of (c). Phase 6 lands the first variant in branch (b) — `templates/project-skeleton.zh/` — AND upgrades branch (c) from passive marker to the on-the-fly 4-agent chain described above.)

**Per-file status handling** — decide per the status from Step 1.2 for each file:

**`NEW`**: copy directly from the source root chosen above. If the parent directory does not exist, `mkdir -p` first.

**`SAME`**: no-op, skip. Print one line in the conversation `Skipped (already identical): <path>`.

**`CONFLICT`**: **ask the user about all of them at once** — do not ask file by file.

Use **<ask tool>** to present a diff summary for each conflict file (`diff -u` first 10 lines + last 10 lines, truncated with `... (N more lines)` if too long), and let the user pick for each file. **Available options dispatch by file type**:

| File type | Options |
|---|---|
| `.gitignore` (line-set semantics) | `keep` / `overwrite` / `smart-merge` (recommended) |
| Markdown files (`*.md`) | `keep` / `overwrite` / `merge` (mechanical append) |
| Other non-markdown files | `keep` / `overwrite` (no merge available) |

Option semantics:

- `keep`: keep current state, skip this template.
- `overwrite`: overwrite with the template.
- `merge` (markdown only): append the template content to the end of the existing file with separator `\n\n<!-- ↓ plugin-skeleton template content ↓ -->\n\n`. **Mechanical concatenation** — does not deduplicate sections, does not reconcile user's section structure; the user is responsible for cleaning up afterward.
- `smart-merge` (`.gitignore` only): three-phase pipeline. See `ai_context/decisions.md` §Skill Implementation #14 for full rationale.

  1. **Phase 1 — deterministic union** (Python). Read both files, then call `gitignore_compute_union(template_content, target_content)` exported by `scripts/holo_update_check.py`. The return value is `(merged_content, added_patterns)`: `added_patterns` is the list of patterns present in the template but not in the target (canonical form, deduplicated, template order); `merged_content` is the deterministic fallback (target verbatim + banner sentinel + the added patterns at the tail). Compute the **expected pattern set** via `gitignore_pattern_lines(merged_content)` — this is the load-bearing invariant Phase 3 will gate against.
  2. **Phase 2 — LLM reorganize**. Invoke the LLM with the union pattern set and a prompt that pins:
     - Output every input pattern exactly, byte-for-byte (no rewrite, no normalisation, no dedup).
     - Add no new patterns.
     - Use only the seven section headers exposed as `_GITIGNORE_SECTION_WHITELIST` in the script: `# Editor / IDE`, `# Python`, `# Node`, `# OS`, `# Local config`, `# Build outputs / caches`, `# Project-specific`. Omit any section that has no patterns; do not invent new section headers.
     - Group related patterns under their idiomatic section.

     This step is **non-load-bearing**: its output is purely aesthetic. If the LLM call fails entirely, treat it as a Phase 3 failure and proceed to the fallback.
  3. **Phase 3 — set-equality gate** (Python). Call `gitignore_verify_reorganize(llm_output, expected_patterns, _GITIGNORE_SECTION_WHITELIST)`. It enforces two invariants:
     - Pattern set equality (no missing, no extra, no rewritten).
     - Every `#`-prefix comment line in the LLM output is in the whitelist (the banner sentinel is implicitly allowed).

     On `passed=True` → write the LLM output to the target `.gitignore`. On `passed=False` → write the Phase 1 `merged_content` to the target instead, and print a warning citing the gate's `violations` list verbatim:
     ```
     ⚠️ LLM reorganize gate failed for .gitignore: <violations>; wrote deterministic union (raw template additions appended at file tail with banner) instead.
     ```
     Correctness is guaranteed by Phase 1 alone — the LLM is a tidy-up step, not a merge step.

**<ask tool> resolution**: Claude → `AskUserQuestion` (max 4 questions per call, batch beyond); other runtimes (no structured ask tool, e.g. Codex / Copilot agent mode) → enumerate questions + options per question in the response text and let the user answer in one pass (still max 4 per batch, batch beyond).

After the user answers, execute decisions per file.

**3.1 wrap-up**: re-run the status scan from Step 1.2 to confirm all template files are `SAME` (except those the user chose `keep`); any residual `CONFLICT` → error and stop (indicates the user's choice did not take effect).

Print result: `Created: A | Skipped (identical): B | Skipped (kept existing): C | Overwritten: D | Merged: E | Smart-merged: F | Smart-merge fallbacks: G`.

`Smart-merged` counts `.gitignore` files where the LLM output cleared the Phase 3 gate; `Smart-merge fallbacks` counts those that wrote the Phase 1 deterministic union after gate failure (≥ 1 means the user should eyeball the resulting `.gitignore` — content is correct, organization is the raw banner form).

**3.2 `.agents/skills/` mirror generation (dual source)**

Only executed when Step 1.4 the user picked `Yes`; skip this sub-step on `No`.

The sources for `.agents/skills/` come from **two directories**, but path handling differs:

| Source | Path | Conversion |
|---|---|---|
| commands | `${CLAUDE_PLUGIN_ROOT}/commands/<name>.md` | Command files have no `name:` field in frontmatter (Claude derives it from the filename), but SKILL.md requires it — inject `name: <name>` on the first line of frontmatter during conversion; keep other content as-is |
| skills | `${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md` | Already in SKILL.md format; **byte-for-byte** copy |

`${CLAUDE_PLUGIN_ROOT}` fallback: same as Step 1.2 (derive from this command's path back to the plugin root).

**Enumeration is not hardcoded** — `commands/*.md` and `skills/*/SKILL.md` are all included; newly added commands/skills follow automatically.

Conflict handling (target exists but content differs): same `keep` / `overwrite` question as Step 3.1; `merge` is not supported (frontmatter merge is error-prone).

**Expected content computation = single source of truth**: use the pure function `expected_mirror_content(source_path, name, source_type)` exported by `scripts/holo_update_check.py`. This step **does not re-implement the frontmatter injection logic**; to change the format rule, edit the script. See `ai_context/decisions.md` §Skill Implementation #5.

Reference implementation:

```bash
python3 <<'PYEOF'
import os, sys, glob

PR = os.environ.get('CLAUDE_PLUGIN_ROOT')  # fallback: derive from command path if unset
sys.path.insert(0, f'{PR}/scripts')
from holo_update_check import expected_mirror_content

target = '.agents/skills'
os.makedirs(target, exist_ok=True)
copied = same = conflict = 0

def install(name, content):
    global copied, same, conflict
    dst = f'{target}/{name}/SKILL.md'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        if open(dst).read() == content:
            same += 1; return
        # conflict — Step 3.1 same flow asks user keep/overwrite
        conflict += 1; return
    with open(dst, 'w') as f:
        f.write(content)
    copied += 1

for cmd in sorted(glob.glob(f'{PR}/commands/*.md')):
    name = os.path.splitext(os.path.basename(cmd))[0]
    install(name, expected_mirror_content(cmd, name, 'command'))

for sk in sorted(glob.glob(f'{PR}/skills/*/SKILL.md')):
    name = os.path.basename(os.path.dirname(sk))
    install(name, expected_mirror_content(sk, name, 'skill'))

print(f'.agents/skills/: Copied {copied} | Identical {same} | Conflicts {conflict}')
PYEOF
```

Print: `.agents/skills/: Copied N | Identical M | Kept existing K | Overwritten W` (commands + skills aggregate).

## Step 4: Probe + ask + fill

> **Language**: disk-bound — write the filled values into the landed template files in `content_language` per `ai_context/skills_config.md §Language`. The `_(TODO)_` Skip-marker and `<placeholder>` literal markers stay English regardless. Code identifiers, file paths, field names, and ISO 639-1 codes stay English.

> **Language**: user-facing — render the Round 1 / Round 2 / Round 3 `<ask tool>` question batches, their option labels, and the Skip-acknowledgement lines in `conversation_language` per `ai_context/skills_config.md §Language`. Default-value suggestions probed in Step 1.3 (project name candidates, main branch defaults, timezone strings like `UTC` / `Asia/Shanghai`) stay verbatim.

Purpose: replace `<...>` placeholders in the templates with the project's actual values.

**4.1 grep out pending placeholders**

```bash
python3 <<'PYEOF'
import re, os, glob
files = ['CLAUDE.md', 'AGENTS.md', 'README.md']
for d in ('ai_context', 'docs'):
    if os.path.isdir(d):
        files += sorted(glob.glob(f'{d}/**/*.md', recursive=True))
for f in files:
    if not os.path.isfile(f): continue
    in_fence = False
    in_comment = False
    for i, raw in enumerate(open(f), 1):
        line = raw.rstrip('\n')
        if line.lstrip().startswith('```'):
            in_fence = not in_fence; continue
        if in_fence: continue
        if line.lstrip().startswith('|'): continue       # markdown table row
        if '<!--' in line: in_comment = True
        if in_comment:
            if '-->' in line: in_comment = False
            continue
        cleaned = re.sub(r'`[^`]*`', '', line)           # strip inline code spans
        if re.search(r'<[^>]+>', cleaned):
            print(f'{f}:{i}:{line}')
PYEOF
```

> **Note**: Python rather than `awk` — because the Claude Code slash-command rendering layer treats `$0` / `$1` etc. as argument placeholders and strips them, so `$0` (current line) in an awk script becomes empty. Python does not have this gotcha.

Each remaining `<...>` is a real pending placeholder — excluding: (a) format examples inside code fences, (b) markdown table row examples, (c) HTML comments (MAINTENANCE section), (d) doc-reference patterns using `<name>` inside inline code spans. Print grouped by file once.

**4.2 Required questions (Round 1)**

Use **<ask tool>** to ask 4 questions at once (values probed in Step 1.3 act as `Recommended` options; the user can pick `Other` to fill in their own):

1. Project name (for `<project-name>` in CLAUDE.md / AGENTS.md / README.md)
2. One-line project description (for `<one-line project description>` in README.md)
3. Main branch name (for `ai_context/skills_config.md` §Main branch policy; default `main`)
4. Timezone command template (for `ai_context/skills_config.md` §Timezone; default `TZ='UTC' date '+%Y-%m-%d_%H%M%S'`)

After receiving answers, **immediately** use `Edit` to write into the corresponding file (do not batch then write — interruptions still preserve progress).

**Additionally — language config write-back from Step 1.5**: at this same point, use `Edit` to write the `<content_language>` and `<conversation_language>` values chosen in Step 1.5 into `ai_context/skills_config.md §Language`, replacing the template defaults (`content_language: en` / `conversation_language: auto`) with the user's chosen values. If the user's choices match the template defaults, this is a no-op (still verify the lines exist and have the chosen values). This makes Step 1.5's answers persistent in the landed project.

**4.3 Top-level directory classification questions (Round 2)**

If Step 1.3 detected top-level directories beyond `.git/` / `ai_context/` / `docs/` / `logs/`, use **<ask tool>** to ask at most 4 questions, one probed directory per question, let the user classify:

- `source` → written into `skills_config.md` §Source directories
- `data-contract` → written into `skills_config.md` §Data contract directories
- `example-artifact` → written into `skills_config.md` §Example artifact directories
- `do-not-commit` → written into `skills_config.md` §Do-not-commit paths
- `skip` → not written into any section

More than 4 directories → batch. No such directories (empty-directory init scenario) → skip Round 2 entirely.

**4.4 Inferred fills (no questioning, write directly)**

The following values can be derived directly from Step 1.3 without further questioning:

- Top-Level Structure of `architecture.md`: expand the top-level directory inventory from Step 1.3 into `- \`<dir>/\` — <inferred description / leave blank for user to fill>` form (leave `<...>` for inferred description so the user can supplement)
- Default Priority of `read_scope.md`: auto-include existing `docs/` / top-level README.md (if any)

**4.5 Content fill questions (Round 3, each question can be Skipped)**

Purpose: clear the `<...>` placeholders in `ai_context/` body content files in one pass — either fill in real content, or explicitly mark TODO; **never let `<...>` placeholders linger**.

Use **<ask tool>** to ask 4 questions at once (each at most a paragraph answer; each question carries a Skip option):

1. `project_background.md` — "project goal / guiding principles / build order: describe in a few sentences or bullets"
2. `current_status.md` — "current stage / what exists / what is missing / what rules are in use: a paragraph or bulleted description"
3. `next_steps.md` — "high / medium / long-term next steps: list a few items per priority (high-only is fine)"
4. `handoff.md` — "2-4 sentences mental model + a few user preferences ('what the user cares about')"

Options per question:

- **Fill content** (user types freely, AskUserQuestion's `Other` / free text in other runtimes)
- **`Skip — fill later`**: skip this file; all `<...>` placeholders replaced with `_(TODO — skipped at /holo:init; fill via later /go or directly edit)_`

After receiving answers, **immediately** use `Edit` to write to disk (interruptions still preserve progress):

- **Filled**: try to split the user's answer along the file's section order into matching sections; when precise splitting is not possible, drop the whole paragraph into the most important section (the first one), and replace `<...>` in other sections with `_(TODO — see §<first section name>; or supplement later)_`
- **Skip**: all `<...>` in that file → `_(TODO — skipped at /holo:init; fill via later /go or directly edit)_`

**4.6 decisions.md auto wrap-up**

`decisions.md` defaults to one placeholder line `<Start writing decisions here as they happen.>` — this is not a question field (decisions happen incrementally). Use `Edit` directly to replace it with:

```
_(no decisions logged yet — append entries per §Format above as they land)_
```

Do not ask the user. Other structure / `## Format` code block examples are filtered by the Step 4.1 grep and will not appear in the placeholder list.

## Step 5: Wrap-up verification

> **Language**: user-facing — render the wrap-up status report printed to the user (template-files landed, mirror status, language-config summary, next-steps suggestion) in `conversation_language` per `ai_context/skills_config.md §Language`. File paths and ISO 639-1 codes quoted in the report stay verbatim; only surrounding prose translates.

**5.1 Placeholder / TODO residue scan**

Two-category scan:

(a) Re-run the Step 4.1 grep; list any remaining `<...>` as a list — **normally should be 0** (because Step 4.5 either fills or Skip→`_(TODO)_`, no `<...>` stays). If > 0 → warn explaining which files Step 4.5 missed.

(b) `grep -rn '_(TODO' CLAUDE.md AGENTS.md ai_context/ docs/ 2>/dev/null` to list all TODOs the user actively Skipped:

```
User chose Skip in Step 4.5 (K items; fill via later /go or directly edit):
  ai_context/project_background.md:22  _(TODO — skipped at /holo:init; …)_
  ai_context/next_steps.md:31          _(TODO — skipped at /holo:init; …)_
  ...
```

**5.2 skills_config.md self-check**

`Read` `ai_context/skills_config.md` and check whether all 12 section headers below exist:

```
## Background processes
## Protected branch prefixes
## Main branch policy
## Do-not-commit paths
## Source directories
## Data contract directories
## Example artifact directories
## Core component keywords
## Sensitive content placeholder rules
## Timezone
## Language
## Activity sources
```

Any header missing → error and stop (indicates Step 3 / Step 4 damaged the file).

**5.3 CLAUDE.md / AGENTS.md sync check**

`diff CLAUDE.md AGENTS.md` — should only differ on the first line (`# <project-name> — Claude Entry Point` vs `Agent Entry Point`). Other lines diff → warn (indicates Step 4 updated only one side).

**5.4 `.agents/skills/` mirror verification** (only when Step 1.4 picked `Yes`)

Verify the two sources from Step 3.2 separately:

- **commands source**: for each `${CLAUDE_PLUGIN_ROOT}/commands/<name>.md`, compute the "expected SKILL.md content" via the Step 3.2 same conversion (inject `name:` field), then byte-compare against `.agents/skills/<name>/SKILL.md`
- **skills source**: for each `${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md`, byte-compare directly against `.agents/skills/<name>/SKILL.md`

Any inconsistency → error listing the diverging paths and stop. **Note**: `commands/` and `skills/` are two independent source kinds with distinct conversions (see Step 3.2 table); each goes directly into `.agents/skills/` without crossing.

**5.5 Summary print**

```
✅ /holo:init complete

Templates: Created A | Skipped (identical) B | Kept existing C | Overwritten D | Merged E
.agents/skills/ mirror: <generated N / skipped>

Suggested next steps:
  1. Fill in remaining placeholders (N items above) — recommend starting with ai_context/project_background.md + handoff.md
  2. git add + commit the skeleton first, then fill content in increments (cleaner git history)
  3. Maintain the project subsequently via /go / /commit / /todo-add etc. skills
```

## Constraints

- **Never silently overwrite**: any template conflict must ask the user
- **Do not touch non-template files**: existing files outside template paths are not touched
- **Do not `git add` / do not commit**: `/holo:init` only generates / modifies files; commits are done by the user via `/commit`
- **Placeholder syntax fixed at `<...>`**: grep / Edit both rely on this convention; do not introduce other forms like `{{...}}` / `$VAR`
- **Interruption preserves progress**: each fill value in Step 4 is written to disk immediately upon answer, not deferred to batch
