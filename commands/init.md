---
description: Project skeleton initialization — thin user-entry shell that collects user answers (Step 0 language axes + Round 1 project basics + Round 2 directory classification + Round 3 doc bootstrap) and delegates all per-file landing to `commands/update.md ## Reconcile core` SOP (mode=`"init-post-bootstrap"`). Reconcile core handles template inventory / language alignment / NEW file copy / drift detection / 3-bucket dispatch (smart-merge / deterministic --fix / display-only). Three-bucket template schema: REQUIRED `<...>` (filled by Step 0 + Round 1 + Step 5 substitution) / PROGRESSIVE marker (filled as project evolves) / INFERRED (Step 5 AI-infer). No arguments; empty + already-initialized both handled. Never silently overwrites — CONFLICTs flow through smart-merge with `take_snapshot` backup; `.gitignore` via append-only union. Does not git add, does not commit. Triggers: /holo:init / initialize project / install skeleton / create an empty project.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (template files landed in the project, the filled-in placeholder values written by Step 5 substitution, the `skills_config.md §Language` values, any in-place translation result produced by Reconcile.Step 2b) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / `[lang-translate]` progress lines / planned-actions print / `Step N skipped` lines) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, ISO 639-1 codes (`zh`, `en`, etc.), and structural prefixes (`Step N:`, `NEW`, `EXISTING`) stay English regardless. **Note on the bootstrap edge case**: until Step 0 settles `<conversation_language>` (the Step 0 question itself is asked before any settle), the AI follows `auto` semantics (per-turn match the user's most recent message language); from Step 0's answer onward the chosen value governs all subsequent user-facing output in this init run.

# /holo:init — project skeleton initialization

Thin user-entry shell around the shared **`## Reconcile core`** SOP defined in `commands/update.md`. The shell asks Step 0 (Language axes) + Round 1 (Project basics) + Round 2 (Directory classification, conditional) BEFORE invoking Reconcile, so the post-Reconcile substitution (Step 5) has the user's answers available to fill REQUIRED `<...>` placeholders in the landed templates. After Reconcile completes, Step 6 (Round 3 doc bootstrap) handles `ai_context/architecture.md` + `ai_context/requirements.md` first-pass content; Step 7 prints the final summary.

**Per-file landing is owned by Reconcile core** (in `commands/update.md`). Init does not classify SAME / CONFLICT, does not handle CONFLICT directly, does not translate files, does not copy templates — all of that is delegated. To change file-update behavior, edit `commands/update.md ## Reconcile core`; do not duplicate logic into this shell.

No arguments. The repo's current state is probed automatically (empty directory / existing code / previously initialized all handled by Reconcile core's drift-detection sub-step); no mode flag needed.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`. Until Step 0 settles `<conversation_language>` (only the Step 0 question itself precedes it), follow `auto` semantics — match the user's most recent message language for entries written then.

The flow is split into `## Step 0:` ~ `## Step 7:`.

**Before entering Step 0**: call **<progress tool>** to pre-register Step 0 ~ Step 7 (one entry per step, `content` as `Step N: <sub-section title>`, all `status` = `pending`). This is a hard requirement — **do not proceed without calling <progress tool>**.

On entering each step: flip the current step to `in_progress` and mark the previous one `completed`, then do the actual work. Skipping a step: mark it `completed` directly and print one line in the conversation `Step N skipped (reason: …)`.

