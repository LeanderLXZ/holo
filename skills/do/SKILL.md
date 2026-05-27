---
name: do
description: Default landing path for already-discussed changes — 4 steps: load config → plan + edit → single-segment LOG → ask commit. Single intent / ≤2 files / no PRE log / no review / no smoke / no worktree. Auto-asks upgrade to /go when planned set ≥ 3 files; docs/ai_context edits only when explicitly the discussion target (opportunistic "while I'm here" edits blocked). $ARGUMENTS = focus / slug hint (optional). Pick /do unless one of /go's triggers clearly applies. Triggers: do / do it / quick edit / quick fix / edit in place / land lightly / land what we just discussed / change one file.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (logs / docs / commit messages / code comments / files written) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / status lines / strategy declarations / findings rendered in chat) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, and structural prefixes (`Step N:`, `LOG:`, etc.) stay English regardless.

# /do — default landing path

Execute per the discussion above. `/do` is the default path for landing already-discussed changes — single intent, ≤2 files, short feedback loop. No PRE log gating, no smoke, no review, no cross-file fan-out, no worktree / stash / branch switch. If `$ARGUMENTS` is present, it is the focus / slug hint for this round.

**Discipline (per `CLAUDE.md` §Dilution Self-Check, adapted for `/do`)** — before editing, answer the three:

1. **Scope check** — am I doing exactly what the user asked, or am I expanding into proactive refactor / "while I'm here" fixes? If expanding → stop and ask first.
2. **Right layer** — does the file I am about to edit sit in the right module / layer for this concern? If unsure → re-read `ai_context/architecture.md`.
3. **Default-no-doc rule** — do NOT touch any file under `docs/` or `ai_context/` unless **(a)** the user explicitly named it in the discussion, or **(b)** the entire discussion is about that file in the first place. `/do` is NOT for "I noticed the docs were out of date while I was here" — that opportunistic alignment is `/go`'s job (Step 3 / Step 6).

If the change surface widens past `/do`'s envelope mid-flight (≥ 3 files / cross-file alignment needed), exit and re-enter via `/go` — `/do` does **NOT** mid-flight escalate.

**Anti-pattern (hard).** `/do` does NOT call `/go` / `/post-check` / `/full-review` / `/commit` / `/update-docs`. The Step 3 commit is a raw `git add` + `git commit`, not a delegated invocation. `/do` does NOT switch branches, open worktrees, stash / pop, or fan out to other branches. `/do` does NOT maintain `ai_context/` durable state (`current_status.md` / `next_steps.md` / `handoff.md` / `decisions.md`) or `docs/todo_list.md` — those are `/go` Step 6's job.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`.

The flow below is split into `## Step 0:` ~ `## Step 3:`.

**Before entering Step 0**: call **<progress tool>** to pre-register Step 0 ~ Step 3 (one entry per step, `content` as `Step N: <sub-section title>`, all `status` = `pending`). This is a hard requirement — **do not proceed without calling <progress tool>**.

On entering each step: call **<progress tool>** to flip the current step to `in_progress` (in the same call, mark the previous step `completed`), then do the actual work. **Do not skip the call when crossing steps.** Progress is shown directly through the <progress tool> UI; **do not print progress lines like `[/do] Step N: ...` in the conversation**.

Skipping a step: call **<progress tool>** to mark the corresponding entry `completed` directly, and print one line in the conversation `Step N skipped (reason: …)` — the "reason" is information the UI lacks, so keep this line; do not silently skip.

Final step done: call **<progress tool>** to mark the last entry `completed`.

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block before each state change. Semantic alignment: pre-register + flip state + mark complete.

**<ask tool> resolution**: Claude → `AskUserQuestion` (max 4 questions per call, batch beyond); other runtimes (no structured ask tool, e.g. Codex / Copilot agent mode) → enumerate questions + options per question in the response text and let the user answer in one pass.

