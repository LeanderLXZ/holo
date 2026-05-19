---
name: commit
description: Commit the current working tree changes — verify tracking state (forbidden paths / large files / untracked files), split commits along logical units, message aligned to repo convention (drawn from git log). $ARGUMENTS = commit subject (optional). No push / no force / no amend / no --no-verify; cross-file ai_context/docs alignment → /go, cross-branch sync → /forward. Triggers: commit / commit it / commit the current changes.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (the commit message body, any in-place file edits like `.gitignore` additions) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / wrap-up `commit OK: <sha> <subject>` line) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, structural prefixes (`Step N:`, `commit OK:`, commit SHAs, branch names) stay English regardless.

# /commit — Quickly confirm and commit the current changes

Run a light verification of the current working tree, then commit once the changes are valid and tracking state is clean. **No full-repo review, no ai_context / docs alignment** (that is `/go`'s job); **no cross-branch sync** (that is `/forward`'s job).

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`.

The flow below is divided into `## Step 0:` ~ `## Step 3:` (the preceding `## $ARGUMENTS parsing` section is argument parsing, not a formal step).

**Before entering Step 0**: call **<progress tool>** to pre-register Step 0 ~ Step 3 (one entry per step, `content` set to `Step N: <sub-section title>`, `status` all `pending`; `$ARGUMENTS` parsing is not counted). This is a hard requirement — **do not proceed without calling <progress tool>**.

On entering each step: call **<progress tool>** to flip the current step to `in_progress` (in the same call, mark the previous step `completed`), then do the actual work. **Do not skip the call when crossing steps.** Progress is shown directly in the <progress tool> UI; **do not print `[/commit] Step N: ...` style progress lines in conversation**.

Skipping a step: call **<progress tool>** to mark that entry `completed` directly, and print one line in conversation: `Step N skipped (reason: …)` — the "reason" is information the UI lacks, keep that line; do not silently skip.

Final step done: call **<progress tool>** to mark the last entry `completed`.

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block on every state change. Semantic alignment: pre-register + flip state + mark complete.

## `$ARGUMENTS` parsing

`$ARGUMENTS` as a whole is taken as a hint / subject for the commit message (see Step 3); when empty the message is summarized from the diff. **No longer carries sync trigger words** — for cross-branch sync use `/forward`.

## Step 0: Load skills config

`Read` `ai_context/skills_config.md`.

- File missing / a section heading missing → fail loudly: print the missing item + prompt to fill it in per the plugin template, stop
- A section's content is `(none)` or empty → skip the section's related steps (treat as not applicable to this project)
- A section lists a concrete path but the path does not exist → fail loudly: report that the section has drifted to a non-existent path, stop and wait for the user to fix

When later steps reference "skills_config.md `## XX`", they refer to this config. This skill uses:
`## Do-not-commit paths` (Step 2 tracking-state scan).

## Step 1: Change validity

> **Language**: user-facing — render the `no changes to commit` exit message and any "is this change worth its own commit?" questions to the user in `conversation_language` per `ai_context/skills_config.md §Language`. Git output (`git status` / `git diff --stat`) captured verbatim stays in its original form; only the surrounding explanatory prose translates.

- `git status` + `git diff --stat` inspect working tree and index
- **If there are no changes at all** (working tree clean + empty index): nothing to commit this turn, print "no changes to commit" and end; subsequent steps all skipped
- Scan the change list and judge whether each is worth an independent commit (not whitespace / accidental save / temp debug print); anything suspicious → ask the user first

## Step 2: Tracking state

> **Language**: user-facing — render the forbidden-path / untracked-file / large-file confirmation prompts to the user in `conversation_language` per `ai_context/skills_config.md §Language`. File paths quoted in the prompts stay verbatim; only surrounding explanatory prose translates.

- Scan forbidden paths: per skills_config.md `## Do-not-commit paths` list +(`.gitignore` + `ai_context/conventions.md`) fallback
- `git ls-files --others --exclude-standard` shows untracked files, judge whether to include / add to .gitignore / leave alone
- Large files (>1MB) or binaries listed separately, ask the user to confirm inclusion
- Anything suspicious → stop and ask the user, do not run `git add -A` on your own

## Step 3: Commit

> **Language**: disk-bound — write the commit message text itself in `content_language` per `ai_context/skills_config.md §Language`. The commit message follows repo-convention prefixes (`feat:` / `fix:` / `log:` / `docs:` etc.) per `git log --oneline -10`; those prefixes stay English regardless of `content_language`. Code identifiers, file paths, field names stay English regardless.

> **Language**: user-facing — render any pre-commit preview wrapper around the message, the post-commit `commit OK: <short-sha> <subject>` line, and any `/forward` follow-up suggestion in `conversation_language` per `ai_context/skills_config.md §Language`. The commit message text inside the preview stays in `content_language` (it is the disk-bound surface).

- Split commits along logical units (if the change spans multiple independent topics); do not stuff too much into one
- Message style follows `git log --oneline -10`, keep repo convention (English/Chinese / prefix / verb tense)
- `$ARGUMENTS` non-empty → expand from it as subject; otherwise summarize from the diff
- Execute `git add <specific files>` + `git commit` (**do not use `git add -A` / `git add .`**, avoid accidentally including sensitive files)
- After commit `git status` confirms clean

When done print one line `commit OK: <short-sha> <subject>` to wrap up. If forwarding to other branches is needed, the user will explicitly invoke `/forward` next.

## Constraints

- No `git push`, no `--force`, no `--amend`, no branch switching, no merge (unless the user explicitly requests)
- Anything suspicious found (forbidden paths, huge diff, unresolved conflicts) → stop and ask, do not bypass
- No cross-branch sync — that capability has moved to `/forward`
