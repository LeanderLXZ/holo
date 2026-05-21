---
name: go
description: Heavyweight landing path — **only pick when one of these is true**: (a) change spans schema + code + docs and needs cross-file alignment verification; (b) you want /post-check to re-validate this round against a PRE log intent baseline; (c) work tree dirty / branch switch / worktree isolation needed; (d) smoke or data-contract validation must run before commit; (e) planned set ≥ 3 files. **Otherwise prefer /do.** 11-step flow: load config → ask work location → PRE log → doc authoring → implementation → smoke → cross-file alignment + todo_list maintenance → multi-line review → POST log → commit → stash/worktree wrap-up. Step 1 always asks work location (clean 3 options / dirty 4 options); Steps 2-9 are silent without questioning; Step 10 only handles residue from this round, no fan-out (cross-branch sync → /forward). Step 2 PRE log is the intent baseline for /post-check; no PRE, no file changes allowed. $ARGUMENTS = focus of this change (optional). Triggers: go / full /go / run the full flow / this change needs review / spans multiple modules / will follow with /post-check / dirty tree handling required / heavyweight landing.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (logs / docs / commit messages / code comments / files written) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / status lines / strategy declarations / findings rendered in chat) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, and structural prefixes (`Step N:`, `LOG:`, etc.) stay English regardless.

# /go — heavyweight landing path

Execute per the discussion above; if a step is N/A this round, say so explicitly ("skip Step X"). If `$ARGUMENTS` is present, it is the focus of this change.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`. Same rule applies to sub-task entries `Step Na:` / `Step Nb:` / ….

The flow below is split into `## Step 0:` ~ `## Step 10:`.

**Before entering Step 0**: call **<progress tool>** to pre-register Step 0 ~ Step 10 (one entry per step, `content` as `Step N: <sub-section title>`, all `status` = `pending`). This is a hard requirement — **do not proceed without calling <progress tool>**.

On entering each step: call **<progress tool>** to flip the current step to `in_progress` (in the same call, mark the previous step `completed`), then do the actual work. **Do not skip the call when crossing steps.** Progress is shown directly through the <progress tool> UI; **do not print progress lines like `[/go] Step N: ...` in the conversation**.

Skipping a step: call **<progress tool>** to mark the corresponding entry `completed` directly, and print one line in the conversation `Step N skipped (reason: …)` — the "reason" is information the UI lacks, so keep this line; do not silently skip.

Final step done: call **<progress tool>** to mark the last entry `completed`.

**Sub-tasks (optional, enable on demand)**: when a step's internal work is complex and obviously composed of multiple independent small tasks (e.g. Step 4 simultaneously changing schema / prompt / code / config blocks), upon entering that step you may **expand** `Step N: <title>` in the <progress tool> into several entries `Step Na: <sub-title>` / `Step Nb: …` / `Step Nc: …` (alphabetical, replacing the original `Step N` entry in the same call), flipping `in_progress` / `completed` as sub-tasks progress. **Only expand sub-tasks for the currently active step** — other steps stay collapsed as a single `Step M: <title>` entry, not expanded. Once all sub-tasks of the current step are `completed`, **on entering the next step fold these sub-tasks back into one** `Step N: <title>` `status=completed`, then expand the next step (if needed). This way the UI is always "current step fine-grained + other steps collapsed coarse-grained".

Simple steps need not enable this — just flip state on `Step N: <title>` directly. Sub-task numbering uses the same alphabetical series; **do not nest a second layer** (no `4a-1` / `4a-2`).

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block before each state change. Semantic alignment: pre-register + flip state + mark complete (including sub-task expand / fold-back).

**<ask tool> resolution**: Claude → `AskUserQuestion` (max 4 questions per call, batch beyond); other runtimes (no structured ask tool, e.g. Codex / Copilot agent mode) → enumerate questions + options per question in the response text and let the user answer in one pass (still max 4 per batch, batch beyond).

## Step 0: Load skills config

`Read` `ai_context/skills_config.md`.

