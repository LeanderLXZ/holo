---
name: post-check
description: Focused review after /go — two tracks in parallel: track 1 uses the PRE log to reconcile the planned action list + validation criteria; track 2 expands to files outside the plan to find cross-file conflicts / ambiguity / bugs / inconsistencies. Mandatory loading of the latest PRE log under logs/change_logs/ as the intent baseline; may dispatch sub-agents in parallel to run the spec / implementation / artifact lines. $ARGUMENTS = log slug (defaults to latest). Report printed + summary written back to log; aside from the log summary, read-only, no code changes / no commits. Full-repo review → /full-review. Triggers: re-confirm this change / after-check / review after /go completes / post-check.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (logs / docs / commit messages / code comments / files written) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / status lines / strategy declarations / findings rendered in chat) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, and structural prefixes (`Step N:`, `LOG:`, `H1:`, `REVIEWED-PASS`, etc.) stay English regardless.

# /post-check — focused review after /go

Run a focused review of **this change set**, two tracks in parallel: **track 1 — original requirement fulfillment** (reconcile the planned action list + validation criteria from the PRE log), **track 2 — impact spread / unplanned side effects** (expand to files outside the plan to find conflicts / bugs / ambiguity / inconsistencies). **Sub-agents may run scans in parallel**.

This is not a full-repo review (that is `/full-review`); it only targets the details touched by this `/go`. If `$ARGUMENTS` is present, use it as an exact slug match for this round's log file; otherwise pick the most recent file under `logs/change_logs/` by filename timestamp as the intent baseline.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`.

The flow below is split into `## Step 0:` ~ `## Step 7:` (including sub-step `## Step 1.5:`).

**Before entering Step 0**: call **<progress tool>** to pre-register Step 0 / Step 1 / Step 1.5 / Step 2 ~ Step 7 (one entry per step, `content` as `Step N: <sub-section title>`, all `status` = `pending`). This is a hard requirement — **do not proceed without calling <progress tool>**.

On entering each step: call **<progress tool>** to flip the current step to `in_progress` (in the same call, mark the previous step `completed`), then do the actual work. **Do not skip the call when crossing steps.** Progress is shown directly through the <progress tool> UI; **do not print progress lines like `[/post-check] Step N: ...` in the conversation**.

Skipping a step: call **<progress tool>** to mark the corresponding entry `completed` directly, and print one line in the conversation `Step N skipped (reason: …)` — the "reason" is information the UI lacks, so keep this line; do not silently skip.

Final step done: call **<progress tool>** to mark the last entry `completed`.

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block before each state change. Semantic alignment: pre-register + flip state + mark complete.

## Step 0: Load skills config

`Read` `ai_context/skills_config.md`.

- File missing / any section header missing → fail loudly: print the missing items + prompt to complete per plugin template, stop
- Section content `(none)` or empty → skip the related steps for that section (treat as N/A in this project)
- Section lists concrete paths but the path does not exist → fail loudly: report the section drifting to a nonexistent path, stop and wait for the user to fix

Subsequent steps referencing "skills_config.md `## XX`" use this config. This skill uses:
`## Example artifact directories` (track 2 artifact-structure line),
`## Sensitive content placeholder rules` (track 2 residue check),
`## Data contract directories` (Step 3 spec-line data contract scan; includes JSON Schema / proto / OpenAPI / Pydantic / SQL DDL etc.).

## Step 1: Scope this change

> **Language**: user-facing — render the scope print line and the language-axes anchor below in `conversation_language` per `ai_context/skills_config.md §Language`. Structural labels (`Review scope:`, `Language axes:`) translate to their `conversation_language` equivalent if natural; commit SHAs / file paths / axis values stay verbatim.

