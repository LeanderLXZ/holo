---
name: update-docs
description: Land conversation narrative into `ai_context/` + `docs/` files — semantic match decides which file + section each just-discussed point belongs to, composes patches that respect the PROGRESSIVE marker contract (`_(none yet — delete this marker once content is added)_` line removed in the same pass when first content lands), surfaces lockstep pairs from `ai_context/conventions.md §Cross-File Alignment`, previews every patch in one batched `<ask tool>` (Confirm / Tweak first / Cancel), applies on confirm, reminds user to run `/commit` to persist. $ARGUMENTS = optional focus (file path / section name / topic keyword) to narrow candidate selection. No commit / no push / no code / no schema / no fan-out / no multi-agent review / no PRE-POST log — patches outside `ai_context/` + `docs/` are rejected. Sibling of `/todo-add` for prose instead of todo entries. Triggers: /update-docs / update docs / record discussion in ai_context / land blueprint into ai_context / land discussion into docs.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (patch content written into `ai_context/` + `docs/` files, marker-line removals, the trailing reminder appended to the conversation if redirected to a file) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / candidate file list rendered in chat / patch preview wrappers / final changed-files summary line) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, section headings (`## §6`, `### [T-XXX]`), and structural prefixes (`Step N:`, `PATCH:`, etc.) stay English regardless.

# /update-docs — Land conversation narrative into `ai_context/` + `docs/`

Take what the user just discussed in the session and land it as patches
to the corresponding `ai_context/` + `docs/` files. Lightweight sibling
of `/go` for **doc-only narrative authoring**: no PRE/POST log, no
multi-agent review, no commit, no fan-out. Sibling of `/todo-add` for
**prose content** instead of single todo entries.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`.

The flow below is split into `## Step 0:` ~ `## Step 3:`.

**Before entering Step 0**: call **<progress tool>** to pre-register all of Step 0 ~ Step 3 (one entry per step, `content` = `Step N: <sub-section title>`, `status` = `pending` for all). This is a hard requirement — **do not proceed without calling <progress tool>**.

Each time you enter a step: call **<progress tool>** to flip the current step to `in_progress` (mark the previous step `completed` in the same call), then do the real work. **Do not skip the call across step boundaries**. Progress is rendered directly by the <progress tool> UI — **do not print `[/update-docs] Step N: ...` style progress lines in the conversation**.

Skipping a step: call **<progress tool>** to mark the entry directly `completed`, and print one line `Step N skipped (reason: …)` in the conversation — "reason" is information the UI lacks, keep that line; do not silently skip.

Final step completion: call **<progress tool>** to mark the last entry `completed`.

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block on every state change. Semantic alignment: pre-register + flip state + mark complete.

**<ask tool> resolution**: Claude → `AskUserQuestion` (max 4 questions per call, batch beyond); other runtimes (no structured ask tool, e.g. Codex / Copilot agent mode) → enumerate questions + options per question in the response text and let the user answer in one pass (still max 4 per batch, batch beyond).

## Step 0: Load skills_config

`Read` `ai_context/skills_config.md`.

- File missing / any section header missing → fail loudly: print the missing items + prompt to complete per plugin template, stop
- Section content `(none)` or empty → skip the related steps for that section (treat as N/A in this project)
- Section lists concrete paths but the path does not exist → fail loudly: report the section drifting to a nonexistent path, stop and wait for the user to fix

This skill uses:
`## Language` (drives `content_language` for patch content + `conversation_language` for user-facing surface; the L1 directive at top of this file already routes both buckets).

## Step 1: Identify candidate files + compose patches

> **Language**: disk-bound — patch content composed here will land in `ai_context/` + `docs/` files at Step 3 and is therefore disk-bound from the moment of composition. Write the patch text (paragraph additions, marker-line removals, list entries, table rows, decisions log entries) in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names, section headings (`## Goal`, `### [T-XXX]`, `**Updated**`), and the PROGRESSIVE marker token `_(none yet — delete this marker once content is added)_` stay English regardless. The Step 2 preview wraps the patch in user-facing prose — wrapper prose translates to `conversation_language`; patch content stays in `content_language`.

> **Language**: user-facing — render the "candidate files" list printed to the conversation (file path + section + one-line patch summary, no patch body yet) in `conversation_language` per `ai_context/skills_config.md §Language`. Structural labels (`file:`, `section:`, `add:` / `replace:` / `remove marker:`) stay English; only the summary prose translates.

> **Compactness Requirements**: patches landing in `ai_context/` follow the universal contract —
> - Shorter is better than longer. Each entry is a summary, not a detail dump.
> - Compactness must not sacrifice accuracy or completeness — never drop important information just to fit the length target.
> - Aim for ≤ 5 lines and push longer detail to the linked source (`docs/<topic>.md`, schemas, script docstrings).
> - Do not compress or touch content unrelated to the current edit.

Scan the recent conversation turns and identify "what the user just decided / discussed that should land as narrative." For each candidate point:

