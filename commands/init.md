---
description: Project skeleton initialization — drop the standard skeleton from the plugin's templates/project-skeleton/ (CLAUDE.md / AGENTS.md / ai_context/ / docs/todo_list.md / logs/) into the current working directory, then based on repo probing + user questioning fill placeholders with the project's actual values. Step 0 asks language axes first (content_language / conversation_language); then three rounds of questioning: Round 1 (project name / one-or-two-sentence goal / main branch / timezone — Q2 answer fans out to README description + plugin.json description + ai_context/project_background.md §Goal) / Round 2 (top-level directory classification, conditional) / Round 4 (doc bootstrap for architecture.md + requirements.md — each: auto-scan / manual / skip). Template uses a three-bucket schema: REQUIRED `<...>` (always filled by Round 1 / Step 0) / PROGRESSIVE `_(none yet — delete this marker once content is added)_` (template starts empty, fill as evolves) / INFERRED (Step 4.4 deterministic AI-infer). Optional generation of `.agents/skills/` mirror. No arguments; empty directory or already initialized both handled. Never silently overwrites — conflicts ask file-type-dispatched options (`.gitignore` → keep / overwrite / smart-merge with three-phase LLM-reorganize pipeline; markdown → keep / overwrite / merge mechanical append; other non-markdown → keep / overwrite). Does not touch non-template files, does not git add, does not commit. Triggers: /holo:init / initialize project / install skeleton / create an empty project.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (template files landed in the project, the filled-in placeholder values, the `skills_config.md §Language` values written by Step 4.2, any in-place translation result) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / `[lang-translate]` progress lines / planned-actions print / `Step N skipped` lines) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, ISO 639-1 codes (`zh`, `en`, etc.), and structural prefixes (`Step N:`, `NEW`, `SAME`, `CONFLICT`, `SAME-after-translate`, `CONFLICT-after-translate`) stay English regardless. **Note on the bootstrap edge case**: until Step 0 settles `<conversation_language>` (the Step 0 question itself is asked before any settle), the AI follows `auto` semantics (per-turn match the user's most recent message language); from Step 0's answer onward the chosen value governs all subsequent user-facing output in this init run.

# /holo:init — project skeleton initialization

Drop the templates under `${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton/` into the current working directory, then based on repo probing + user questioning fill the `<...>` REQUIRED placeholders in the templates with the project's actual values. PROGRESSIVE sections start empty with a `_(none yet — delete this marker once content is added)_` marker and fill as the project evolves. **Does not touch existing non-template files**; template conflicts always stop and ask the user, no silent overwrite.

No arguments. The repo's current state is probed automatically (empty directory / existing code / previously initialized all handled); no mode flag needed.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`. Until Step 0 settles `<conversation_language>` (only the Step 0 question itself precedes it), follow `auto` semantics — match the user's most recent message language for entries written then.

The flow below is split into `## Step 0:` ~ `## Step 5:`.

**Before entering Step 0**: call **<progress tool>** to pre-register Step 0 ~ Step 5 (one entry per step, `content` as `Step N: <sub-section title>`, all `status` = `pending`). This is a hard requirement — **do not proceed without calling <progress tool>**.

On entering each step: flip the current step to `in_progress` and mark the previous one `completed`, then do the actual work. Skipping a step: mark it `completed` directly and print one line in the conversation `Step N skipped (reason: …)`.

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block before each state change. Semantic alignment: pre-register + flip state + mark complete.

## Step 0: Language axes (asked first)

> **Language**: user-facing — render both language questions and their option descriptions in `conversation_language` per `ai_context/skills_config.md §Language`. **Bootstrap edge case**: until question 2 settles `<conversation_language>`, follow `auto` semantics — match the user's most recent message language for the questions themselves; from this point on, the chosen value governs all subsequent user-facing output. ISO 639-1 codes (`en`, `zh`, etc.) and the `auto` keyword stay English in option text.

**Hard rule**: AI MUST surface `<ask tool>` for both questions even when sensible defaults exist. Defaults appear as `Recommended` options on the rendered ask; they are NEVER AI-applied silently. The user picks (or overrides via the ask tool's `Other` path). This applies equally on fresh-init and re-init paths.

Use **<ask tool>** to ask 2 questions covering the project-level language config (later written into `ai_context/skills_config.md §Language` by Step 4.2 — see Step 4.2's "language config write-back" paragraph):

1. **Project content language?** — the language of every written artifact the AI produces or maintains in this project: `ai_context/` / `docs/` / `logs/` / commits / README / skill output / new code comments. Accepts any ISO 639-1 code. Default suggestion: `en` (or the conversation language if that is a single ISO 639-1 code).
2. **AI conversation language?** — the language of AI ↔ user turns (`AskUserQuestion` / replies / confirmations). Accepts `auto | <ISO 639-1>`. `auto` follows the user's current-message language per turn. Any explicit value is a hard rule with a single-message escape hatch ("respond in `<other>`"). Default suggestion: `auto`.

Record the user's choices as `<content_language>` and `<conversation_language>` — referenced below by Step 1.2 (template inventory baseline lookup), Step 2 (existing-directory translation detection), Step 3.1 (template variant lookup), and Step 4.2 (write back into `skills_config.md §Language`).

ISO 639-1 lock: `zh`, not `cn` (country code). Locale variants (`zh-CN`, `zh-TW`) reserved for future regional split — current phase rejects them.

**On re-init** (the project already has `ai_context/skills_config.md §Language` set): the existing values are SHOWN as the `Recommended` options for each question (alongside the template defaults `en` / `auto`); the user confirms or overrides. The ask is never bypassed. After answering, Step 4.2 writes back the chosen values, which may be no-ops if the user picked the existing values.

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

**1.5 Print plan**

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

This is informational only — Step 1.5 (this Print plan step) still proceeds with the user's chosen `/holo:init` invocation, and Step 2 onward runs normally. The hint surfaces the existence of `/holo:update` for users who launched `/holo:init` reflexively without realizing the upgrade path exists.

## Step 2: Existing-directory language detection (conditional)

> **Language**: disk-bound — write any translated template files (in-place rewrites of existing on-disk files) in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names, structural prefixes (`SAME`, `CONFLICT`, `SAME-after-translate`, `CONFLICT-after-translate`) stay English.

> **Language**: user-facing — render the single Yes / No translation question, the dirty-tree fail-loud line, the `[lang-translate]` progress lines, the post-translation summary, and the No-path warning block in `conversation_language` per `ai_context/skills_config.md §Language`. File paths quoted in messages stay verbatim; only surrounding prose translates.

> **Language (sub-agent dispatch)**: the 2.5 two-phase four-agent review chain dispatches sub-agents in both phases (Phase 1: Semantic fidelity; Phase 2: glossary / structure / back-translation in parallel). The parent MUST inject the language axes into each sub-agent's prompt explicitly. Include verbatim: "Reply in `conversation_language`=`<value>`; write any disk artifacts in `content_language`=`<value>`; both values from `ai_context/skills_config.md §Language`." Sub-agents do not inherit the parent's language config — they must be told. Sub-agent report-back (review verdicts) to the parent is a USER surface; the translated file landed on disk is DISK surface. **Place this injection at the end of the sub-agent prompt** (recency-favorable position), not in the header / middle — sub-agents have just read canonical EN source templates in their translation / review scope, so the dispatch directive needs recency advantage over the scanned content to keep the reply (review verdicts) in `conversation_language`.

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

> **Language (sub-agent dispatch)**: branch (c)'s on-the-fly two-phase four-agent translation chain dispatches sub-agents in both phases (Phase 1: Semantic fidelity; Phase 2: glossary / structure / back-translation in parallel). The parent MUST inject the language axes into each sub-agent's prompt explicitly. Include verbatim: "Reply in `conversation_language`=`<value>`; write any disk artifacts in `content_language`=`<value>`; both values from `ai_context/skills_config.md §Language`." Sub-agents do not inherit the parent's language config — they must be told. The translated `.md` content the sub-agents write is DISK surface; their per-file review verdicts returned to the parent are USER surface. **Place this injection at the end of the sub-agent prompt** (recency-favorable position), not in the header / middle — sub-agents have just read canonical EN source templates in their translation / review scope, so the dispatch directive needs recency advantage over the scanned content to keep the reply (review verdicts) in `conversation_language`.

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

> **Language**: user-facing — render the Round 1 / Round 2 / Round 4 `<ask tool>` question batches, their option labels, and the Skip-acknowledgement lines in `conversation_language` per `ai_context/skills_config.md §Language`. Default-value suggestions probed in Step 1.3 (project name candidates, main branch defaults, timezone strings like `UTC` / `Asia/Shanghai`) stay verbatim.

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

**Hard rule**: AI MUST surface `<ask tool>` for all 4 questions even when defaults from Step 1.3 are confidently inferred (project name from directory, main branch from git config, timezone from system). Defaults appear as `Recommended` options on the rendered ask; they are NEVER AI-applied silently. Skip / Other is a user choice never an AI shortcut.

Use **<ask tool>** to ask 4 questions at once (values probed in Step 1.3 act as `Recommended` options; the user can pick `Other` to fill in their own):

1. Project name (for `<project-name>` in CLAUDE.md / AGENTS.md / README.md)
2. **Project primary goal** — one or two sentences naming the project's primary goal (what it is / what problem it solves). This single answer fans out to **three sinks** simultaneously: `README.md` first-paragraph one-line description, `.claude-plugin/plugin.json` `description` field (if a plugin manifest exists in the project — most consumer projects do not, skip silently when absent), and `ai_context/project_background.md §Goal` section body
3. Main branch name (for `ai_context/skills_config.md` §Main branch policy; default `main`)
4. Timezone command template (for `ai_context/skills_config.md` §Timezone; default `TZ='UTC' date '+%Y-%m-%d_%H%M%S'`)

After receiving answers, **immediately** use `Edit` to write into the corresponding files (do not batch then write — interruptions still preserve progress). Q2's answer is written to all three sinks in the same pass.

**Additionally — language config write-back from Step 0**: at this same point, use `Edit` to write the `<content_language>` and `<conversation_language>` values chosen in Step 0 into **three sinks simultaneously**:

1. `ai_context/skills_config.md §Language` (canonical source per `ai_context/decisions.md` §Language Configuration #17)
2. `CLAUDE.md §Language` (hardcoded `- \`content_language: <value>\`` + `- \`conversation_language: <value>\`` bullets — read-cache for the AI's session-start awareness)
3. `AGENTS.md §Language` (byte-identical to CLAUDE.md §Language except the Sync-section title direction)

All three carry the same two values, replacing the template defaults (`content_language: en` / `conversation_language: auto`) with the user's chosen values. If the user's choices match the template defaults, this is a no-op (still verify the lines exist and have the chosen values). The three-way write keeps the read-cache in sync with canonical at init time — `/holo:update` finding category `claude_agents_lang_drift` (per `scripts/holo_update_check.py`) catches drift introduced after init.

**4.3 Top-level directory classification questions (Round 2)**

**Hard rule** (when applicable): if Step 1.3 detected top-level directories beyond `.git/` / `ai_context/` / `docs/` / `logs/`, AI MUST surface `<ask tool>` for each detected directory; never auto-classify or auto-skip. When no such directories exist (typical empty-directory init), this round is skipped per its own conditional — that is not the AI exercising discretion, it's the round having no applicable input.

If Step 1.3 detected such directories, use **<ask tool>** to ask at most 4 questions, one probed directory per question, let the user classify:

- `source` → written into `skills_config.md` §Source directories
- `data-contract` → written into `skills_config.md` §Data contract directories
- `example-artifact` → written into `skills_config.md` §Example artifact directories
- `do-not-commit` → written into `skills_config.md` §Do-not-commit paths
- `skip` → not written into any section

More than 4 directories → batch. No such directories (empty-directory init scenario) → skip Round 2 entirely.

**4.4 Inferred fills (no questioning, write directly)**

**Hard rule exemption**: this sub-step is DETERMINISTIC AI-INFER from Step 1.3 probe results — no ask, no discretion. The must-ask rule does NOT apply here. The values are derived programmatically from the file tree.

The following values can be derived directly from Step 1.3 without further questioning:

- Top-Level Structure of `architecture.md`: expand the top-level directory inventory from Step 1.3 into `- \`<dir>/\` — <inferred description / leave blank for user to fill>` form (leave `<...>` for inferred description so the user can supplement). **Note**: when Round 4 Q1 (Step 4.5 below) picks `Auto-scan` or `Manual input` for `architecture.md`, Step 4.4 still seeds Top-Level Structure (deterministic baseline); Round 4 then fills the other sections with AI survey or user prose on top. When Round 4 Q1 picks `Skip for now`, this Step 4.4 baseline IS the architecture.md content for the section — other sections retain their `_(none yet — ...)_` markers from the template
- Default Priority of `read_scope.md`: auto-include existing `docs/` / top-level README.md (if any). When literally nothing is inferrable, leave the section with its template `_(none yet — ...)_` marker — do NOT replace with an empty list

**4.5 Doc bootstrap questions (Round 4 — architecture.md + requirements.md)**

Purpose: give the user explicit control over whether `ai_context/architecture.md` and `ai_context/requirements.md` get an AI-survey-based first draft, a user-provided first pass, or are left with template `_(none yet — ...)_` markers for later progressive fill.

**Hard rule**: AI MUST surface `<ask tool>` for both questions even when one option (typically `Skip for now`) looks obviously correct. Default appears as `Recommended` on the rendered ask; the user picks. Skip is a user choice never an AI shortcut.

Use **<ask tool>** to ask 2 questions at once:

**Q1 — `ai_context/architecture.md` how should it be filled?**

- **`Auto-scan project` (recommended on existing codebases)**: AI surveys file tree + top-level directories + key entry-point files + manifest files (package.json / pyproject.toml / etc.), drafts content into the file's sections (`## System Layers` / `## Key Boundaries` / `## Runtime / Entry Points` — Top-Level Structure already seeded by Step 4.4). Sections that cannot be confidently inferred remain with `_(none yet — ...)_` markers. No multi-agent review (out of scope for Round 4 — quality audit is `/full-review`'s job)
- **`Manual input`**: user types a paragraph or bullet outline; AI distributes content into sections by section semantics + leaves the rest as `_(none yet — ...)_` markers
- **`Skip for now` (recommended on empty / scaffold-only projects)**: no write; sections keep their template `_(none yet — ...)_` markers. `## Top-Level Structure` retains the Step 4.4 baseline

**Q2 — `ai_context/requirements.md` how should it be filled?**

- **`Auto-scan project`**: best-effort — AI looks for README's "Requirements" / "Features" / "Functional spec" sections, existing `docs/requirements.md` if any, or specification-style files in the repo, and drafts a compressed index pointer block. **Caveat**: requirements are intent not code, so auto-scan effectiveness depends heavily on whether the repo has existing requirements prose. Most fresh / code-only projects → `Skip for now` is the better default
- **`Manual input`**: user provides text; AI lands it in `## Sections` with appropriate pointer structure
- **`Skip for now` (recommended default)**: no write; section keeps its template `_(none yet — ...)_` marker

After receiving answers for both, **immediately** use `Edit` to write to disk (interruptions still preserve progress). For `Auto-scan` paths, when the survey result is too thin to populate even one section, fall back to `Skip for now` behavior with a console line `[round-4] auto-scan produced no actionable content for <file>; falling back to _(none yet)_ marker.` This Auto-scan-only fallback is explicitly exempted from the "Skip is a user choice never an AI shortcut" hard rule in `## Constraints` — the transparency console line is the safety net; without this exemption the AI would be stuck (Auto-scan is the user's chosen path but produces no content, and re-asking the same question would be a loop).

## Step 5: Wrap-up verification

> **Language**: user-facing — render the wrap-up status report printed to the user (template-files landed, mirror status, language-config summary, next-steps suggestion) in `conversation_language` per `ai_context/skills_config.md §Language`. File paths and ISO 639-1 codes quoted in the report stay verbatim; only surrounding prose translates.

**5.1 Placeholder / marker residue scan**

Three-category scan (informational summary, not error gating unless category (a) is non-zero):

(a) Re-run the Step 4.1 grep; list any remaining `<...>` as a list — **MUST be 0** under the three-bucket schema (REQUIRED `<...>` blocks are filled by Step 0 + Round 1 + Step 4.4 + Round 4 `Auto-scan` / `Manual input` paths; PROGRESSIVE sections never had `<...>` to begin with — they ship with `_(none yet — ...)_` markers). If > 0 → error and stop; this indicates a Round 1 / Step 4.4 / Round 4 write missed its target file (a bug, not user discretion). See `ai_context/decisions.md` §Skill Implementation #15 for the schema rationale.

(b) PROGRESSIVE marker inventory — `grep -rn '_(none yet — delete this marker once content is added)_' CLAUDE.md AGENTS.md ai_context/ docs/ 2>/dev/null` lists every PROGRESSIVE section that is still empty (template default state). This is **informational only**: PROGRESSIVE markers are by-design intentional empties; they do not gate completion. Print as a single block so the user sees the remaining onboarding surface:

```
Progressive sections still empty (M items; fill as the project evolves — delete the marker line when adding first content):
  ai_context/project_background.md:25  _(none yet — delete this marker once content is added)_
  ai_context/handoff.md:31             _(none yet — delete this marker once content is added)_
  ...
```

(c) Legacy short-TODO scan — `grep -rn '_(TODO — skipped at /holo:init' CLAUDE.md AGENTS.md ai_context/ docs/ 2>/dev/null` detects markers left over from the pre-three-bucket schema (when Round 3's Skip path wrote 13-character short-TODOs). On a fresh `/holo:init` this MUST be 0. On a re-init of a project initialized under the old schema, it may report > 0; surface them so the user can manually copy the corresponding `<...>` guidance back from the plugin template (per `ai_context/decisions.md` §Skill Implementation #15) or fill with real content. `/holo:update` also surfaces these as `legacy_skip_marker` informational findings.

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
- **Placeholder marker conventions (three-bucket schema)** — see `ai_context/decisions.md` §Skill Implementation #15 for rationale:
  - **REQUIRED** `<...>` syntax: filled by Step 0 (Language) or Round 1 (Project basics) or Step 4.4 (deterministic AI-infer) or Round 4 `Auto-scan` / `Manual input` paths. Step 5.1(a) gates residue=0
  - **PROGRESSIVE** `_(none yet — delete this marker once content is added)_` line: template ships with this marker; user deletes when adding first content. Not reported as drift / not gated
  - **INFERRED**: same `<...>` syntax as REQUIRED, filled by Step 4.4 from probed repo state without user ask
  - The grep / Edit logic relies on this convention; do not introduce other forms like `{{...}}` / `$VAR`
- **AI must surface ask; never auto-apply defaults; never auto-skip** — Step 0 (Language) / Step 4.2 (Round 1) / Step 4.3 (Round 2, when applicable) / Step 4.5 (Round 4) MUST surface `<ask tool>` even when sensible defaults exist. Defaults are `Recommended` options on the rendered ask, never AI-applied silently. Skip is a user choice never an AI shortcut. Step 4.4 (Inferred fills) is the only exemption — it is designed as deterministic AI-infer with no ask
- **Single explicit Skip exemption — Round 4 Auto-scan fallback** — when the user picks `Auto-scan` for a Round 4 question (architecture.md or requirements.md) but the AI survey produces no actionable content for even one section, the AI may fall back to `Skip for now` behavior and print a transparency console line `[round-4] auto-scan produced no actionable content for <file>; falling back to _(none yet)_ marker.` This is the **only** AI-driven Skip path permitted; it does not generalise to other rounds. Re-asking the user is not viable here because the user already picked Auto-scan; the failure is on the inference side and a re-ask would loop on the same choice. The transparency line documents the fallback so the user can manually retry / pick a different option on a re-run if desired
- **Interruption preserves progress**: each fill value in Step 4 is written to disk immediately upon answer, not deferred to batch