**Sub-tasks on Step 4 (recommended)**: when Step 4 invokes Reconcile core, expand `Step 4:` into `Step 4a:` ~ `Step 4f:` matching the 6 Reconcile sub-steps (per the `/go` skill's sub-task expansion contract — only the currently active step is fine-grained; Step 0 / 1 / 2 / 3 / 5 / 6 / 7 stay collapsed). Fold back into `Step 4:` `completed` when entering Step 5.

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block before each state change.

## Step 0: Language axes (asked first)

> **Language**: user-facing — render both language questions and their option descriptions in `conversation_language` per `ai_context/skills_config.md §Language`. **Bootstrap edge case**: until question 2 settles `<conversation_language>`, follow `auto` semantics — match the user's most recent message language for the questions themselves; from this point on, the chosen value governs all subsequent user-facing output. ISO 639-1 codes (`en`, `zh`, etc.) and the `auto` keyword stay English in option text.

**Hard rule**: AI MUST surface `<ask tool>` for both questions even when sensible defaults exist. Defaults appear as `Recommended` options on the rendered ask; they are NEVER AI-applied silently. The user picks (or overrides via the ask tool's `Other` path). This applies equally on fresh-init and re-init paths.

Use **<ask tool>** to ask 2 questions covering the project-level language config (later written into `ai_context/skills_config.md §Language` by Step 5 — see Step 5's substitution paragraph):

1. **Project content language?** — the language of every written artifact the AI produces or maintains in this project: `ai_context/` / `docs/` / `logs/` / commits / README / skill output / new code comments. Accepts any ISO 639-1 code. Default suggestion: `en` (or the conversation language if that is a single ISO 639-1 code).
2. **AI conversation language?** — the language of AI ↔ user turns (`AskUserQuestion` / replies / confirmations). Accepts `auto | <ISO 639-1>`. `auto` follows the user's current-message language per turn. Any explicit value is a hard rule with a single-message escape hatch ("respond in `<other>`"). Default suggestion: `auto`.

Record the user's choices as `<content_language>` and `<conversation_language>` — referenced below by Step 1.4 (mirror Q), Step 4 (passed as Reconcile core input parameter), and Step 5 (written into the landed `skills_config.md §Language` + CLAUDE/AGENTS gap-territory bullets).

ISO 639-1 lock: `zh`, not `cn` (country code). Locale variants (`zh-CN`, `zh-TW`) reserved for future regional split — current phase rejects them.

**On re-init** (the project already has `ai_context/skills_config.md §Language` set): the existing values are SHOWN as the `Recommended` options for each question (alongside the template defaults `en` / `auto`); the user confirms or overrides. The ask is never bypassed. After answering, Step 5 writes back the chosen values, which may be no-ops if the user picked the existing values.

## Step 1: Pre-check (probe + mirror Q)

Purpose: paint a clear picture of "what the target directory looks like" so subsequent steps have an accurate basis. **No template-file diffing here** — that work belongs to Reconcile.Step 1 (path-only inventory) and Reconcile.Step 4 (sentinel-aware drift detection); init does NOT pre-classify SAME / CONFLICT.

**1.1 Working directory basic state**

- `pwd` to confirm the absolute path of the current working directory
- `ls -la` to view the top-level file / directory listing
- `test -d .git && git status --short` to check whether it is a git repo + working-tree state. dirty → print a warning (do not stop, because `/holo:init` does not commit; but advise the user to stash / commit existing changes first to keep the git history cleaner)

**1.2 Repo content probing** (pre-fills values for Round 1 questioning)

- Project name candidates (take the first non-empty in priority order):
  1. `name` field in `package.json`
  2. `[project] name` or `[tool.poetry] name` in `pyproject.toml`
  3. `[package] name` in `Cargo.toml`
  4. last segment of module path in `go.mod`
  5. repo root directory name
- One-line description candidates: `description` field of the above manifests; if none → take the first sentence of the existing `README.md` opening paragraph
- Git remote URL: `git remote get-url origin 2>/dev/null`
- Main branch: `git symbolic-ref --short HEAD 2>/dev/null` + `git branch --list main master` (default `main`)
- Top-level directory inventory (excluding obvious noise like `.git/` / `node_modules/` / `__pycache__/` / `.venv/`): candidates for the Top-Level Structure of `architecture.md` + the Source / Data contract / Example artifact candidates of `skills_config.md`
- Timezone: local `date +%Z` as the default for `skills_config.md §Timezone`

**1.3 Re-init detection**

Initialization detected if any of the following exist:

- `CLAUDE.md` at top level
- `AGENTS.md` at top level
- `ai_context/` directory

If any present → re-init path. Print one informational hint line **before** the Step 1.4 mirror question:

```
Hint: this project is already initialized. If you only want non-destructive
structural sync after a plugin upgrade (add missing template files / section
headers / skills_config fields with `_(TODO)_` stubs, regenerate
.agents/skills/ mirror, re-align sentinel-aware drift via smart-merge),
`/holo:update` is the lighter tool — it skips the Round 1 / 2 / 4 Q&A and
the REQUIRED `<...>` substitution loop. Both `/holo:init` and `/holo:update`
flow through the same `## Reconcile core` SOP, so the per-file landing
decisions you'll see are identical; continue with `/holo:init` only if you
intend to re-walk the bootstrap questions.
```

This is informational only — Step 1 proceeds with the user's chosen `/holo:init` invocation.

**1.4 Ask whether to generate `.agents/skills/` mirror**

Use **<ask tool>** to ask one question:

> Generate `.agents/skills/` mirror? (Converts all plugin commands/ + skills/ into `.agents/skills/<name>/SKILL.md`. Purpose: let Codex / other non-Claude runtimes also recognize this set of commands / skills for cross-validation — they do not recognize slash commands, only SKILL.md. Pick No if not needed — if this repo invokes the plugin only via Claude / Claude Code, a local duplicate is redundant.)

Options:

- `No` (recommended default): skip `.agents/` generation.
- `Yes`: pre-create an empty `<target_root>/.agents/skills/` directory so Reconcile.Step 4 drift detection surfaces `agents_sync.missing` findings (one per command + skill the plugin ships); Reconcile.Step 5b's `--fix` then populates it via `expected_mirror_content()`. Step 7 verifies the mirror byte-matches expected output.

Record the user's choice (referenced below as `<.agents-opt>`). On `Yes`, `mkdir -p .agents/skills/` immediately so the directory exists before Reconcile.Step 4 runs.

**1.5 Print plan**

Aggregate the above into a "planned actions" print:

```
Language config (from Step 0):
  - content_language:      <value>
  - conversation_language: <value>
.agents/skills/ mirror: <yes / no>
Probed pre-fill values:
  - Project name candidate: <value>
  - One-line description:   <value>
  - Main branch:            <value>
  - Timezone:               <value>
  - Top-level directories:  <list>
Re-init detected: <yes / no>
```

## Step 2: Required questions (Round 1)

> **Language**: user-facing — render the Round 1 `<ask tool>` question batch + option labels in `conversation_language` per `ai_context/skills_config.md §Language`. Default-value suggestions probed in Step 1.2 (project name candidates, main branch defaults, timezone strings like `UTC` / `Asia/Shanghai`) stay verbatim.

**Hard rule**: AI MUST surface `<ask tool>` for all 4 questions even when defaults from Step 1.2 are confidently inferred (project name from directory, main branch from git config, timezone from system). Defaults appear as `Recommended` options on the rendered ask; they are NEVER AI-applied silently.

Use **<ask tool>** to ask 4 questions at once (values probed in Step 1.2 act as `Recommended` options; the user can pick `Other` to fill in their own):

1. Project name (for `<project-name>` in CLAUDE.md / AGENTS.md / README.md)
2. **Project primary goal** — one or two sentences naming the project's primary goal (what it is / what problem it solves). This single answer fans out to **three sinks** simultaneously when Step 5 substitutes: `README.md` first-paragraph one-line description, `.claude-plugin/plugin.json` `description` field (if a plugin manifest exists in the project — most consumer projects do not, skip silently when absent), and `ai_context/project_background.md §Goal` section body
3. Main branch name (for `ai_context/skills_config.md` §Main branch policy; default `main`)
4. Timezone command template (for `ai_context/skills_config.md` §Timezone; default `TZ='UTC' date '+%Y-%m-%d_%H%M%S'`)

Record answers as `<project_name>`, `<project_goal>`, `<main_branch>`, `<timezone_cmd>` for Step 5's substitution pass. Do NOT Edit any file here — the files don't exist yet (Reconcile.Step 3 copies them in Step 4). Step 5 writes after Reconcile lands the templates.

## Step 3: Top-level directory classification questions (Round 2)

> **Language**: user-facing — render in `conversation_language` per `ai_context/skills_config.md §Language`. File paths stay verbatim.

**Hard rule** (when applicable): if Step 1.2 detected top-level directories beyond `.git/` / `ai_context/` / `docs/` / `logs/`, AI MUST surface `<ask tool>` for each detected directory; never auto-classify or auto-skip. When no such directories exist (typical empty-directory init), this step is skipped per its own conditional — that is not the AI exercising discretion, it's the round having no applicable input.

If Step 1.2 detected such directories, use **<ask tool>** to ask at most 4 questions, one probed directory per question, let the user classify:

- `source` → written into `skills_config.md` §Source directories
- `data-contract` → written into `skills_config.md` §Data contract directories
- `example-artifact` → written into `skills_config.md` §Example artifact directories
- `do-not-commit` → written into `skills_config.md` §Do-not-commit paths
- `skip` → not written into any section

More than 4 directories → batch. No such directories (empty-directory init scenario) → mark Step 3 `skipped` (reason: "no extra top-level directories detected") and move to Step 4.

Record the per-directory classifications as `<dir_classifications>` for Step 5's substitution pass.

## Step 4: Invoke Reconcile core

Call the shared **`## Reconcile core`** SOP defined in `commands/update.md` with:

```
mode = "init-post-bootstrap"
target_root = "."                                       # consumer project root (CWD where /holo:init was launched)
plugin_root = "${CLAUDE_PLUGIN_ROOT}"                   # if unset, derive from this command's path back to the plugin root
content_language = <content_language>                   # from Step 0 answer
```

Reconcile core executes its 6 sub-steps (Template inventory → Language alignment 2a/2b → NEW file copy → Drift detection → 3-bucket dispatch 5a/5b/5c → Return). On return, capture:

```
{
  write_counts: { merged: M, overwritten: N, kept: K, failed: Z, new_copied: P, deterministic_fixed: Q },
  fix_counts: { regenerated, created, deleted, template_copied, section_appended, field_appended, gitignore_appended, claude_agents_lang_fixed, orphan_siblings_left },  # raw `holo_update_check.py --fix --json` output; init's Step 7.5 summary aggregates the per-category counters into `deterministic_fixed=Q`, but the full sub-object is preserved here for parity with `commands/update.md` Step 3's finer-grained mapping
  snapshot_dir: "<path or null>",
  remaining_drift: [...],
  translation_log: [...]
}
```

**Init-specific notes on Reconcile sub-step behavior**:

- **Reconcile.Step 1** classifies every template file as `NEW` (typical for fresh empty-dir init) or `EXISTING` (typical for re-init). Both are handled by Reconcile; init does not branch on the count.
- **Reconcile.Step 2b** runs whenever `EXISTING` count ≥ 1 (so re-init paths get the in-place translation chain offered; fresh-init paths skip 2b silently since there are no consumer files to compare).
- **Reconcile.Step 3** does the wholesale NEW file copy (the bulk of fresh-init's work). Copied files retain `<...>` REQUIRED placeholders + PROGRESSIVE markers verbatim — Step 5 (post-Reconcile) substitutes the REQUIRED placeholders.
- **Reconcile.Step 4 drift detection** runs against the post-Step-3 state. On fresh-init, `claude_agents_lang_drift` will surface because CLAUDE.md / AGENTS.md just landed with template-default values (`content_language: en` / `conversation_language: auto`) that may differ from the user's Step 0 answers; this is expected and resolved by Step 5b's `--fix` in the same dispatch (no separate hand-edit needed).
- **Reconcile.Step 5a smart-merge** typically does not fire on fresh-init (no EXISTING markdown files → no `sentinel_layout_drift` findings). On re-init it fires for any consumer file whose sentinel structure drifted from the new plugin template — same dispatch as `/holo:update`.
- **Reconcile.Step 5b `--fix`** populates `.agents/skills/` if Step 1.4 chose Yes (the empty directory pre-created in Step 1.4 makes the script see `agents_sync.missing` findings, which `--fix` fills via `expected_mirror_content()`).

## Step 5: REQUIRED placeholder substitution

> **Language**: disk-bound — write the filled values into the landed template files in `content_language` per `ai_context/skills_config.md §Language`. The `_(none yet …)_` PROGRESSIVE-marker text and `<placeholder>` literal markers stay English regardless. Code identifiers, file paths, field names, and ISO 639-1 codes stay English.

Purpose: replace the `<...>` REQUIRED placeholders in the landed templates with the answers collected in Step 0 / Step 2 / Step 3, plus deterministic INFERRED fills from Step 1.2's probe.

**5.1 Grep pending placeholders**

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

Each remaining `<...>` is a real pending placeholder — excluding: (a) format examples inside code fences, (b) markdown table row examples, (c) HTML comments (MAINTENANCE section), (d) doc-reference patterns using `<name>` inside inline code spans.

**5.2 Round-1 substitution (project basics + language axes)**

Using the values recorded in Step 0 (`<content_language>`, `<conversation_language>`) and Step 2 (`<project_name>`, `<project_goal>`, `<main_branch>`, `<timezone_cmd>`), use `Edit` to write into the landed files:

- `<project-name>` → `<project_name>` in `CLAUDE.md` H1 + `AGENTS.md` H1 + `README.md` H1 (occurrences).
- `<project_goal>` answer fans out to **three sinks** simultaneously:
  1. `README.md` first-paragraph one-line description.
  2. `.claude-plugin/plugin.json` `description` field — write only if a plugin manifest exists in the project (typical consumer projects do not have one; skip silently when absent).
  3. `ai_context/project_background.md §Goal` section body.
- `<main_branch>` → `ai_context/skills_config.md §Main branch policy` `Main branch:` bullet.
- `<timezone_cmd>` → `ai_context/skills_config.md §Timezone` `Command template:` bullet.

**Language config write-back (three sinks)** — use `Edit` to write `<content_language>` and `<conversation_language>` into:

1. `ai_context/skills_config.md §Language` (canonical source per `ai_context/decisions.md` §Language Configuration #17) — gap-territory bullets outside the sentinel block (Option A layout).
2. `CLAUDE.md §Language` (gap-territory `- \`content_language: <value>\`` + `- \`conversation_language: <value>\`` backticked bullets positioned OUTSIDE the `<!-- holo:section start/end -->` block per Layout footer 2026-05-22 — read-cache for the AI's session-start awareness).
3. `AGENTS.md §Language` (byte-identical to CLAUDE.md §Language except the Sync-section title direction).

All three carry the same two values, replacing the template defaults (`content_language: en` / `conversation_language: auto`) with the user's chosen values. If the user's choices match the template defaults, this is a no-op (still verify the lines exist and have the chosen values).

**Step 5.2 is the authoritative write of the user's Step-0 choice in every case** — do not mistake it for a defense-in-depth verification layer:

- **Fresh-init path**: Reconcile.Step 3 lands the three sinks with template defaults (`content_language: en` / `conversation_language: auto`); Reconcile.Step 4 drift detection sees skills_config = `en` and CLAUDE/AGENTS = `en` (matching) → no `claude_agents_lang_drift` finding → Reconcile.Step 5b's `--fix` is a no-op for the §Language axes. Step 5.2 here is **the first and only authoritative write** of the user's Step-0 choice into all three sinks.
- **Re-init path** (project already has Step-0 values, possibly out of sync between skills_config and CLAUDE/AGENTS): Reconcile.Step 5b's `--fix` first reconciles CLAUDE/AGENTS toward whatever skills_config currently holds (per Source-of-truth model A); Step 5.2 then layers the user's freshly-answered Step-0 choice on top, which may differ from both pre-existing values.

In both cases removing or skipping Step 5.2 would silently lose the user's Step-0 answer on fresh init — do not remove this step thinking Reconcile.Step 5b covers it.

**5.3 Round-2 substitution (top-level directory classifications)**

For each entry in `<dir_classifications>` (from Step 3), use `Edit` to append to the matching `skills_config.md` section's bullet list:

- `source` → `## Source directories` bullet list
- `data-contract` → `## Data contract directories` bullet list
- `example-artifact` → `## Example artifact directories` bullet list
- `do-not-commit` → `## Do-not-commit paths` bullet list

`skip` entries are not written anywhere. When all probed directories were classified `skip`, the four sections may legitimately retain their `(none)` bullets — no action.

**5.4 Inferred fills (no questioning, write directly)**

**Hard rule exemption**: this sub-step is DETERMINISTIC AI-INFER from Step 1.2 probe results — no ask, no discretion. The must-ask rule does NOT apply here.

- **Top-Level Structure of `architecture.md`**: expand the top-level directory inventory from Step 1.2 into `- \`<dir>/\` — <inferred description / leave blank for user to fill>` form (leave `<...>` for inferred description so the user can supplement). **Note**: when Step 6 Round 3 Q1 picks `Auto-scan` or `Manual input` for `architecture.md`, this Step 5.4 seed remains as the baseline; Round 3 then fills the other sections with AI survey or user prose on top. When Round 3 Q1 picks `Skip for now`, this Step 5.4 baseline IS the architecture.md content for the Top-Level Structure section — other sections retain their `_(none yet — ...)_` markers from the template.
- **Default priority of `instructions.md §Read Scope`**: auto-include existing `docs/` / top-level README.md (if any) as bullets under the "Project-specific default-priority paths" user-territory list. When literally nothing is inferrable, leave the list with its template `_(none yet — ...)_` marker — do NOT replace with an empty list.

## Step 6: Doc bootstrap questions (Round 3)

> **Language**: user-facing — render the Round 3 `<ask tool>` questions in `conversation_language` per `ai_context/skills_config.md §Language`.

Purpose: give the user explicit control over whether `ai_context/architecture.md` and `ai_context/requirements.md` get an AI-survey-based first draft, a user-provided first pass, or are left with template `_(none yet — ...)_` markers for later progressive fill.

**Hard rule**: AI MUST surface `<ask tool>` for both questions even when one option (typically `Skip for now`) looks obviously correct. Default appears as `Recommended` on the rendered ask; the user picks. Skip is a user choice never an AI shortcut.

Use **<ask tool>** to ask 2 questions at once:

**Q1 — `ai_context/architecture.md` how should it be filled?**

- **`Auto-scan project` (recommended on existing codebases)**: AI surveys file tree + top-level directories + key entry-point files + manifest files (package.json / pyproject.toml / etc.), drafts content into the file's sections (`## System Layers` / `## Key Boundaries` / `## Runtime / Entry Points` — Top-Level Structure already seeded by Step 5.4). Sections that cannot be confidently inferred remain with `_(none yet — ...)_` markers.
- **`Manual input`**: user types a paragraph or bullet outline; AI distributes content into sections by section semantics + leaves the rest as `_(none yet — ...)_` markers.
- **`Skip for now` (recommended on empty / scaffold-only projects)**: no write; sections keep their template `_(none yet — ...)_` markers. `## Top-Level Structure` retains the Step 5.4 baseline.

**Q2 — `ai_context/requirements.md` how should it be filled?**

- **`Auto-scan project`**: best-effort — AI looks for README's "Requirements" / "Features" / "Functional spec" sections, existing `docs/requirements.md` if any, or specification-style files in the repo, and drafts a compressed index pointer block. **Caveat**: requirements are intent not code, so auto-scan effectiveness depends heavily on whether the repo has existing requirements prose. Most fresh / code-only projects → `Skip for now` is the better default.
- **`Manual input`**: user provides text; AI lands it in `## Sections` with appropriate pointer structure.
- **`Skip for now` (recommended default)**: no write; section keeps its template `_(none yet — ...)_` marker.

After receiving answers for both, **immediately** use `Edit` to write to disk. For `Auto-scan` paths, when the survey result is too thin to populate even one section, fall back to `Skip for now` behavior with a console line `[round-3] auto-scan produced no actionable content for <file>; falling back to _(none yet)_ marker.` This Auto-scan-only fallback is explicitly exempted from the "Skip is a user choice never an AI shortcut" hard rule in `## Constraints` — the transparency console line is the safety net.

## Step 7: Wrap-up verification + final print

> **Language**: user-facing — render the wrap-up status report in `conversation_language` per `ai_context/skills_config.md §Language`. File paths and ISO 639-1 codes quoted in the report stay verbatim; only surrounding prose translates.

**7.1 Placeholder / marker residue scan**

Three-category scan (informational summary; only category (a) gates completion):

(a) Re-run the Step 5.1 grep; list any remaining `<...>` as a list — **MUST be 0** under the three-bucket schema (REQUIRED `<...>` blocks are filled by Step 0 + Step 2 + Step 5.4 + Step 6 `Auto-scan` / `Manual input` paths; PROGRESSIVE sections never had `<...>` to begin with — they ship with `_(none yet — ...)_` markers). If > 0 → error and stop; this indicates a Step 2 / Step 5.4 / Step 6 write missed its target file (a bug, not user discretion). See `ai_context/decisions.md` §Skill Implementation #15 for the schema rationale.

(b) PROGRESSIVE marker inventory — `grep -rn '_(none yet — delete this marker once content is added)_' CLAUDE.md AGENTS.md ai_context/ docs/ 2>/dev/null` lists every PROGRESSIVE section that is still empty (template default state). This is **informational only**: PROGRESSIVE markers are by-design intentional empties; they do not gate completion. Print as a single block so the user sees the remaining onboarding surface.

(c) Legacy short-TODO scan — `grep -rn '_(TODO — skipped at /holo:init' CLAUDE.md AGENTS.md ai_context/ docs/ 2>/dev/null` detects markers left over from the pre-three-bucket schema. On a fresh `/holo:init` this MUST be 0. On a re-init of a project initialized under the old schema, it may report > 0; surface them so the user can manually copy the corresponding `<...>` guidance back from the plugin template or fill with real content.

**7.2 skills_config.md self-check**

`Read` `ai_context/skills_config.md` and check whether all required section headers exist (per `ai_context/conventions.md §skills_config.md schema → Required headers`). Any header missing → error and stop (indicates Reconcile or Step 5 damaged the file).

**7.3 CLAUDE.md / AGENTS.md sync check**

`diff CLAUDE.md AGENTS.md` — should only differ on the first line (`# <project-name> — Claude Entry Point` vs `Agent Entry Point`). Other lines diff → warn (indicates Step 5 updated only one side, or smart-merge wrote asymmetrically).

**7.4 `.agents/skills/` mirror verification** (only when Step 1.4 picked `Yes`)

Verify Reconcile.Step 5b's `--fix` populated the mirror correctly: re-run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py" --json` and assert `agents_sync.stale / missing / orphan` are all empty. Any inconsistency → error listing the diverging paths and stop.

**7.5 Summary print**

```
✅ /holo:init complete

Templates landed (via Reconcile core):
  - new_copied:          <P>
  - smart-merged:        <M>     # re-init path only
  - overwritten:         <N>     # re-init path only
  - kept (no merge):     <K>     # re-init path only
  - failed-after-retry:  <Z>     # surface staging output if > 0
Deterministic --fix counts (mirror generation + section/field appends + gitignore sync + lang-bullet sync etc.): <Q>
Snapshot:                 <snapshot_dir or "(none — fresh init or no smart-merge writes)">
Translation log:          <count> work items processed during Reconcile.Step 2

Progressive sections still empty (M items; fill as the project evolves):
  <list from 7.1(b)>

Suggested next steps:
  1. Fill in remaining PROGRESSIVE sections — recommend starting with ai_context/project_background.md + handoff.md
  2. git add + commit the skeleton first, then fill content in increments (cleaner git history)
  3. Maintain the project subsequently via /go / /commit / /todo-add etc. skills
  4. After future plugin upgrades, run /holo:update to re-sync (same Reconcile core, lighter shell)
```

## Constraints

- **Reconcile core is the single source of truth for per-file landing logic** — Step 4 invokes it (mode=`"init-post-bootstrap"`); this shell does not classify SAME / CONFLICT, does not handle CONFLICT, does not translate files, does not copy templates. Changes to file-update behavior go to `commands/update.md ## Reconcile core`.
- **Never silently overwrite**: any template conflict (re-init paths) flows through Reconcile.Step 5a smart-merge dispatch's three-layer ask + `take_snapshot` backup.
- **Do not touch non-template files**: existing files outside template paths are not touched (Reconcile.Step 2b's CJK-detection scope is restricted to the canonical manifest).
- **Do not `git add` / do not commit**: `/holo:init` only generates / modifies files; commits are done by the user via `/commit`.
- **Placeholder marker conventions (three-bucket schema)** — see `ai_context/decisions.md` §Skill Implementation #15 for rationale:
  - **REQUIRED** `<...>` syntax: filled by Step 0 (Language) or Step 2 (Project basics) or Step 5.4 (deterministic AI-infer) or Step 6 `Auto-scan` / `Manual input` paths. Step 7.1(a) gates residue = 0.
  - **PROGRESSIVE** `_(none yet — delete this marker once content is added)_` line: template ships with this marker; user deletes when adding first content. Not reported as drift / not gated.
  - **INFERRED**: same `<...>` syntax as REQUIRED, filled by Step 5.4 from probed repo state without user ask.
  - The grep / Edit logic relies on this convention; do not introduce other forms like `{{...}}` / `$VAR`.
- **AI must surface ask; never auto-apply defaults; never auto-skip** — Step 0 (Language) / Step 2 (Round 1) / Step 3 (Round 2, when applicable) / Step 6 (Round 3) MUST surface `<ask tool>` even when sensible defaults exist. Defaults are `Recommended` options on the rendered ask, never AI-applied silently. Skip is a user choice never an AI shortcut. Step 5.4 (Inferred fills) is the only exemption — it is designed as deterministic AI-infer with no ask.
- **Single explicit Skip exemption — Round 3 Auto-scan fallback** — when the user picks `Auto-scan` for a Round 3 question (architecture.md or requirements.md) but the AI survey produces no actionable content for even one section, the AI may fall back to `Skip for now` behavior and print a transparency console line `[round-3] auto-scan produced no actionable content for <file>; falling back to _(none yet)_ marker.` This is the **only** AI-driven Skip path permitted; it does not generalise to other rounds.
- **Interruption preserves progress**: each fill value in Step 5 is written to disk immediately upon completion of the corresponding substitution, not deferred to batch.
