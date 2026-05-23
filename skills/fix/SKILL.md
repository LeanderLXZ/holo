---
name: fix
description: Post-audit triage handoff — read findings from the most recent `/post-check` / `/full-review` / `/check-review` (session context first, disk fallback) and triage each finding (H/M/L) and Open Question into a fix / todo / skip bucket; delegate the fix bucket to `/go` or `/do` (AI recommends per `/do`'s envelope rules: ≥ 3 files OR docs/ai_context touched → `/go`; else `/do`). Two top-level modes via `AskUserQuestion` (4 options, recommended first): Auto `/<recommended>` / Auto `/<other>` / Item-by-item / Exit. Auto applies AI recommendations only — "skip" and "todo" recommendations both drop, no automatic `/todo-add`; only the "fix" subset delegates. Item-by-item asks per finding (3 options shared with OQs: fix / todo / skip, recommended first), collects, summarises, then if the fix bucket is non-empty re-asks `/go` vs `/do` (3 options: Auto recommended / Auto other / Exit); todo bucket lands via `/todo-add` per item. Anti-over-engineering reminder embedded in the fix brief in both modes; no auto re-run of `/post-check` after fixes land. $ARGUMENTS = source slug / model keyword (optional; defaults to most recent in-session review, else latest on disk). Triggers: fix / fix it / triage findings / handle the review findings / /fix / fix after /post-check / fix after /full-review / fix after /check-review.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (logs / docs / commit messages / code comments / files written / fix brief composed for the delegated `/go` / `/do` discussion context) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / status lines / strategy declarations / per-finding summary table rendered in chat) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, and structural prefixes (`Step N:`, `H1`, `M1`, `L1`, `OQ1`, `REVIEWED-PASS`, etc.) stay English regardless.

# /fix — post-audit triage handoff

Triage findings from the most recent review surface — `/post-check`, `/full-review`, or `/check-review` — into three buckets (fix / todo / skip) and delegate the fix bucket to `/go` or `/do`. `/fix` does not modify code on its own; every landing is delegated. The discipline baked into this skill is that AI's recommended disposition is **only a starting position** — the user always picks (Auto = "accept all recommendations as a single bulk action"; Item-by-item = "decide per finding"). Open Questions (OQ) share the same 3-option schema with H/M/L findings.

**Discipline (anti-over-engineering, applies to both Auto and Item-by-item modes)** — before delegating, the fix brief handed to `/go` / `/do` always carries this paragraph verbatim:

> Anti-over-engineering reminder: post-review fixes — minimal patches only. No opportunistic refactor / "while I'm here" cleanup / new abstractions / new tests / new flags. If a 3-line edit solves it, do not extract helpers. Reviewers picked these findings precisely because they are worth fixing on their own — do not bundle adjacent rewrites unless the reviewer flagged them.

This reminder propagates the discipline of `/do` Step 1.0 (Dilution Self-Check) and `/go` Step 3 (no opportunistic doc edits) into the delegated round.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`.

The flow below is split into `## Step 0:` ~ `## Step 5:`.

**Before entering Step 0**: call **<progress tool>** to pre-register Step 0 ~ Step 5 (**one entry per parent Step**, `content` as `Step N: <sub-section title>`, all `status` = `pending`). Step 4 registers as a single entry `Step 4: triage dispatch (Auto or Item-by-item)` — 4a / 4b are mutually exclusive runtime branches, not separate entries; the chosen branch flips Step 4 `in_progress` then `completed`. This is a hard requirement — **do not proceed without calling <progress tool>**.

On entering each step: call **<progress tool>** to flip the current step to `in_progress` (in the same call, mark the previous step `completed`), then do the actual work. **Do not skip the call when crossing steps.** Progress is shown directly through the <progress tool> UI; **do not print progress lines like `[/fix] Step N: ...` in the conversation**.

Skipping a step: call **<progress tool>** to mark the corresponding entry `completed` directly, and print one line in the conversation `Step N skipped (reason: …)` — the "reason" is information the UI lacks, so keep this line; do not silently skip.

Final step done: call **<progress tool>** to mark the last entry `completed`.

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block before each state change. Semantic alignment: pre-register + flip state + mark complete.

**<ask tool> resolution**: Claude → `AskUserQuestion` (max 4 questions per call, batch beyond); other runtimes (no structured ask tool, e.g. Codex / Copilot agent mode) → enumerate questions + options per question in the response text and let the user answer in one pass (still max 4 per batch, batch beyond).

**<skill tool> resolution**: Claude → `Skill` (handoff to the named skill with `$ARGUMENTS` as the args field); other runtimes — print "User: please run `/go <slug>` next" (or `/do <slug>` / `/todo-add`) and let the user invoke manually. Semantic alignment: `/fix` writes the fix brief into conversation context first, then triggers the next skill so the receiving skill reads the brief as the discussion baseline.

## Step 0: Load skills config

`Read` `ai_context/skills_config.md`.

- File missing / any section header missing → fail loudly: print the missing items + prompt to complete per plugin template, stop
- Section content `(none)` or empty → skip the related steps for that section (treat as N/A in this project)
- Section lists concrete paths but the path does not exist → fail loudly: report the section drifting to a nonexistent path, stop and wait for the user to fix

Subsequent steps referencing "skills_config.md `## XX`" use this config. This skill uses:
`## Language` (L1 + L3 directives throughout — already loaded via the file header read),
`## Activity sources.Change logs.Path` + `Filename time pattern` (Step 1 disk fallback for `REVIEWED-*` change-log entries),
`## Activity sources.Review reports.Path` + `Filename pattern` (Step 1 disk fallback for `/full-review` outputs).

> **Language**: user-facing — render the language-axes anchor line below in `conversation_language` per `ai_context/skills_config.md §Language`. Axis values are echoed verbatim from §Language.

After reading, print one line **Language-axes anchor**: `Language axes: conversation_language=<value> · content_language=<value> (source: ai_context/skills_config.md §Language)`. Both axis values are echoed **verbatim** from the §Language section; the bracketed source path stays English; the natural-language prefix translates to `conversation_language` (rendered in the project's chosen language). This is a deliberate high-salience anchor planted before Steps 1–5 accumulate context.

## Step 1: Locate findings source

> **Language**: user-facing — render the "Selected findings source" line and the parsed finding-count summary in `conversation_language` per `ai_context/skills_config.md §Language`. Structural labels (`Selected findings source:`, `H={h} M={m} L={l} OQ={oq}`, file paths, finding IDs) stay English; the natural-language prefix and any rendered prose translate.

Resolution rule (three-tier; first non-empty wins):

1. **`$ARGUMENTS` slug / keyword match.** Treat `$ARGUMENTS` as either a slug or a model keyword:
   - Match against `<change_logs_path>/*.md` filenames (path per `skills_config.md ## Activity sources.Change logs`) — pick the most recent file whose filename contains the slug, then check it has a `## Review conclusion` writeback from `/post-check` (else reject)
   - Match against `<review_reports_path>/*.md` filenames (path per `skills_config.md ## Activity sources.Review reports`) — pick the most recent file whose filename contains the slug or model keyword (`claude` / `opus` / `sonnet` / `codex` / `gpt` follow the same alias rules as `/check-review` Step 0 / `## Activity sources.Review reports`)
   - Match against an in-session `/check-review` re-check output (no disk artifact; identified by the `Source Report:` line in the rendered output) — `$ARGUMENTS` slug treated as a substring against that source-report path
   - No match → fail loud listing the existing slugs / model entries under the two paths
2. **Most recent review surface in current session.** Scan the conversation context (most recent first) for any of these markers, take the most recent:
   - `/post-check` Step 6 output — identified by the `## Scope` / `## Track 1` / `## Track 2` heading sequence + the Step 5 writeback `LOG: <path>` echo printed in the same conversation
   - `/full-review` rendered output — identified by the `## Findings` / `## Alignment Summary` / `## Residual Risks` / `## Open Questions / Ambiguities` / `## Recommendations` heading sequence + the archive path echo
   - `/check-review` Step 4 output — identified by the `Source Report:` / `Per-Finding Review:` / `Proposed Execution Plan` heading sequence
3. **Disk fallback.** No in-session review surface found:
   - `ls -1t <change_logs_path>/*.md` and pick the most recent file that has a `## Review conclusion` section (search the body)
   - `ls -1t <review_reports_path>/*.md` and pick the most recent
   - Pick whichever has the newer mtime
4. **None.** No tier resolves → **fail loud**: print "no recent `/post-check` / `/full-review` / `/check-review` output found in this session or on disk; run one of those skills first, then `/fix`." and **stop the skill**.

After resolving, parse the source body and build the **findings table** in memory — one row per finding with these columns:

- **ID**: stable from the source (`H1`, `M2`, `L3`, `OQ1`, …). Renumber only if the source has no IDs (backfill in source order, note in the conversation "IDs backfilled this round"); never rename IDs that the source already issued
- **Severity bucket**: `High` / `Medium` / `Low` / `OQ` (Open Question)
- **File:line**: the evidence anchor cited by the finding (or `(no file anchor)` if the finding is repo-wide)
- **Description**: 1-sentence summary trimmed from the source
- **AI-recommended disposition**: `fix` / `todo` / `skip` / `unknown` — read from the source's "Recommendations" section if present (`/post-check` Step 6 §Recommendations, `/full-review` Output §Recommendations, `/check-review` Step 4 §Recommendations). Apply the following alias map when parsing the source's wording (the three upstream review skills emit non-uniform tokens; normalize them here):
  - `fix` ← `fix`
  - `todo` ← `todo` / `leave as todo` / `leave todo` / `park todo` / `park as todo` / `defer to todo` / `defer` (OQ surface wording)
  - `skip` ← `skip` / `skip — <reason>`
  - `adopt` (OQ-only) ← treated as `fix` for bucket-routing purposes (adopted OQ-answer joins the fix delegation brief; see Step 4b.1 for OQ-surface wording)
  
  After alias normalization: **if the source has no Recommendations section at all, or no recommendation for this specific ID, mark the disposition `unknown`** — do not infer a silent default; the user must see the gap

After resolving, **fail-fast on three empty conditions**:

- **No findings at all** (h+m+l+oq == 0, e.g. a `REVIEWED-PASS` log) → print `Selected findings source: <path>; no findings to triage. /fix exited.` and stop
- **`$ARGUMENTS` resolved via tier 1 but in-session has a more recent review** → print one extra transparency line: `Note: tier-1 ($ARGUMENTS) selected; in-session <type> at <path> would have been picked otherwise.`
- (other empty cases are caught downstream at Step 4)

Print one summary line:

`Selected findings source: <path or "in-session /post-check">; H={h} M={m} L={l} OQ={oq}; recommendations: fix={f} todo={t} skip={s} unknown={u}`

If `unknown > 0`, append one extra line: `⚠️ {u} findings have no AI-recommended disposition (source missing Recommendations section or entry); Auto modes will refuse to dispatch and force Item-by-item.`

## Step 2: Recommend `/go` vs `/do`

> **Language**: user-facing — render the recommendation line + the 1-sentence rationale in `conversation_language` per `ai_context/skills_config.md §Language`. Structural prefixes (`Recommended:`, file counts, the option names `/go` / `/do`) stay English; only the rationale prose translates.

Compute the AI's recommendation per `/do`'s envelope rules (single source of truth: see `skills/do/SKILL.md` Step 1.1):

- **≥ 3 distinct files implicated by the fix-recommended subset** (count the unique `File:line` anchors of every finding whose AI-recommended disposition is `fix`, plus any cross-file file the finding's description explicitly names) → recommend `/go`
- **Any fix-recommended finding's anchor lives under `docs/` or `ai_context/`** (and the discussion target is that file — not opportunistic) → recommend `/go`
- **Otherwise** → recommend `/do`

Print one line:

`Recommended: /go (or /do). Rationale: <one sentence — e.g. "fix subset touches 4 files across skills/ + docs/", or "fix subset is 2 files inside skills/ only, no docs/ai_context spillover">.`

Cache the recommendation as `<RECOMMENDED>` (and the other as `<OTHER>`) for Step 3 / Step 4.

## Step 3: Top-level mode dispatch (Auto / Item-by-item / Exit)

> **Language**: user-facing — render the `<ask tool>` prompt and option labels in `conversation_language` per `ai_context/skills_config.md §Language`. Structural prefixes (`/go` / `/do` / `Auto` / `Item-by-item`) stay English; only the surrounding prose translates.

**If `unknown > 0` (any finding without an AI-recommended disposition)**: Auto modes are unsafe (silent High-finding drops possible), so the 4-option ask is replaced with a 2-option `<ask tool>` — the user is **never** silently railroaded into Item-by-item without an Exit option.

Question: `{u} findings have no AI-recommended disposition (source missing Recommendations section or entry). Auto modes disabled. Choose how to proceed.`

Options (exactly two, recommended option first):

1. **Proceed to Item-by-item (recommended)** — proceed to Step 4b; decide each finding yourself
2. **Exit — drop the triage** — abort the skill, no delegation, no `/todo-add`; print `/fix exited; no actions taken` and stop

Otherwise (every finding has a known disposition), call **<ask tool>** with one question:

Question: `${h+m+l+oq} findings selected (fix={f} todo={t} skip={s}); recommended landing path: /<RECOMMENDED>. Choose how to proceed.`

Options (exactly four, recommended option first):

1. **Auto — apply AI recommendations via `/<RECOMMENDED>` (recommended)** — only findings recommended `fix` reach `/<RECOMMENDED>`; "todo" and "skip" recommendations both drop (no automatic `/todo-add` in Auto mode); fix brief carries the source review path + selected IDs + anti-over-engineering reminder; proceed to Step 4a
2. **Auto — apply AI recommendations via `/<OTHER>`** — same dispatch logic but delegates to `/<OTHER>` instead (user overrides AI's `/go` vs `/do` recommendation); proceed to Step 4a
3. **Item-by-item — decide each finding (and each OQ) myself** — proceed to Step 4b
4. **Exit — drop the triage** — abort the skill, no delegation, no `/todo-add`; print `/fix exited; no actions taken` and stop

## Step 4a: Auto path (recommended option / other option)

> **Language**: disk-bound — the fix brief composed here is disk-bound from the moment of composition (it becomes the discussion context for the delegated `/go` PRE log or `/do` discussion). Write the brief in `content_language` per `ai_context/skills_config.md §Language`. The user-facing wrapper prose around the brief (the "I will hand off the following brief to /go" lead-in line and the `Skill` invocation confirmation) translates to `conversation_language`; the brief content itself stays in `content_language`. Code identifiers, file paths, IDs stay English regardless.

Filter the findings table to keep only rows whose AI-recommended disposition is `fix`. Drop everything else (no `/todo-add` calls — Auto mode is "accept the recommendations, period").

If the filtered set is **empty** (AI recommended only `todo` / `skip` across the board): print one line `Auto mode found no findings recommended for fix; nothing to delegate. Dropped: {t} todo recommendations + {s} skip recommendations from this round. To register the "todo" recommendations explicitly, re-run /fix in Item-by-item mode.` and **stop the skill** (mark Step 4: completed).

Otherwise, compose the **fix brief** and write it into the conversation as a fenced code block:

```
Source review: <resolved source path> (Type: <GO|review_report|check-review-output>, status: <REVIEWED-PASS|REVIEWED-PARTIAL|REVIEWED-FAIL|n/a>)
Findings selected for fix: <comma-separated ID list, e.g. H1, H3, M2>
OQ resolutions (if any): <OQ1 resolved as "<AI's recommended answer>" | none>

Anti-over-engineering reminder: post-review fixes — minimal patches only. No opportunistic refactor / "while I'm here" cleanup / new abstractions / new tests / new flags. If a 3-line edit solves it, do not extract helpers. Reviewers picked these findings precisely because they are worth fixing on their own — do not bundle adjacent rewrites unless the reviewer flagged them.

Per-finding detail:
- H1 (<file:line>): <description trimmed from source>
- H3 (<file:line>): <description>
- M2 (<file:line>): <description>
- OQ1 (<file:line>): <description> — resolution: <answer>
```

Then invoke **<skill tool>** with the chosen target:

- Target = `<RECOMMENDED>` or `<OTHER>` (per Step 3 selection)
- `$ARGUMENTS` = `fix-from-<source-type>-<source-timestamp>` (e.g. `fix-from-postcheck-2026-05-23_094517`); source-type is `postcheck` / `fullreview` / `checkreview` derived from the resolved source's filename or render type; source-timestamp is the source's filename timestamp (or current timestamp if no filename)

Proceed to Step 5.

## Step 4b: Item-by-item path

> **Language**: user-facing — render the per-finding `<ask tool>` batches, the final summary table, and the optional re-ask for `/go` vs `/do` in `conversation_language` per `ai_context/skills_config.md §Language`. Finding IDs / file paths / option names (`/go` / `/do` / `/todo-add`) stay English; only the surrounding prose translates.

### 4b.1 Per-finding asks (batched, max 4 per call)

Iterate over the findings table in **source order** (preserving the source's H1, H2, …, M1, …, L1, …, OQ1, … sequence). For each finding, prepare one `<ask tool>` question with **exactly three options** (AI-recommended option first).

**For H/M/L findings**:

Question: `<ID> (<file:line>): <description trimmed from source>. <disposition-clause>. Choose disposition.`

Where `<disposition-clause>` is:
- `AI recommends: <fix|todo|skip>` when the disposition is explicit
- `AI recommendation: (none — pick yourself)` when the disposition is `unknown` (do NOT print "AI recommends: unknown" — it reads as if AI made a recommendation literally named "unknown")

Options (semantics for H/M/L):

1. **Fix — include in this round's delegated landing (`/go` or `/do`)**
2. **Add todo — register as `/todo-add` Next entry instead of fixing this round**
3. **Skip — do not fix, do not register**

**For Open Questions (OQ)** — adapt the wording to OQ semantics (the same 3-bucket schema, different surface):

Question: `<OQ ID>: <question text>. <suggestion-clause>. Choose disposition.`

Where `<suggestion-clause>` is:
- `AI suggests: "<suggested answer / candidate direction>"` when the source provided one
- `AI suggestion: (none — pick yourself)` when the disposition is `unknown`

Options (semantics for OQ):

1. **Adopt — accept AI's suggested answer and fold into this round's fix delegation**
2. **Defer to todo — register the open question as a `/todo-add` Discussing entry for later resolution**
3. **Skip — do not act on this OQ this round**

For both shapes, the order rule is: recommended option first, then the other two in `fix→todo→skip` (H/M/L) or `adopt→defer→skip` (OQ) precedence with the recommended one removed from the fixed precedence. When the disposition is `unknown` (no AI recommendation), the order falls back to the fixed precedence (fix/todo/skip or adopt/defer/skip).

Batch up to **4 findings per `<ask tool>` call** (the Claude `AskUserQuestion` hard limit); the same batch may mix H/M/L and OQ — do not split by severity. Repeat batches until all findings have been answered.

> **Language**: disk-bound — the per-finding result table that this sub-step collects is rendered to the user in 4b.2 (user-facing), but the same data is also referenced when composing the fix brief in 4b.3 (disk-bound) — so internally treat the structured data as language-neutral (raw IDs + file paths + disposition tokens); only the rendered presentation translates. Code identifiers, file paths, IDs stay English regardless.

### 4b.2 Summary table

After all batches are answered, print a summary table in chat:

| ID | Severity | File:line | AI rec | User pick |
|---|---|---|---|---|
| H1 | High | path:line | fix | fix |
| H2 | High | path:line | fix | todo |
| ... | ... | ... | ... | ... |

Below the table, print bucket counts:

`Fix bucket: N findings. Todo bucket: M findings. Skip bucket: K findings.`

### 4b.3 Branch on bucket emptiness

- **All three buckets empty** (impossible if user answered every batch — defensive guard) → print `no actions selected; exiting` and stop
- **Only the skip bucket non-empty** → print `all findings skipped; no actions to take; exiting` and stop
- **Fix bucket empty, todo bucket non-empty** → no `/go` / `/do` delegation; proceed to 4b.5 (todo handling) only
- **Fix bucket non-empty** → proceed to 4b.4 (re-ask `/go` vs `/do`)

### 4b.4 Re-ask `/go` vs `/do` (fix bucket only)

Re-compute the recommendation per Step 2's rules, but **against the user's fix bucket** (which may differ from AI's fix subset). Cache the result as `<RECOMMENDED_2>` / `<OTHER_2>`.

Call **<ask tool>** with one question:

Question: `Fix bucket contains N findings. Recommended landing path: /<RECOMMENDED_2>. Choose how to land.`

Options (exactly three, recommended first):

1. **Auto — land via `/<RECOMMENDED_2>` (recommended)** — compose fix brief from the fix bucket; invoke `Skill("<RECOMMENDED_2>")` with `$ARGUMENTS = fix-from-<source-type>-<source-timestamp>` (slug computed as in Step 4a)
2. **Auto — land via `/<OTHER_2>`** — same as above but delegate to `/<OTHER_2>`
3. **Exit — drop the fix bucket (also drop the todo bucket if any)** — abort, no delegation, no `/todo-add`; print `/fix exited; no actions taken` and stop

On option 1 / 2: compose the fix brief in the same format as Step 4a (Source review / Findings selected / OQ resolutions / Anti-over-engineering reminder / Per-finding detail) and invoke `Skill(...)`. Then proceed to 4b.5 for the todo bucket.

### 4b.5 Todo bucket — invoke `/todo-add` per item

When the todo bucket has > 1 item, print one pre-warning line before the first invocation:

`About to invoke /todo-add {N} times sequentially (one per todo-bucket finding); each invocation runs its own Step 5 preview ask — you will see {N} preview prompts in a row.`

Then, for each finding in the todo bucket, **before invoking `<skill tool>`, print a fenced context block** carrying the finding's metadata (so `/todo-add` Step 2 — which reads "from the last few turns of the current session" and is instructed "do not guess, do not stitch on the user's behalf" — can grab it cleanly without re-asking the user). The fenced block format:

```
Todo bucket item from /fix (source review: <path>):
- ID: <finding ID — H1 / M2 / OQ1 / etc.>
- File:line: <evidence anchor>
- Description: <one-line summary trimmed from source>
- Why registered as todo: <user's reason from 4b.1 pick, or "deferred per AI recommendation">
```

Then invoke **<skill tool>** with target = `todo-add` and `$ARGUMENTS = next` (OQs deferred to todo use `$ARGUMENTS = discuss` since they carry open decisions; H/M/L deferred to todo use `next`). The skill body of `/todo-add` will handle UPDATE-vs-CREATE semantic match per its own contract; the fenced block above becomes the canonical session-context Step 2 reads.

> **Important**: do NOT bypass `/todo-add` and write directly to `docs/todo_list.md`. The Index refresh + UPDATE-vs-CREATE semantic match + preview-and-confirm are part of `/todo-add`'s contract; bypassing them violates `ai_context/conventions.md §Cross-File Alignment` (row: "Skill bodies cite the section by name (`## Activity sources.<block>.<field>`)…").

If `/todo-add` for any item is cancelled by the user (per its Step 5 Cancel option), continue to the next item — do not abort `/fix`. After all todo items have been processed, proceed to Step 5.

## Step 5: Wrap-up

> **Language**: user-facing — render the wrap-up status line in `conversation_language` per `ai_context/skills_config.md §Language`. Structural prefixes (`✓`, `/go`, `/do`, `/todo-add`, source path) stay English; only the surrounding prose translates.

Print one line summarising what was handed off:

- **Auto path (Step 4a)**: `✓ /fix complete — handed off to /<RECOMMENDED|OTHER> with N findings; source review: <path>. Re-verification not auto-run — invoke /post-check yourself when the delegated round finishes if you need it.`
- **Item-by-item path with fix bucket non-empty (Step 4b.4 option 1 / 2)**: `✓ /fix complete — handed off to /<RECOMMENDED_2|OTHER_2> with N fix findings + registered M todo entries; source review: <path>. Re-verification not auto-run — invoke /post-check yourself when the delegated round finishes if you need it.`
- **Item-by-item path with only todo bucket (Step 4b.5 only)**: `✓ /fix complete — registered M todo entries; no fix delegation; source review: <path>.`
- **Item-by-item path with all-skip**: `✓ /fix complete — all findings skipped; no actions taken; source review: <path>.`

Do not invoke `/post-check` after fixes land — the user decides whether to re-verify (typical follow-up: run the delegated `/go` / `/do`, then optionally `/post-check` again). Do not commit, do not push, do not write to disk beyond the fix brief and the delegated-skill arguments.

## Constraints

- **No code changes by `/fix` itself**. Every landing is delegated to `/go` or `/do`; every todo registration goes through `/todo-add`; every audit re-run is the user's decision (re-invoke `/post-check` manually).
- **Auto mode drops "todo" recommendations**. By design — Auto mode is the bulk-accept path; users who want explicit todo registration pick Item-by-item.
- **OQ uniformity**. Open Questions share the same 3-option schema as H/M/L findings; do not split them into a separate ask round.
- **Anti-over-engineering reminder is mandatory**. Both Auto and Item-by-item paths embed the same fixed-text reminder paragraph in the fix brief; never omit.
- **Source-resolution failure is fail-loud**. If no review surface is found across all three tiers (arg / session / disk), stop with a hint — do not guess, do not pull findings from random commit messages.
- **Per-finding IDs are stable**. Reuse the source's `H1` / `M1` / `L1` / `OQ1` numbering verbatim; backfill only when the source has no IDs and note it explicitly; never rename.
- **The fix brief is the handoff contract**. The receiving `/go` reads it as its discussion baseline (Step 2 PRE log "Background / Trigger" cites it); the brief must always carry: source review path + finding IDs + anti-over-engineering reminder + per-finding detail.
- **No conversation-history rewriting**. `/fix` reads what the review skills already produced; do not re-render the original review report inside `/fix`'s output (that is the source skill's job and the user has it scrolled up).