- `git log --oneline -n 10` + `git status` to determine the commit range produced by `/go` (typically the latest 1–N); if changes are uncommitted, use the working-tree snapshot
- `git diff <base>..HEAD --stat` (or `git diff --stat`) to list files touched this round, as the "must review" file set
- Print explicitly two lines in succession:
  - **Scope line**: `Review scope this round: commits {X..Y} (or working tree), N files`. Natural-language portion translates to `conversation_language`.
  - **Language-axes anchor line**: `Language axes: conversation_language=<value> · content_language=<value> (source: ai_context/skills_config.md §Language)`. Both axis values echoed verbatim from §Language read in Step 0; the natural-language prefix translates to `conversation_language` (rendered in the project's chosen language). This anchor is planted before the parallel sub-agent fan-out in Step 3.

## Step 1.5: Load intent baseline (mandatory)

- `$ARGUMENTS` provides a slug → exact match against `logs/change_logs/*_{slug}.md`; otherwise pick the most recent file under `logs/change_logs/` by filename timestamp
- **Type-field gate**: read the file header for a `- **Type**:` line.
  - `Type: DO` → this is a `/do` single-segment log; `/post-check` does not apply (no PRE phase by design). Print "log `<path>` is `Type: DO` (`/do` single-segment); `/post-check` targets `Type: GO` only — stopping. For a `/do` change review, scan the diff manually or upgrade the next round to `/go`." and **stop the skill**.
  - `Type: GO` → continue to PRE-section read below.
  - `Type` field missing (pre-contract log predating the Type-field rollout) → assume `GO` and continue (per `ai_context/conventions.md §Logging` "no backfill" rule, missing Type does NOT abort).
- Read the PRE section: **Background / Trigger**, **Conclusion and decisions**, **Planned action list**, **Validation criteria**, **Execution deviations**
- Print: "intent baseline: `logs/change_logs/{...}.md`" + a structured summary of the PRE section
- Log missing or has no PRE section → print "⚠️ intent baseline missing; skipping track 1, running only track 2" and continue

## Step 2: Cross-File Alignment consult

> **Language**: disk-bound — write this track 1 findings list (folded into log writeback at Step 5) in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names stay English regardless.

Read the Cross-File Alignment table in `ai_context/conventions.md`; for each dimension touched this round (requirements / schema / prompt / code / architecture / ai_context / README / directory structure), list the file set that **should have been changed together**. This set feeds both track 1 (reconcile Missed Updates) and track 2 (spread starting points).

When the table does not exist: skip the reconcile input from this step, track 1 reconciles only the PRE plan list against the actual diff (Missed Updates degrades to the subset "listed in PRE but not changed"), track 2 spread starting points use only the files touched by this diff + upstream/downstream references.

## Step 3: Parallel sub-agent dual-track audit lines

> **Language**: disk-bound — write this track 2 findings list (folded into log writeback at Step 5) in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names stay English regardless.

> **Language (sub-agent dispatch)**: when spawning sub-agents at this step, the parent MUST inject the language axes into each sub-agent's prompt explicitly. Include verbatim: "Reply in `conversation_language`=`<value>`; write any disk artifacts in `content_language`=`<value>`; both values from `ai_context/skills_config.md §Language`." Sub-agents do not inherit the parent's language config — they must be told. Sub-agent report-back to the parent is a USER surface; its on-disk findings folded into the log are DISK surface. **Place this injection at the end of the sub-agent prompt** (recency-favorable position), not in the header / middle — sub-agents have just read English source files in their scan scope, so the dispatch directive needs recency advantage over the scanned content to keep the reply in `conversation_language`.

> **Track vs. line**: a **track** is an audit perspective (track 1 reconcile / track 2 spread, 2 total); a **line** is the scan division (file-domain sliced sub-agents, 4 total). The two are orthogonal — each line runs both tracks simultaneously.

For small change surface, run serially in a single line; across modules or layers, dispatch sub-agents in parallel — four lines each carry both tracks:

1. **Spec line**: `docs/requirements.md` / `docs/architecture/` / `ai_context/` / directories listed in skills_config.md `## Data contract directories` (skip scan when `(none)`) / the prompt-sources path from skills_config.md `## Activity sources.Prompt sources.Path` (skip when `(none)`) — descriptions vs. this change consistent; any residual old descriptions / old fields / old flows
2. **Implementation line**: code changed this round + its upstream / downstream (callers / callees / importers) — field names / params / return values / state machines / gates / exception paths still coherent; do imports still run
3. **Risk line**: code changed this round + related code dragged along (callers / callees / shared state / shared data flow) — boundary conditions, null / None, exception paths, concurrency, retry / rollback, error handling hiding bugs; do new behaviors introduce data loss / security holes / performance regressions; do state machines / gates / invariants have missed branches. **Distinct from implementation line**: implementation line asks "does it still hook up" (signatures / imports / upstream-downstream consistency); risk line asks "is what it does correct" (semantic correctness + failure modes); outputs go to Step 4 "bug / behavior risk" and the same-named subsection of the Step 6 report
4. **Artifact and structure line**: did this round affect samples under directories listed in skills_config.md `## Example artifact directories`, related README displays, directory structure; if directories or filenames changed, trace all reference points. Skip this line when the section is `(none)` / empty

> **Each dispatched sub-agent must re-read the intent baseline PRE log first**: stuff the log path Step 1.5 read into its prompt and **explicitly require it to read the PRE "Conclusion and decisions / Planned action list / Validation criteria / Execution deviations" before starting**, then scan the scope of this line. Sub-agents have independent context; without enforced PRE reading they will spin only on the brief in the prompt, easily drifting from this round's intent; both reconcile and spread judgement must be anchored in the PRE log.

Each line produces: **track 1 reconcile result** (PRE plan items × actual change cross-check) + **track 2 findings** (issues in files outside the plan, with file + line, direct evidence vs. inference).

## Step 4: Key checks (only for this change)

> **Language**: disk-bound — write this dual-track findings aggregation (folded into log writeback at Step 5) in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names stay English regardless.

- **Cross-file inconsistency**: do the same field / concept in schema / code / docs / prompt match in naming and definition
- **Ambiguity**: do requirements / architecture descriptions of new behavior admit two readings
- **Conflict**: do "docs say A, code does B, samples say C" emerge
- **Residual old logic / legacy wording**: any paragraphs describing the old flow, replaced fields, dead imports, dead branches; also check the docs / prompts / ai_context touched this round for real content violating skills_config.md `## Sensitive content placeholder rules`, or `old / legacy / deprecated / formerly` wording
- **Dangling references / over-deletion**: if this diff deleted a symbol / file / section, grep the rest of the repo to see if references remain un-updated; this is the inverse of "residual old logic" — the old target is gone but the old reference stays
- **change_log / docs internal-link breakage**: this round's log or modified docs reference `decisions.md #25` / `[xxx](path)` / `see logs/change_logs/.../X.md` etc.; verify the numbers have not drifted, relative paths exist, anchors are real
- **todo_list drift**: if this round materially completes a todo entry (PRE log "Completion criteria" section says "this todo entry moves to archived", or the diff equals the "change list" of some Next/Discussing entry), check whether the TODO list (path per `skills_config.md ## Activity sources.TODO list.Path`, typically `docs/todo_list.md`) has moved the entry wholesale into the archived TODO list (path per `## Activity sources.Archived TODO list.Path`, typically `docs/todo_list_archived.md`) `## Completed` + whether the Index section has been refreshed in sync. Missed move → add to Missed Updates
- **bug / behavior risk**: will new code crash under boundary / null / exception paths; state machines / gates / retry / rollback have holes
- **README / directory structure**: are added / deleted / renamed files synced to the relevant README and directory descriptions
- **ai_context drift**: have durable decisions this round landed in `ai_context/decisions.md` / `current_status.md` / `next_steps.md`; does handoff need updating
- **commit message vs diff match**: commit body description vs `git diff --stat` actual changes — do they cover each other; body lists N items but diff only touches M, or diff changed files the body did not mention

> After Step 3 / Step 4 run, hold the dual-track conclusions (plan-item fulfillment status, Findings list, Missed Updates, Open Questions, Residual Risks) **in your head / notes**, do not print immediately. Step 5 writes back a structured summary to the log + commit; Step 6 then expands the full report into the conversation — this way the full report is the last segment of `/post-check` output, the user reads it and decides without scrolling back.

## Step 5: Write back log (summary) + commit

> **Language**: disk-bound — write this review summary appended to the change log + REVIEWED-* verdict in `content_language` per `ai_context/skills_config.md §Language`. The verdict label `REVIEWED-PASS` / `REVIEWED-PARTIAL` / `REVIEWED-FAIL` stays English verbatim (structural). The commit message follows `content_language`. Code identifiers, file paths, field names stay English regardless.

Append the **structured summary** of the dual-track conclusions to the **intent baseline log file** (the one Step 1.5 read), **without duplicating the full Findings text** (the full text goes to Step 6 in the conversation to avoid log file bloat):

```markdown
<!-- /post-check writes -->

## Review conclusion (full report in conversation)

### Track 1 — requirement fulfillment
- Fulfillment rate: {M/N plan items + K/L validations}
- Missed updates: {X} items (see conversation)

### Track 2 — impact spread
- Findings: High={h} / Medium={m} / Low={l}
- Open Questions: {q} items (see conversation)

## Review state
- **Reviewed**: {timestamp}
- **Status**: REVIEWED-PASS | REVIEWED-PARTIAL | REVIEWED-FAIL
  - PASS = track 1 fully landed AND track 2 has no High/Medium
  - PARTIAL = track 1 has gaps OR track 2 has Medium, no High
  - FAIL = track 1 largely unlanded OR track 2 has High
- **Conversation ref**: /post-check output in this session
```

Log missing: print "⚠️ no log to write back; review conclusion kept only in conversation" and **go directly to Step 6** (no commit to make).

After writing back, **immediately commit this log file** — do not leave it as a dirty working tree; otherwise the next `/go` Step 1 question would fold this residue into the dirty summary, forcing the user to choose among WIP commit / direct execute / worktree / stash for no benefit.

- commit on the **current branch** (`/post-check` runs on the user's current branch, no switching needed)
- only `git add` this log file — do not opportunistically include unrelated dirty files in the commit
- commit message style follows existing precedent: `log({slug}): /post-check review writeback REVIEWED-PASS|PARTIAL|FAIL`
- no push, no branch switch; immediately enter Step 6 after commit

When log is missing (no writeback), skip the commit.

## Step 6: Print full dual-track report in conversation

> **Language**: user-facing — render the full dual-track report (Scope / Track 1 / Track 2 / Findings list / Alignment Summary / Residual Risks / Open Questions / Recommendations) in `conversation_language` per `ai_context/skills_config.md §Language`. Markdown section headings, table column labels, and structural prefixes (`H1`, `M1`, `L1`, `OQ1`, `Missed Updates`, etc.) stay English; only finding descriptions / evidence / recommendation prose translate.

> **Language anchor reset (render-time)**: before emitting the report below, re-echo the language axes verbatim — `conversation_language=<value>` · `content_language=<value>` from `ai_context/skills_config.md §Language`. Step 5 just wrote a substantial `content_language`-bound block to disk (log writeback + commit message); this reset refreshes recency at the entry of the USER-facing render so the dual-track report below stays in `conversation_language` even when the template's structural scaffold (Markdown headings + table column labels + ID prefixes) is largely English.

**This is the primary surface for the user's decision; all Findings / Missed Updates / Open Questions print fully into the conversation**, no omissions, no summary-only. **This is the last substantive segment `/post-check` produces in the conversation** — placed after log writeback, the user reads the report and decides without scrolling back.

Markdown template:

```markdown
## Scope
- commits {X..Y} (or working tree), N files
- intent baseline: `logs/change_logs/{...}.md` (or "missing")

---

## Track 1 — original requirement fulfillment (reconcile)

Item-by-item check against the PRE log's "Planned action list + Validation criteria":

| Plan item | Status | Evidence |
|-----------|--------|----------|
| {file A: change focus} | ✅ landed | {diff summary / line numbers} |
| {file B: change focus} | ⚠️ partial | {missing X} |
| {file C: change focus} | ❌ not landed | {file not touched} |
| {validation 1} | ✅ pass | {command output summary} |
| {validation 2} | ❌ fail | {error summary} |

**Missed Updates** (reconcile delta ∪ Cross-File Alignment delta):
- {file path — why it should have been synced but was not}

When intent baseline is missing: **skip this track** and print "no PRE log, cannot reconcile".

---

## Track 2 — impact spread / unplanned side effects

Starting from the intent-scoped set, expand to files **outside the plan**:

### Findings

**All findings must carry a numbered ID** — within the same priority, increment from 1 (`H1` / `H2` / `H3`...; `M1` / `M2`...; `L1` / `L2`...). Subsequent conversation / `/go` / `/check-review` references to a finding **must use this ID**; once issued the numbers do not renumber (even on merge / cancel, the original ID stays as a placeholder → "(withdrawn)" or "(merged into H1)"; do not rename H3 to H2).

- **H1** `{file:line}` — {conflict / bug / ambiguity description} — evidence / inference
- **H2** `{file:line}` — ...
- **M1** `{file:line}` — ...
- **L1** `{file:line}` — ...

### Cross-file conflicts
- "docs say A, code does B, samples say C" style findings

### Residual old logic / legacy wording
- {location + line numbers}

### bug / behavior risk
- {boundary, null, exception path, state-machine holes}

### README / directory / ai_context drift
- {drift points}

---

## Alignment Summary
This round's alignment status across requirements / schema / code / README / architecture / ai_context / prompts / directories; which layer is least aligned

## Residual Risks
{not yet confirmed bugs but worth caution}

## Open Questions
{points the repo cannot resolve on its own and need the user to decide; each comes with candidate directions}

## Recommendations

**For reference only; user decision takes priority**. Before each recommendation, pass the three-question self-check:

1. **Necessary?** — what happens if not fixed? Just looks off / OCD → lean "skip" or "leave as todo"
2. **Can it be simpler?** — if 3 lines fix it, do not extract helpers / add layers / add config / add flags
3. **Out of scope?** — is the opportunistic "related fix" spilling out of this round's goal

- **{H1/M1/L1}** → recommend {fix / leave as todo / skip}: {one-sentence reason / recommended approach}
- **OQ1** → recommend {candidate A/B}: {one-sentence reason}
- ...
```

## Step 7: Wait for confirmation

> **Language**: user-facing — render the closing "awaiting your call" short line in `conversation_language` per `ai_context/skills_config.md §Language`. One short sentence at most; do not produce additional summary / recommendations / next-step lists.

After the full report prints, **stop**. At most add one more sentence like "awaiting your call" or a similarly very short closing line, **do not write further summaries, do not commit further, do not list next steps** — any tail pushes the dual-track report up. Do not enter `/go`, do not modify code, do not modify schema / prompt / docs / ai_context; wait for the user to decide item by item based on the full report in the conversation, typically handed to the next `/go` for follow-up fixes.

## Constraints

- Do not go through the motions just because `/go` Step 7 already reviewed — this round looks again with fresh eyes, focusing on the linked files and ambiguity `/go` missed
- **Output order hard constraint**: log writeback + commit (Step 5) **precedes** conversation report output (Step 6). The full dual-track report must be the **last substantive segment** `/post-check` produces in the conversation — Step 7 closes with a single "awaiting confirmation" short phrase, no further summary / commit prompt / next steps after the report, otherwise the user has to scroll back again