## Step 0: Load skills config

`Read` `ai_context/skills_config.md`.

- File missing / any section header missing → fail loudly: print the missing items + prompt to complete per plugin template, stop
- Section content `(none)` or empty → skip the related steps for that section (treat as N/A in this project)
- Section lists concrete paths but the path does not exist → fail loudly: report the section drifting to a nonexistent path, stop and wait for the user to fix

Subsequent steps referencing "skills_config.md `## XX`" use this config. This skill uses:
`## Sensitive content placeholder rules` (Step 1.2 — only when a `docs/` or `ai_context/` file is touched),
`## Do-not-commit paths` (Step 3.2 do-not-commit path scan before commit),
`## Protected branch prefixes` (Step 3.0 protected branch check),
`## Timezone` (Step 2 LOG timestamp),
`## Activity sources.Change logs.Path` + `Filename time pattern` (Step 2 LOG file path).

> **Language**: user-facing — render the language-axes anchor line below in `conversation_language` per `ai_context/skills_config.md §Language`. Axis values are echoed verbatim from §Language.

After reading, print one line **Language-axes anchor**: `Language axes: conversation_language=<value> · content_language=<value> (source: ai_context/skills_config.md §Language)`. Both axis values are echoed **verbatim** from the §Language section; the bracketed source path stays English; the natural-language prefix translates to `conversation_language` (rendered in the project's chosen language). This is a deliberate high-salience anchor planted before Steps 1–3 accumulate context.

## Step 1: Plan + modify

> **Language**: user-facing — render the `Plan:` declaration line, the `<ask tool>` 3-option fork prompt + option labels (if it fires), and any exit lines in `conversation_language` per `ai_context/skills_config.md §Language`. Structural labels (`Plan:`, `/do exited`, file paths) stay English; only surrounding prose translates.

> **Language**: disk-bound — file edits themselves follow the target file's existing `content_language` rules (typically `content_language` per `ai_context/skills_config.md §Language`). Code identifiers, file paths, field names stay English regardless.

### 1.0 Self-check

Run the three Dilution Self-Check questions at the top of this skill. If any answer is "expanding scope" / "wrong layer" / "would touch `docs/` or `ai_context/` opportunistically" → stop and ask the user before proceeding.

### 1.1 Declare planned modification set

Print one line: `Plan: file1 / file2 / file3 / ...` listing every file you expect to modify in this `/do` run, then count. (The `Plan:` prefix translates to `conversation_language` if natural; file paths stay English.)

**What counts toward the threshold**: user-discussed file modifications only. The single-segment LOG file written by Step 2 is an auxiliary record (one file per run, always written) — it does **not** count toward the ≥ 3 threshold.

**If count ≥ 3** → call **<ask tool>** with this question:

> "Planned modification set has `<N>` files, exceeding `/do`'s lightweight envelope. Choose how to proceed."

Options (exactly three, recommended option first):

1. **Upgrade to `/go` (recommended)** — exit `/do`; user re-invokes `/go`, which carries PRE log + cross-file alignment + multi-line review.
2. **Continue with `/do`** — accept the wider scope on this run; subsequent additions during execution do NOT re-trigger this question (see 1.2 "Mid-flight new file" rule).
3. **Exit without modifying** — abort `/do`; no files touched, no LOG written.

Branch on the answer:

- Option 1 → print `/do exited; re-enter via /go for ≥ 3-file changes` and stop the skill.
- Option 2 → proceed to 1.2.
- Option 3 → print `/do exited; no files modified` and stop.

**If count < 3** → proceed to 1.2 directly (no ask).

### 1.2 Execute modifications

Edit files per the discussion. Constraints:

- **Default-no-doc/ai_context**: do NOT edit any file under `docs/` or `ai_context/` unless **(a)** the user explicitly named it in the discussion, or **(b)** the entire discussion is about that file. Touching them opportunistically is `/go`'s job, not `/do`'s.
- **If a `docs/` or `ai_context/` file IS touched**: apply `skills_config.md ## Sensitive content placeholder rules` (skip when `(none)`) and do not introduce `legacy` / `deprecated` / `formerly` / `renamed from` wording (per `ai_context/conventions.md §Generic Placeholders`).
- **Mid-flight new file** — if while editing you discover a 3rd / 4th file that was not in the Step 1.1 declaration, do **NOT** re-ask. Edit it if you judge it strictly necessary for the current change to be correct, then record the addition in the LOG `## Execution deviations` section at Step 2. (User's recourse is to re-run as `/go` next time; `/do` does not retroactively escalate.)

## Step 2: Write single-segment LOG

> **Cross-skill protocol ownership**: this Step defines the `/do` single-segment LOG template — `Type: DO`, single `Status: DONE | BLOCKED` token, `## Motivation` / `## Change list` / `## Verification summary` / `## Execution deviations` subsection set. **NOT** consumed by `/post-check` (which targets `Type: GO` only — see `skills/post-check/SKILL.md` Step 1.5). Renaming any subsection / the `Type` value / the `Status` tokens requires a lockstep edit per `ai_context/conventions.md §Cross-File Alignment` (row: "PRE/POST/REVIEW change-log protocol"). `/recent-activity` reads only the file head 40 lines and is heading-insensitive — NOT a lockstep consumer for renames.

> **Language**: disk-bound — write this LOG file in `content_language` per `ai_context/skills_config.md §Language`. The `LOG: …` echo printed to the user is user-facing (label `LOG:` stays English, path text translates only if a non-default `conversation_language` makes it natural; default = leave the line as `LOG: <path>`). Code identifiers, file paths, field names stay English regardless.

Write to `<change_logs_path>/<filename pattern with slug substituted>` — `<change_logs_path>` is `skills_config.md ## Activity sources.Change logs.Path` and the pattern is `## Activity sources.Change logs.Filename time pattern` (defaults: `logs/change_logs/` + `{YYYY-MM-DD}_{HHMMSS}_{slug}.md`). HHMMSS is executed per the skills_config.md `## Timezone` command template; on missing / failure, follow the §Timezone-declared fallback (system-tz `date '+%Y-%m-%d_%H%M%S'`). `slug` is a semantic short English name; use `$ARGUMENTS` as a hint if it was provided.

The LOG must contain:

```markdown
# {slug}

- **Started**: {YYYY-MM-DD HH:MM:SS} {timezone abbrev: per skills_config.md `## Timezone` setting}
- **Branch**: {work branch at /do entry}
- **Type**: DO
- **Status**: DONE | BLOCKED

## Motivation
{why this change — original user ask, upstream discussion summary in 1–3 sentences}

## Change list
- file: {path} → {change focus, file + line numbers or 1-line diff summary}
- ...

## Verification summary
- {how the change was confirmed correct — e.g. "import has no error", "grep residue = 0", "rendered output matches design"; or explicitly "no automated check — visual review only"}
- ...

## Execution deviations
- {if Step 1.2 added files not in the Step 1.1 declaration, list each with a one-line rationale; otherwise write "none"}
```

Echo path one line: `LOG: logs/change_logs/...md`.

If the LOG write fails (IO error, path not writable, permission denied) → **stop and report**; the modifications stay on disk but the activity record is missing, so do NOT proceed to Step 3 commit. The user decides retry / abandon.

## Step 3: Commit ask

> **Language**: user-facing — render the `git status` / `git diff --stat` summary explanation, the `<ask tool>` commit question + option labels, and the final state line in `conversation_language` per `ai_context/skills_config.md §Language`. Tool stdout / stderr captured verbatim stays in its original form; only the surrounding explanatory prose translates. Code identifiers / file paths / structural labels (`HEAD`, `branch`) stay English.

> **Language**: disk-bound — commit message written in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names stay English regardless. The pre-commit confirmation surface (message preview shown to the user) is user-facing — explanatory prose around the message translates to `conversation_language`, but the commit message text itself stays in `content_language`.

### 3.0 Protected branch check

`git branch --show-current` to get the current branch `<X>`. Compare against `skills_config.md ## Protected branch prefixes`. If `<X>` matches any prefix → **fail loud**: print "Current branch `<X>` matches Protected branch prefix `<Y>`; `/do` does not auto-commit on protected branches. Use `/go` (which has explicit branch-switch flow), or commit manually after switching." and stop. Modifications + LOG are already on disk; the user handles the commit themselves.

When `## Protected branch prefixes` is `(none)`, skip this check.

### 3.1 Show change summary

Run:
- `git status --short`
- `git diff --stat HEAD`

Print both verbatim to the user (wrapped in fenced code blocks) so the user sees exactly what is about to be committed before answering Step 3.3.

### 3.2 Do-not-commit path scan

Walk the changed file list (from Step 3.1) against `skills_config.md ## Do-not-commit paths`. Skip when `(none)`. If any forbidden path appears in the change set → **fail loud**: print "Change set contains do-not-commit path `<path>`; remove / unstage that file before `/do` can commit." and stop. The user resolves manually (e.g. `git restore --staged <path>` + `git stash` or delete the change).

### 3.3 Ask whether to commit

Call **<ask tool>** with this question:

> "`/do` modifications written + LOG recorded. Commit now?"

Options (exactly two, recommended option first):

1. **Commit now (recommended)** — `git add <change set + LOG file>` then `git commit` with a message authored in the project's existing style (see 3.4).
2. **Skip commit** — leave the working tree dirty; the user commits later (e.g. via `/commit` skill, or manual `git commit`).

### 3.4 Execute (option 1) or skip (option 2)

**Option 1 (commit)**:

- Stage **only** files in the Step 3.1 change set + the LOG file from Step 2 (do NOT opportunistically include unrelated dirty files; if other dirty files exist, they remain unstaged).
- Author the commit message in the style of `git log --oneline -10` (read the recent precedent to match prefix conventions, e.g. `<slug>: ...` / `feat(...): ...` / `fix(...): ...`). The LOG file + modifications go into **one commit** — do not split.
- After commit, run `git status` to confirm clean working tree.
- Print one line: `/do complete; commit landed on <branch>; LOG: <path>`.

**Option 2 (skip)**:

- Do not stage / commit anything. Modifications + LOG file stay as dirty working tree.
- Print one line: `/do complete; modifications + LOG on disk, commit skipped; current branch: <branch>`.

## Constraints

- **No delegated skills**: `/do` does NOT call `/go` / `/post-check` / `/full-review` / `/commit` / `/update-docs`. The Step 3 commit is raw `git add` + `git commit`, not a delegated invocation.
- **No environment takeover**: `/do` does NOT switch branches, open worktrees, stash / pop, run background-process probes, or fan out to other branches. Cross-branch sync → `/forward` (user-invoked, separately, after `/do`).
- **No mid-flight escalation**: `/do` does NOT mid-flight escalate to `/go`. If the scope widens, exit cleanly and re-enter via `/go`.
- **No durable-doc maintenance**: `/do` does NOT touch `ai_context/current_status.md` / `next_steps.md` / `handoff.md` / `decisions.md` unless the discussion is explicitly about those files. Durable maintenance is `/go` Step 6's job.
- **No todo bookkeeping**: `/do` does NOT maintain `docs/todo_list.md` (no entry move to archived, no Index refresh). Use `/todo-add` or `/go` for todo bookkeeping.
- **No backfill of pre-existing logs**: pre-existing `logs/change_logs/*.md` files are NOT retroactively assigned a `Type` field. Only new logs from `/go` (`Type: GO`) and `/do` (`Type: DO`) onward carry the field.