- File missing / any section header missing → fail loudly: print the missing items + prompt to complete per plugin template, stop
- Section content `(none)` or empty → skip the related steps for that section (treat as N/A in this project)
- Section lists concrete paths but the path does not exist → fail loudly: report the section drifting to a nonexistent path, stop and wait for the user to fix

Subsequent steps referencing "skills_config.md `## XX`" use this config. This skill uses:
`## Background processes` (Step 1 dirty question's associated-process detection),
`## Do-not-commit paths` (Step 9 do-not-commit path scan before commit),
`## Timezone` (Step 2 / Step 8 timestamps),
`## Sensitive content placeholder rules` (Step 3 / Step 7),
`## Data contract directories` (Step 5 / Step 7 data contract scan; includes JSON Schema / proto / OpenAPI / Pydantic / SQL DDL etc.).

## Step 1: Lock the work location (environment probe + question-driven)

> **Language**: user-facing — render the `<ask tool>` prompts, option labels, the strategy declaration, and the language-axes anchor line below in `conversation_language` per `ai_context/skills_config.md §Language`. Structural prefixes (`Strategy:` / `Language axes:`) translate to their `conversation_language` equivalent if natural; the axis values are echoed verbatim from §Language.

The `/go` git interaction contract: **Step 1 always asks once** (selecting the work location here); **Steps 2 through 9 never ask in the middle**; **Step 10** decides whether to ask once more based on the Step 1 choice (worktree follow-up / stash pop etc.). `/go` no longer implicitly "switches to the main branch first" — whether to switch branches and whether to launch a worktree is explicitly selected by the user in Step 1.

- `git branch --show-current` to get current branch `<X>`; `git status --porcelain` to judge clean / dirty; probe per skills_config.md `## Background processes` (pgrep patterns + process artifact paths; skip process detection when the section is empty). Merge the dirty summary + associated processes (if any) into a single line `<dirty summary / associated process P>` as context for the Dirty question
- **Orphan-stash probe** (runs before either question dispatches): `git stash list | grep -F "/go autostash"` to count any earlier `/go` autostash entries still on the stash stack. A non-zero count means a previous `/go` run crashed between Step 2 and Step 9 (no pop in Step 10); pushing another autostash on top makes the stack ambiguous. Carry the count as `<stash-orphan-count>` (default 0) — referenced inside the Dirty question below
- **<ask tool>** one question, with different option sets for clean / dirty:

**Clean path** (working tree clean and no associated processes):

Question: "Current branch is `<X>`. Please choose `/go`'s work location."

1. **Execute in place on current branch `<X>` (recommended)** — stay on `<X>`; subsequent edits / PRE log / commit all land on that branch
2. **Switch to a specified branch then execute** — branch name required; enters worktree follow-up (see below) but uses `git checkout` rather than `git worktree add`: if the local branch exists, `git checkout` directly; if not, ask for base branch then `git checkout -b <branch> <base>`
3. **Execute in a separate worktree** — branch name required; enters worktree follow-up

**Dirty path** (working tree dirty or associated process detected):

Question: "Current branch is `<X>`; working tree detected `<dirty summary / associated process P>`. Please choose how to handle it." When `<stash-orphan-count>` > 0, append a prefix sentence to the question body: `⚠️ Detected <stash-orphan-count> existing "/go autostash" entr(y/ies) on the stash stack from a previous crashed run; consider \`git stash drop\` / \`git stash pop\` before re-stashing (option 4 below will push another autostash on top).` This surfacing is informational; the user still picks freely.

1. **Commit current WIP progress, then execute `/go` (recommended)** — reuse the `/commit` Step 1–3 scan contract (do-not-commit paths + untracked files + large-file fallback; **does not bypass** the Step 2 safety checks) to make one WIP commit (message defaults to `wip: <X> snapshot before /go`, may be overridden in subject by current `$ARGUMENTS`), then stay on `<X>` and continue `/go`
2. **Execute `/go` directly without handling** — uncommitted changes will be committed together with this change (user confirms this is intended)
3. **Execute in a separate worktree** — branch name required; enters worktree follow-up (worktree and current dirty working tree do not interfere)
4. **Stash current changes (`git stash`) then execute `/go`** — `git stash push -u -m "/go autostash <X>"` then stay on `<X>`; Step 10 at the end auto `git stash pop` to restore (see Step 10). When `<stash-orphan-count>` > 0 the option label gains a `(WARN: <N> orphan autostash already on stack)` suffix so the user sees the ambiguity hazard at the picker

**Worktree follow-up (only for Clean option 3 / Dirty option 3)**:

Ask another question: "Which branch should the worktree check out? Provide the branch name."

- The branch the user provided exists locally → `git worktree add ../<repo>-<branch> <branch>`; subsequent edits / PRE log / commit under the worktree path all go through that worktree
- The branch the user provided does not exist → ask one more: "Branch `<branch>` does not exist. Provide the base branch (default = current branch `<X>`)", then with the base obtained, `git worktree add -b <branch> ../<repo>-<branch> <base>`
- Worktree path conflict (directory already exists) → stop and report, let the user decide (clean up manually then re-run / pick another branch name)

**Switch to specified branch follow-up (only for Clean option 2)**:

Same "branch name → ask base if not exists" flow, but use `git checkout` / `git checkout -b <branch> <base>` and do not open a worktree. This option only appears on the Clean path — switching branches directly on a Dirty path would pollute the working tree; the user should first use Dirty option 1 / 4 to clean up the working tree then switch.

After selecting, print **two declaration lines** in succession:

- **Strategy line**: `Strategy: <chosen path>`, e.g. `Strategy: current branch develop in place` / `Strategy: switch to feature/x in place` / `Strategy: ../holo-main worktree isolation (branch=main)` / `Strategy: WIP commit then stay on develop in place` / `Strategy: stash then stay on develop in place (Step 10 auto pop)`. Natural-language portion translates to `conversation_language`; the structural prefix `Strategy:` (or its `conversation_language` equivalent) leads the line.
- **Language-axes anchor line**: `Language axes: conversation_language=<value> · content_language=<value> (source: ai_context/skills_config.md §Language)`. Both axis values are echoed **verbatim** from the §Language section read in Step 0; the bracketed source path stays English; the natural-language prefix translates to `conversation_language` (rendered in the project's chosen language). This line is a deliberate high-salience anchor planted before Steps 2–10 accumulate context.

If any of `git checkout` / `git worktree add` / WIP commit / `git stash` fails → stop and report the cause, wait for the user to decide. **No further questioning after Step 1** until the end of Step 10.

## Step 2: PRE log registration (register before acting)

> **Cross-skill protocol ownership**: this Step defines the PRE log template (section names, `Status: PRE` token, the `## Background / Trigger` / `## Conclusion and decisions` / `## Planned action list` / `## Validation criteria` / `## Execution deviations` subsection set) — the canonical definition consumed by `/post-check` Step 1.5 (intent baseline read). Renaming any of these subsection names, the `Status` token, or the file-header structure requires a lockstep edit in `/post-check` Step 1.5 + Step 5 per `ai_context/conventions.md §Cross-File Alignment` (row: "PRE/POST/REVIEW change-log protocol"). `/recent-activity` reads only the file head 25 lines and is heading-insensitive — NOT a lockstep consumer for these renames.

> **Language**: disk-bound — write this PRE log file in `content_language` per `ai_context/skills_config.md §Language`. The `LOG: …` echo printed to the user is user-facing (label `LOG:` stays English, path text translates only if a non-default `conversation_language` makes it natural; default = leave the line as `LOG: <path>`). Code identifiers, file paths, field names stay English regardless.

**Before any code / schema / prompt / docs / ai_context / skill change**, create this round's log file and write the PRE section. This is the intent baseline source for `/post-check`; mandatory.

- Filename: `<change_logs_path>/<filename pattern with slug substituted>` — `<change_logs_path>` is `skills_config.md ## Activity sources.Change logs.Path` and the pattern is `## Activity sources.Change logs.Filename time pattern` (defaults: `logs/change_logs/` + `{YYYY-MM-DD}_{HHMMSS}_{slug}.md`). HHMMSS is mandatory and executed per the skills_config.md `## Timezone` command template; if §Timezone is missing or its command fails, follow the fallback declared in §Timezone (system-tz `date '+%Y-%m-%d_%H%M%S'`). slug is a semantic short English name.
- Echo the path back to the user (one line `LOG: logs/change_logs/...md`) for later explicit reference by `/post-check`

The PRE section must contain:

```markdown
# {slug}

- **Started**: {YYYY-MM-DD HH:MM:SS} {timezone abbrev: per skills_config.md `## Timezone` setting}
- **Branch**: {work branch at /go entry}
- **Type**: GO
- **Status**: PRE

## Background / Trigger
{session context, user original ask, upstream discussion chain summary}

## Conclusion and decisions
{plan already decided at /go entry: direction picked, what changes, what does not}

## Planned action list
- file: {path} → {change focus}
- ...

## Validation criteria
- [ ] {e.g. Import has no error}
- [ ] {e.g. data contract validation passes}
- [ ] {e.g. grep residue = 0}
- ...

## Execution deviations
(append during execution; write "none" if no deviation)
```

Write the PRE section, then **enter Step 3**. If execution mid-way drifts from the plan → append a `## Execution deviations` paragraph to the log recording the new decision, **do not silently change**.

If the PRE log file write fails (IO error, path not writable, disk full, permission denied) → **stop and report the cause; do not enter Step 3**. `ai_context/conventions.md` §Logging "No PRE log → do not start modifying files" is the operative invariant; a failed write means no PRE log exists, so subsequent steps must not run.

## Step 3: Land discussion conclusions into docs (content authoring)

> **Language**: disk-bound — write these docs / ai_context updates in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names stay English regardless.

> **Compactness Requirements**: writes to `ai_context/` in this step follow the universal contract —
> - Shorter is better than longer. Each entry is a summary, not a detail dump.
> - Compactness must not sacrifice accuracy or completeness — never drop important information just to fit the length target.
> - Aim for ≤ 5 lines and push longer detail to the linked source (`docs/<topic>.md`, schemas, script docstrings).
> - Do not compress or touch content unrelated to the current edit.

Translate decisions from the conversation into doc language. **This step only does "writing"** — cross-file alignment verification belongs to Step 6; full-repo review belongs to Step 7. Any "I wrote file A and now feel file B needs changing too" sensation in this step **first goes into the PRE log's "Execution deviations" section**, deferred to Step 6 for systematic patching; do not stream-edit across files while writing.

Filter by scope touched in this discussion (do not blindly run all):

- **`docs/requirements.md` + `ai_context/requirements.md`** (paired, lockstep): update the matching sections when this round touches **user-visible functional contract / acceptance criteria / boundary constraint** changes
- **`docs/architecture/` + `ai_context/architecture.md`** (paired, lockstep): update matching sections when this round touches any of — **new module / new interface / new state machine / call-graph change / new branch strategy / new workflow contract / new entry point**
- **`ai_context/decisions.md`**: durable decisions produced this round land as entries immediately, not deferred to Step 6 / Step 8; **if the decision touches the trigger words above, simultaneously add a section in architecture / requirements describing it** (decision is "why", architecture / requirements is "what")
- **Prompt sources** (path per `skills_config.md ## Activity sources.Prompt sources.Path`; skip when `(none)`): update when discussion conclusions include prompt behavior contract / template changes
- **`README.md`**: only when directory / entry point / startup method changes

Authoring constraints:

- **Use placeholders per skills_config.md `## Sensitive content placeholder rules` to replace real content** (skip this scan when the section is empty)
- Descriptions write only the current design; do not write "old / legacy / deprecated / formerly"

## Step 4: Implement code / schema / prompt / config

> **Language**: disk-bound — write these code / schema / prompt / config changes in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names stay English regardless; user-facing chat reports of what changed translate to `conversation_language`.

Change schema, prompt template, architecture code, config per the discussion. **First confirm the PRE log "Validation criteria" section has ≥ 1 concrete executable item** (e.g. `import has no error` / `grep residue = 0` / `smoke X all pass`; not vague "as long as it works"); if vague → immediately add concrete ones then continue. Consult the Cross-File Alignment table in `ai_context/conventions.md` to list linked files (skip this if the table does not exist; judge by intuition based on this change).

## Step 5: Smoke test + data contract validation (only when code / data contract changes)

> **Language**: user-facing — render any chat report of smoke / contract validation outcomes (pass / fail summary, tool output rendered for the user) in `conversation_language` per `ai_context/skills_config.md §Language`. Tool stdout / stderr captured verbatim stays in its original form; only the surrounding explanatory prose translates. Code identifiers / file paths / structural labels (`PASS:` / `FAIL:`) stay English.

Import check + smoke test on key functions; if this change touches directories listed in skills_config.md `## Data contract directories` (schema / proto / openapi / pydantic / SQL DDL etc. data contracts), run the project's corresponding validation tool once (e.g.: JSON Schema → `jsonschema` / `ajv`; OpenAPI → `openapi-spec-validator` / `redocly lint`; proto → `protoc --lint_out`; pydantic → model import + `model_rebuild()`; SQL DDL → migration dry-run). Skip this contract validation when the section is `(none)`. Fix errors immediately.

## Step 6: Cross-file alignment + todo_list maintenance

> **Language**: disk-bound — write these ai_context / docs / todo_list maintenance edits in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names stay English regardless.

By here, Step 3 / 4 / 5 have written content into docs and code. **This step only does "alignment verification + maintenance wrap-up"**, no content authoring — if something needs re-authoring of a requirements / architecture description paragraph, go back to Step 3 to rewrite rather than cramming it in here.

**Cross-file alignment**:

- Consult the Cross-File Alignment table in `ai_context/conventions.md` (if absent, judge by intuition based on the files actually touched in Step 3 / Step 4), and check whether schema / prompt / code / docs / ai_context / README are consistent across these dimensions:
  - field names / params / return values / state values / error codes
  - flow descriptions / state machines / gating timing
  - terminology / concept naming
- If a file should have synced but did not → patch as a **gap-fix**; small change (one or two lines of sync) fix in place; large change (rewriting a whole requirements / architecture description paragraph) → go back to Step 3

**ai_context durable maintenance**:

- `ai_context/current_status.md`: does the current-state line need updating
- `ai_context/next_steps.md`: do new directions / blockers from this round need to be logged
- `ai_context/handoff.md`: does the next session need a one-liner handoff

**todo_list maintenance**:

- The TODO list (path per `skills_config.md ## Activity sources.TODO list.Path`, typically `docs/todo_list.md`): completed entries this round **move wholesale to the `## Completed` section of the archived TODO list** (path per `## Activity sources.Archived TODO list.Path`, typically `docs/todo_list_archived.md`) — slimmed: title + completion form + 1 line summary + this round's log link; update state changes
- After moves / additions / updates, **refresh the top `## Index` section in sync** (rule in the "Index maintenance" subsection at the top of `docs/todo_list.md`). The `/todo` skill reads the index only; without refresh it returns stale info
- ⚠️ Only maintain entries "directly produced / completed by this change"; new issues discovered during Step 7 review **do not register here**; follow Step 7 handling rules

## Step 7: Full-repo multi-line review (parallel)

> **Language**: disk-bound — when a finding is fixed in place inside a target file, the edited file follows that file's existing `content_language` rules (typically `content_language` per `ai_context/skills_config.md §Language`). Code identifiers, file paths, field names stay English.

> **Language**: user-facing — render the "suggest registering to todo_list" chat list (file + line + issue summary + suggested segment) in `conversation_language` per `ai_context/skills_config.md §Language`. Structural labels (`file:`, `line:`, `suggest segment:`) stay English; only the summary prose translates.

> **Language anchor reset (render-time)**: before emitting the "suggest registering to todo_list" chat list below, re-echo the language axes verbatim — `conversation_language=<value>` · `content_language=<value>` from `ai_context/skills_config.md §Language`. Step 6 just wrote `content_language`-bound ai_context / todo_list maintenance edits; this reset refreshes recency at the entry of the USER-facing chat-list render so the listed items stay in `conversation_language` even when sub-agent reports return findings phrased in English source language.

> **Language (sub-agent dispatch)**: when spawning sub-agents at this step, the parent MUST inject the language axes into each sub-agent's prompt explicitly. Include verbatim: "Reply in `conversation_language`=`<value>`; write any disk artifacts in `content_language`=`<value>`; both values from `ai_context/skills_config.md §Language`." Sub-agents do not inherit the parent's language config — they must be told. The sub-agent's report-back to the parent is a USER surface; its on-disk edits (if any) are DISK surface. **Place this injection at the end of the sub-agent prompt** (recency-favorable position), not in the header / middle — sub-agents have just read English source files in their review scope, so the dispatch directive needs recency advantage over the scanned content to keep the reply in `conversation_language`.

Scan in parallel files across the repo related to / dragged along by this change, **at least four lines, sub-agents may run in parallel**; for small change surface, run a single line serially.

**Four lines** (each re-reads the PRE log before scanning):

1. **Spec line**: `ai_context/` / `docs/` / directories listed in skills_config.md `## Data contract directories` (skip scan when `(none)`) / the prompt-sources path from skills_config.md `## Activity sources.Prompt sources.Path` (skip when `(none)`) — descriptions vs. this change consistent; any residual old descriptions / old fields / old flows; also check for real content violating skills_config.md `## Sensitive content placeholder rules`, or `old / legacy / deprecated / formerly` wording
2. **Implementation line**: code changed this round + its upstream / downstream (callers / callees / importers) — field names / params / return values / state machines / gates / exception paths still coherent; do imports still run
3. **Risk line**: code changed this round + related code dragged along (callers / callees / shared state / shared data flow) — boundary conditions, null / None, exception paths, concurrency, retry / rollback, error handling hiding bugs; do new behaviors introduce data loss / security holes / performance regressions; do state machines / gates / invariants have missed branches. **Distinct from implementation line**: implementation line asks "does it still hook up" (signature / import consistency); risk line asks "is what it does correct" (semantic correctness + failure modes)
4. **Structure line**: are README / directory structure / committed example artifacts / artifact directories aligned with this change; if filenames / directory structure changed → trace all reference points

**Findings handling** (**important**: issues discovered in this step do not get written directly into `docs/todo_list.md`):

- **One-line fixes** (typo, missed placeholder, missing import, obvious slip, single dangling reference) → **fix on the spot**, no tail
- **Big issues / cross-scope / need re-discussion / outside this round's intent** → **do not write into `docs/todo_list.md` yourself**; in the conversation list a "**suggest registering to todo_list**" block, each entry with: file + line, issue summary, suggested segment. After the user decides, `/todo-add` or the next `/go` lands the entry — avoid polluting todo_list history with findings outside this round's intent

> **Before entering this step, re-read the PRE log Step 2 created yourself** — after the editing context of prior steps, you have drifted from "original intent"; recalibrate against the PRE "Conclusion and decisions / Planned action list / Validation criteria" before scanning.
>
> **Each dispatched sub-agent must also re-read the same PRE log**: stuff the `LOG:` path into its prompt and **explicitly require it to read the log's PRE section before acting**. Sub-agents have independent context; without enforced PRE reading they will spin only on the brief in the prompt, easily drifting from this round's intent.

## Step 8: POST log wrap-up

> **Cross-skill protocol ownership**: this Step defines the POST section template (`## Landed changes` / `## Diff from plan` / `## Validation results` / `## Completed` subsection set) and the `Status: DONE | BLOCKED` state-machine transition from `PRE`. The POST section is consumed by `/post-check` Step 5 (REVIEW append, which expects the POST section to already exist and reads the `Status` token to decide whether to flip to `REVIEWED-*`). Renaming any of these subsection names, the `Status` tokens, or the `Completed` block structure requires a lockstep edit in `/post-check` Step 5 per `ai_context/conventions.md §Cross-File Alignment` (row: "PRE/POST/REVIEW change-log protocol").

> **Language**: disk-bound — write this POST log section appended to the same log file in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names stay English regardless.

Update **the same log Step 2 created**, appending the POST section:

```markdown
<!-- POST phase fills in -->

## Landed changes
{which files actually changed, what each changed, file + line numbers or diff summary}

## Diff from plan
{compared with PRE "Planned action list", what was added / removed / modified; write "none" if nothing}

## Validation results
- [x] {PRE validation 1} — {output summary}
- [ ] {PRE validation 2} — {failure cause}
- ...

## Completed
- **Status**: DONE | BLOCKED
- **Finished**: {timestamp, per skills_config.md `## Timezone` command template, same timezone as PRE Started}
```

Do not create a new log file; update the same file that holds the PRE section in place.

## Step 9: Git commit

> **Language**: disk-bound — write this commit message in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names stay English regardless. The pre-commit confirmation surface (the message preview shown to the user) is user-facing — render explanatory prose around the message in `conversation_language`, but the commit message text itself stays in `content_language`.

Step 1 has locked the work location (current branch in place / branch after switch / branch inside the worktree); commit **lands on the branch selected in Step 1**. Whether to clean up the worktree is left to Step 10 — this step does not touch it.

- `git status` shows only this change; scan per skills_config.md `## Do-not-commit paths` + (`.gitignore` + `ai_context/conventions.md`) as fallback
- message style aligned with `git log --oneline -10`
- **This change + PRE/POST log file merge into one commit** — no longer split into `<slug>: ...` + `log(<slug>): /go PRE+POST` two commits
- After commit, `git status` confirms clean
- **If Step 1 went the worktree path**: commit executes inside that worktree; after commit **does not auto-clean** the worktree (cleanup goes through the Step 10 end question). `/go` always stays at the work location selected in Step 1 (worktree / switched branch / original branch), does not switch back behind the user's back

## Step 10: Wrap-up (stash pop + worktree follow-up)

> **Language**: user-facing — render the worktree-handling `<ask tool>` prompt, the final state line, and the `stash popped and restored` confirmation in `conversation_language` per `ai_context/skills_config.md §Language`. Structural prefixes (`stash`, `worktree`, `HEAD`) stay English; only surrounding prose translates.

> **Language anchor reset (render-time)**: before emitting the wrap-up prose / `<ask tool>` prompt / final state line below, re-echo the language axes verbatim — `conversation_language=<value>` · `content_language=<value>` from `ai_context/skills_config.md §Language`. Step 9 just wrote a `content_language`-bound commit message; this reset refreshes recency at the entry of the USER-facing wrap-up surface (the last conversation segment `/go` produces) so the prompt + state line + confirmation stay in `conversation_language`.

`/go` **no longer fans out to other branches** — cross-branch sync is `/forward`'s job, explicitly invoked by the user after this `/go` completes. This step only handles the state left by the Step 1 choice.

Handle per the path actually taken in Step 1:

- **Clean option 1 (current branch in place) / Clean option 2 (switched branch in place) / Dirty option 1 (WIP commit in place) / Dirty option 2 (execute without handling)** → no leftover state; print directly "`/go` complete; currently on `<branch>`; commit landed. For subsequent sync to other branches, use `/forward`", **no questioning**, end
- **Dirty option 4 (stash then execute)** → on source branch `<X>`, auto `git stash pop` to restore the working tree. pop failure (conflict / stash lost) → stop and report, let the user decide; on success, print one line `stash popped and restored`, **no questioning**, end
- **Clean option 3 / Dirty option 3 (worktree path)** → use **<ask tool>** to ask once: "`/go` complete; this commit landed on `<branch>`. How to handle worktree `../<path>`?"
  1. **Keep worktree (recommended — convenient for continued work on that branch)** — leave the worktree alone; print the current worktree path for next-time use
  2. **Clean up immediately (`git worktree remove`)** — execute `git worktree remove ../<path>` from the source repo root; the commit has landed on the branch ref, removing the worktree directory does not lose data. If `git worktree remove` fails due to dirty files → stop and report, let the user decide (do not auto-add `--force`)

Print a final state line: `/go` complete; current HEAD = `<branch>`; worktree handling result (kept / cleaned). **Does not switch back to any "main branch"** — `/go` always respects the work location selected in Step 1, leaving "which branch I am on" to the user.