1. **Semantic match against `ai_context/` + `docs/` files.** Map the topic to its natural home:
   - project goal / scope / stakeholders → `ai_context/project_background.md` + matching `docs/` section if present
   - current state snapshot → `ai_context/current_status.md`
   - architecture decisions → `ai_context/architecture.md` + `docs/architecture/<topic>.md`
   - durable engineering decisions ("why" rationale) → `ai_context/decisions.md` (append entry; do **not** renumber)
   - user-visible requirements → `docs/requirements.md` (long-form) + `ai_context/requirements.md` (summary line) — lockstep pair
   - planned-but-unfinished tasks → **redirect to `/todo-add`**, this skill does not touch `docs/todo_list.md`
   - mental model / quick-start / user-cares / operational commands → `ai_context/handoff.md`
   - roadmap / next directions → `ai_context/next_steps.md`

2. **Cross-file alignment surfacing.** Consult `ai_context/conventions.md §Cross-File Alignment` and surface any lockstep pairs touched by the candidate (e.g. `docs/requirements.md` + `ai_context/requirements.md`; `docs/architecture/<topic>.md` + `ai_context/architecture.md`). Patch each member of the pair, not just one side. When the alignment table absent, judge by intuition — the canonical pairs above are the ones that recur.

3. **PROGRESSIVE marker awareness.** When the target section currently carries the line `_(none yet — delete this marker once content is added)_`, the patch removes that marker line in the same pass as the first content lands. Do not leave both marker + new content side-by-side. (Source of truth for the marker contract: `ai_context/decisions.md` §Skill Implementation #15.)

4. **Out-of-scope rejection.** Patches that touch any of the following are **rejected** — print a one-line redirect and skip the candidate:
   - `docs/todo_list.md` / `docs/todo_list_archived.md` → use `/todo-add`
   - code (`commands/` / `skills/` / `hooks/` / `scripts/` / `templates/` / `.claude-plugin/`) → use `/go`
   - schema / config (`ai_context/skills_config.md` headers/fields, `.gitignore`, `plugin.json`) → use `/go` (or `/holo:update --fix` for drift)
   - `logs/change_logs/` / `logs/review_reports/` → owned by `/go` and `/full-review` respectively
   - any path outside `ai_context/` + `docs/`

5. **Compose patches.** For each accepted candidate, draft the exact patch text in `content_language`. Use the same field-label / heading conventions as the surrounding file. For `decisions.md` append: number = previous max + 1 (do not renumber existing entries); for `requirements.md` lockstep: long-form + summary line in matching numbering. For `handoff.md` bulleted sections: append bullets in alphabetical / logical order. For appended content: 1 blank line before the new block; for marker-line removal: remove the single marker line plus its trailing blank line if present.

If `$ARGUMENTS` is provided, treat it as a focus filter (file path / section name / topic keyword) and narrow candidates to those matching the filter; do not broaden beyond the user's stated focus.

If after the scan + filter the **accepted** candidate set is empty (no in-scope topics found, or all candidates were rejected per §4), print one line `nothing to land — recent conversation has no in-scope narrative for ai_context/ + docs/; if you expected a patch, name the topic explicitly and re-invoke` and stop. Do not enter Step 2.

Print to the conversation a numbered candidate list — one line per patch — in this shape:

```
1. file: ai_context/handoff.md → section: ## Mental Model → add: <one-line summary>
2. file: ai_context/decisions.md → append: §<bucket> #<N> <one-line summary>
3. file: docs/requirements.md + ai_context/requirements.md (lockstep) → §6.2 + bullet 6 → add: <one-line summary>
4. ... (rejected) file: docs/todo_list.md → redirect to /todo-add
```

Do not print the full patch bodies yet — that is Step 2's preview.

## Step 2: Preview + single batched `<ask tool>`

> **Language**: user-facing — render the preview wrapper (the lead-in prose, the per-patch header lines like "patch 1/3: …", the trailing reminder of out-of-scope rejections from Step 1) in `conversation_language` per `ai_context/skills_config.md §Language`. Patch bodies **shown inside** the wrapper are disk-bound — they stay in `content_language` (the language they will land in at Step 3); do not retranslate.

> **Language**: user-facing — render the `<ask tool>` prompt and option labels in `conversation_language` per `ai_context/skills_config.md §Language`. File paths, section headings, and entry IDs quoted inside the prompt / labels stay English; only surrounding prose translates.

Print every accepted patch in full, each block headed with `patch N/M: <file> → <section>`. After all patches are printed, ask via **<ask tool>** — one question, three options:

Question: `Apply all <M> patches as previewed?`

1. **Confirm — apply all patches as shown (recommended)** — proceed to Step 3
2. **Tweak first — adjust wording / drop a patch / add a patch** — wait for the user's tweak instruction, recompose draft, re-enter Step 2
3. **Cancel — drop all patches** — abort the skill, no write

The `<ask tool>`'s auto-appended "Other" fallback covers free-form responses (e.g. "apply patches 1 and 3, drop 2"). Option labels stay concise.

**Tweak-first lockstep self-check** (run on every recompose, before the next preview cycle prints): after applying the user's tweak instruction (drop / wording change / add a patch), re-walk the resulting accepted-patch set against `ai_context/conventions.md §Cross-File Alignment`. If any lockstep pair (e.g. `docs/requirements.md` + `ai_context/requirements.md`; `docs/architecture/<topic>.md` + `ai_context/architecture.md`) has been broken — one half present in the set, the other half dropped — surface a `⚠️ lockstep break:` warn block at the top of the next preview citing the affected pair, **and replace the cycle's third option (`Cancel`) with `Resolve lockstep break (pair: <file A> + <file B>)`**. Picking this option opens one follow-up `<ask tool>` (3 options): `1. Also drop the orphaned <other half> to keep the pair intact (recommended)` / `2. Restore the dropped <half> to keep the pair intact` / `3. Cancel — drop all patches`. This keeps the main cycle at 3 options (Confirm / Tweak first / Resolve lockstep break) while still honoring the AskUserQuestion 4-option-max-per-question contract. Do not silently apply either lockstep fix — the user's intent on lockstep is load-bearing per `## Constraints` and must be confirmed.

**No file is written before user confirmation.**

## Step 3: Apply patches + remind to commit

> **Language**: disk-bound — patches landed into `ai_context/` + `docs/` files are written in `content_language` per `ai_context/skills_config.md §Language`.

> **Language**: user-facing — render the changed-files summary line ("✓ landed N patches across M files: …") and the trailing reminder ("This skill does not commit. To persist, run /commit.") in `conversation_language` per `ai_context/skills_config.md §Language`. Structural prefixes (`✓`, file paths) stay English; only surrounding prose translates.

After confirmation:

a. **Apply patches via `Edit` (or `Write` only when creating a brand-new file under `ai_context/` or `docs/`).** One `Edit` per patch — do not batch unrelated edits into a single `replace_all`.

PROGRESSIVE marker removal — two explicit branches (do not collapse them):

- **Branch A — marker followed by a blank line then next content** (typical when the marker is mid-section and another `## NextSection` or paragraph follows after the blank): `old_string` covers the marker line **plus the one blank line** immediately following it; `new_string` is the new content block (which itself ends with its own trailing newline structure, so the visual spacing between the new block and the next section is preserved).

  Example — marker `_(none yet — delete this marker once content is added)_` followed by blank line then `## NextSection`:

  ```
  ## ThisSection

  _(none yet — delete this marker once content is added)_

  ## NextSection
  ```

  → `old_string` matches `_(none yet — delete this marker once content is added)_\n\n` (marker + blank). `new_string` is the new content block ending with `\n\n` so the final state is `## ThisSection\n\n<new content>\n\n## NextSection`.

- **Branch B — marker followed directly by next content with no blank line** (rarer; happens when the section is terse and the marker abuts the next heading): `old_string` covers **only the marker line**, no blank consumed; `new_string` is the new content block ending with its own `\n` so the next section still starts on its own line.

  Example:

  ```
  ## ThisSection
  _(none yet — delete this marker once content is added)_
  ## NextSection
  ```

  → `old_string` matches `_(none yet — delete this marker once content is added)_\n` (marker only). `new_string` is the new content block ending with `\n` so the final state is `## ThisSection\n<new content>\n## NextSection`.

Pick the branch by **first inspecting the literal bytes around the marker in the target file** (via `Read` or by reusing what was read in Step 1); do not guess. Wrong branch → either two consecutive blank lines (Branch A applied to a Branch-B case) or two headings glued together with no separator (Branch B applied to a Branch-A case).

b. **Verify by re-reading the changed sections** if a patch touched > 1 surrounding line (sanity check that the surrounding context still parses as intended). Do not re-read entire files — only the affected section.

c. **Print the summary line**: `✓ landed N patches across M files: <comma-separated file list>`.

d. **Print the reminder**: `This skill does not commit. To persist, run /commit.` (Do not invoke `/commit` automatically.)

Do not enter `/go`, do not invoke any other skill, do not stage or commit any change.

## Constraints

- **No commit / no push** (persistence delegated to `/commit`)
- **No code / no schema / no config / no logs / no todo_list** — patches outside `ai_context/` + `docs/` are rejected with a one-line redirect to the right skill (`/go` for code/schema/config, `/todo-add` for todo entries)
- **No fan-out / no multi-agent review** — single-pass author-and-write; `/full-review` is the audit path
- **No PRE / POST log** — `logs/change_logs/` is `/go`-only; `/update-docs` writes are attributable via the git diff alone
- **PROGRESSIVE marker contract is load-bearing** — when first content lands into a `_(none yet — delete this marker once content is added)_` section, the marker line is removed in the same pass; never leave marker + new content side-by-side
- **Lockstep pairs are batched** — when `docs/requirements.md` + `ai_context/requirements.md` (or any pair from `ai_context/conventions.md §Cross-File Alignment`) are both touched, both members are patched in this run; the user is not asked to choose between them
- **No silent file creation outside `ai_context/` + `docs/`** — `Write` is used only to create a brand-new file under those two roots (rare — typically a new `docs/architecture/<topic>.md`); even then the file must be one of the documented kinds in `ai_context/conventions.md`, not an arbitrary scratch file
