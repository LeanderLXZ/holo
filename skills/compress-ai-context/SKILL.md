---
name: compress-ai-context
description: Maintenance skill that scans 6 ai_context files (`decisions.md` / `conventions.md` / `requirements.md` / `architecture.md` / `handoff.md` / `next_steps.md`), optionally prunes stale entries first (LLM-judged against current architecture; starter heuristics by file type; per-case 3-option ask for `stale + has live refs`), then compresses bloated entries with rationale landing in `docs/architecture/<topic>.md` where the linked doc target needs it. Sentinel-aware — parses via `scripts/sentinel_parse.py` and operates only on gap-territory content (sentinel-bearing content is plugin-canonical, owned by `/holo:update`). Snapshot-on-apply — `take_snapshot(target_root, slug, files)` (existing helper at `scripts/holo_update_check.py`) invoked **immediately before** each phase's first Edit; snapshots land in `logs/file_snapshots/<YYYY-MM-DD_HHMMSS>_<slug>/<original-path>`. Reuses the contract from `ai_context/conventions.md §Compactness Requirements` (does NOT re-author rules). No numbering check / no auto-reorder / no commit / no push. Triggers: /compress-ai-context / compress ai_context / prune stale ai_context entries / 压缩 ai_context / 清理过时决策.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (prune deletions, compress patches, snapshot files copied, follow-up todo entry written into `docs/todo_list.md`, the trailing reminder line if redirected to a file) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / scan summary printed in chat / per-entry preview wrappers / final wrap-up status line) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, section headings (`## Decisions`, `### [T-XXX]`), and structural prefixes (`Step N:`, `PRUNE:`, `COMPRESS:`, `SNAPSHOT:`, etc.) stay English regardless.

# /compress-ai-context — Prune stale + compress bloated ai_context entries

Maintenance counterpart to `/update-docs`: where `/update-docs` *adds*
narrative into `ai_context/` + `docs/` from session discussions, this
skill *trims* and *relocates* existing `ai_context/` content per the
canonical compactness contract. Two phases (both optional / opt-in via
Step 1 gateway): **prune** stale entries (entries that no longer
reflect current architecture / requirements), then **compress**
bloated-but-still-accurate entries by pushing rationale to linked
docs. Sentinel-aware (won't touch plugin-canonical territory),
snapshot-backed (every write is preceded by `take_snapshot` so
rollback is one `cp` away).

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`. Same rule applies to sub-task entries `Step Na:` / `Step Nb:` / ….

The flow below is split into `## Step 0:` ~ `## Step 8:`.

**Before entering Step 0**: call **<progress tool>** to pre-register all of Step 0 ~ Step 8 (one entry per step, `content` = `Step N: <sub-section title>`, `status` = `pending` for all). This is a hard requirement — **do not proceed without calling <progress tool>**.

Each time you enter a step: call **<progress tool>** to flip the current step to `in_progress` (mark the previous step `completed` in the same call), then do the real work. **Do not skip the call across step boundaries**. Progress is rendered directly by the <progress tool> UI — **do not print `[/compress-ai-context] Step N: ...` style progress lines in the conversation**.

Skipping a step: call **<progress tool>** to mark the entry directly `completed`, and print one line `Step N skipped (reason: …)` in the conversation — "reason" is information the UI lacks, keep that line; do not silently skip. Steps 2–4 are skipped wholesale when the Step 1 gateway answer is "no".

Final step completion: call **<progress tool>** to mark the last entry `completed`.

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block on every state change. Semantic alignment: pre-register + flip state + mark complete.

**<ask tool> resolution**: Claude → `AskUserQuestion` (max 4 questions per call, batch beyond); other runtimes (no structured ask tool, e.g. Codex / Copilot agent mode) → enumerate questions + options per question in the response text and let the user answer in one pass (still max 4 per batch, batch beyond).

## Step 0: Load skills_config

`Read` `ai_context/skills_config.md`.

- File missing / any section header missing → fail loudly: print the missing items + prompt to complete per plugin template, stop
- Section content `(none)` or empty → skip the related steps for that section (treat as N/A in this project)
- Section lists concrete paths but the path does not exist → fail loudly: report the section drifting to a nonexistent path, stop and wait for the user to fix

This skill uses:
`## Language` (drives `content_language` for disk artifacts + `conversation_language` for user-facing surface; the L1 directive at top of this file already routes both buckets),
`## Timezone` (Step 4 / Step 7 snapshot timestamps via the command template),
`## Activity sources` (TODO list path for the optional follow-up todo created in Step 4 when the user picks `Auto-prune + create follow-up todo`).

Also `Read` `ai_context/conventions.md §Compactness Requirements` — this is the canonical contract this skill enforces; do not re-author its rules locally.

## Step 1: Gateway ask (prune phase opt-in)

> **Language**: user-facing — render the `<ask tool>` prompt and option labels in `conversation_language` per `ai_context/skills_config.md §Language`. Structural label `Step 1` stays English; only question prose translates.

Ask via **<ask tool>** — one question, two options:

Question: `Scan ai_context for stale entries to prune before compressing?`

1. **No — compress only (recommended; faster)** — skip Steps 2–4, jump to Step 5 (compress scan)
2. **Yes — prune first, then compress** — enter Steps 2–4 (prune phase), then continue to Step 5

Default = option 1 (no). Most invocations are pure compression. The prune phase is opt-in because (a) it requires whole-repo grep for live-ref detection and is materially slower, and (b) stale detection is LLM-semantic so it should be deliberately invoked, not implicit.

## Step 2: Prune scan (when Step 1 = yes)

> **Language**: user-facing — render the scan summary printed to the conversation (file count + candidate count + per-file finding count) in `conversation_language` per `ai_context/skills_config.md §Language`. Structural labels (`file:`, `entry:`, `verdict:`) stay English; only summary prose translates.

For each of the 6 ai_context files
(`decisions.md` / `conventions.md` / `requirements.md` /
`architecture.md` / `handoff.md` / `next_steps.md`):

1. **Parse via `scripts/sentinel_parse.py`** (`parse(path) -> ParsedFile`). Consider **only gap-territory content** (`ParsedFile.preamble_user_gaps` + each `Section.user_gaps`). **Skip plugin-canonical territory** (`preamble_plugin_blocks` + each `Section.plugin_blocks`) — that content is owned by `/holo:update`, out of scope for this skill.

2. **Apply file-type starter heuristics** (inspection triggers, NOT sufficient evidence on their own):
   - `decisions.md` — pointer-target file/function in the `→` line does not exist; entry self-marks `superseded by #N`; entry references a removed/renamed module that `grep` cannot find.
   - `conventions.md` — Cross-File Alignment row lists files that no longer exist; row's lockstep relationship references removed flow.
   - `requirements.md` — paired `docs/requirements.md §N` section absent; requirement references a removed feature.
   - `architecture.md` — referenced `docs/architecture/<topic>.md` / module / file absent.
   - `handoff.md` — referenced command / skill no longer in `commands/` or `skills/`.
   - `next_steps.md` — referenced todo already in `docs/todo_list_archived.md ## Completed` or `## Abandoned`.

3. **LLM semantic judgment** (the main driver): for each entry, read it and judge — is it still aligned with the current architecture / requirements? Was the decision overturned by a later decision (search `ai_context/decisions.md` for newer #N entries on the same topic)? Has the referenced module / file / flow been removed or restructured? Heuristics from #2 raise candidates for inspection; LLM decides the actual `stale` verdict.

4. **Live-reference grep** for each `stale` candidate. Scope = `repo - logs/ - docs/todo_list_archived.md` (the two historical roots; references inside them don't count as live). Search for: the entry's stable identifier (e.g. `decisions.md #19` for a decisions entry; conventions row title; requirement number); plus the entry's key terms (module names, file paths it mentions). Classify each candidate as `stale + no live refs` (safe orphan) or `stale + has live refs` (needs user decision).

Print to the conversation a scan summary in this shape:

```
PRUNE scan:
- ai_context/decisions.md: 23 entries scanned, 2 stale (0 orphan, 2 with live refs)
- ai_context/conventions.md: 34 rows scanned, 0 stale
- ai_context/requirements.md: 16 entries scanned, 1 stale (1 orphan, 0 with live refs)
- ai_context/architecture.md: 12 entries scanned, 0 stale
- ai_context/handoff.md: 4 sections scanned, 0 stale
- ai_context/next_steps.md: 8 bullets scanned, 0 stale
Total: 3 stale candidates (1 orphan, 2 with live refs)
```

If `Total: 0 stale`, skip to Step 5 with a one-line `0 stale entries found, prune phase no-op` notice.

## Step 3: Prune per-case ask (only when `stale + has live refs` set is non-empty)

> **Language**: user-facing — render the `<ask tool>` prompt + option labels + per-case context in `conversation_language` per `ai_context/skills_config.md §Language`. File paths, entry IDs, reference paths quoted inside the prompt stay English; only surrounding prose translates.

For each `stale + has live refs` case (batched up to 4 questions per `AskUserQuestion` call; batch beyond if > 4 cases):

Question: `Stale entry "<file>:<entry-id-or-title>" still has N live ref(s) at <file:line>, <file:line>, … . How to handle?`

1. **Auto-prune + create follow-up todo (recommended)** — delete the entry; defer the dangling-ref cleanup to a new bundled `T-XXX` entry created in Step 4 (single todo per skill invocation, listing all such dangling refs as its change manifest).
2. **Auto-prune + leave dangling refs** — delete the entry; leave the live refs in place (they'll grep-fail; user accepts the broken state).
3. **Skip (keep entry as-is)** — do not prune; entry stays even though LLM judged it stale.

`stale + no live refs` cases are NOT asked — they go straight to apply in Step 4.

## Step 4: Prune apply

> **Language**: disk-bound — pruned-entry deletions land in 6 ai_context files; follow-up todo (if any case picked option 1) lands in `docs/todo_list.md`. All disk writes use `content_language` per `ai_context/skills_config.md §Language`. Snapshot files are byte-copies of the source files (no language transformation).

> **Compactness Requirements**: any new content this step writes (the bundled follow-up todo entry created when "Auto-prune + create follow-up todo" was picked) follows the universal contract —
> - Shorter is better than longer. Each entry is a summary, not a detail dump.
> - Compactness must not sacrifice accuracy or completeness — never drop important information just to fit the length target.
> - Aim for ≤ 5 lines and push longer detail to the linked source (`docs/<topic>.md`, schemas, script docstrings).
> - Do not compress or touch content unrelated to the current edit.

a. **Snapshot before write**: `take_snapshot(target_root, slug='compress-ai-context-prune', file_paths=[touched ai_context files + docs/todo_list.md if a follow-up todo will land])`. Invoked **immediately before** the first `Edit` of this phase; not pre-emptively at skill startup. Capture the returned snapshot dir path for the wrap-up.

b. **Apply each pruned entry via `Edit`** (one `Edit` per entry; no batched `replace_all`). For `decisions.md` entries: do NOT renumber surviving entries (per `decisions.md §Format` global-append-only rule); just delete the offending block. For `conventions.md` rows: delete the table row only. For all 6 files: also remove any redundant surrounding `---` separator or trailing blank line if the surrounding structure breaks.

c. **Create bundled follow-up todo** (only if ≥ 1 case picked "Auto-prune + create follow-up todo"): append ONE new entry to `docs/todo_list.md ## Next` with slug like `T-PRUNE-DANGLING-REFS-<YYYYMMDD>`, body listing each dangling ref as a change-manifest bullet (file:line + short context). Update the top `## Index` Next sub-table per `docs/todo_list.md "## File guide → Index maintenance"` rules.

d. **Print apply summary**:

```
PRUNE applied:
- 1 orphan entry deleted (no live refs)
- 1 entry deleted + dangling refs (logged in T-PRUNE-DANGLING-REFS-20260521)
- 1 entry kept (user picked Skip)
SNAPSHOT: logs/file_snapshots/<YYYY-MM-DD_HHMMSS>_compress-ai-context-prune/
```

## Step 5: Compress scan

> **Language**: user-facing — render the scan summary printed to the conversation in `conversation_language` per `ai_context/skills_config.md §Language`. Structural labels stay English.

For each of the 6 ai_context files, parse via `scripts/sentinel_parse.py` (same as Step 2) and look at gap-territory content only. **Trigger**: file > 150 lines OR any single entry > 5 lines. If neither, the file is skipped silently.

For each bloated entry:

1. **Identify the linked-doc target** — typically the entry's `→` pointer line (`→ docs/architecture/<topic>.md`); or, when the entry has no explicit pointer, grep `docs/` for the entry's key terms to find a plausible existing doc. If no target exists, the new-doc creation case (rare).

2. **Classify** as:
   - **(a) doc already covers rationale** — the linked doc already documents the design / rationale this entry contains; compression simply removes the duplication, leaving a one-line decision + one-line rationale + pointer in ai_context.
   - **(b) rationale needs landing in docs first** — the linked doc exists but does not cover this entry's rationale yet; compression includes a docs/ patch that lands the rationale **then** trims ai_context.
   - **(c) no linked doc exists** — needs a brand-new `docs/architecture/<topic>.md` file; rare; flagged in the preview so user can confirm before `Write`-ing a new file.

## Step 6: Compress single batched ask

> **Language**: user-facing — render the preview wrapper (the per-entry header lines `entry N/M: <file>:<entry-id>`, before/after snippets, docs landing target, the trailing aggregate counts) in `conversation_language` per `ai_context/skills_config.md §Language`. The patch / snippet bodies shown inside the wrapper are disk-bound — they stay in `content_language` (the language they will land in at Step 7); do not retranslate.

> **Language**: user-facing — render the `<ask tool>` prompt + option labels in `conversation_language` per `ai_context/skills_config.md §Language`. File paths, entry IDs, section headings quoted inside the prompt stay English; only surrounding prose translates.

Print every accepted compress candidate in full, each block headed with `entry N/M: <file>:<entry-id> → <classification>`. For each entry, show: before snippet (≤ 5 lines from the existing entry), after snippet (the compressed form), docs landing target (`docs/architecture/<topic>.md §<section>`, marked `(new file)` for classification (c)), landing snippet (the rationale block that will land in docs). Aggregate counts at top: `<M> entries to compress: <X> already-covered / <Y> needs-docs-landing / <Z> new-doc-file`. After all entries are printed, ask via **<ask tool>** — one question, three options:

Question: `Apply all <M> compress patches as previewed?`

1. **Confirm — apply all patches as shown (recommended)** — proceed to Step 7
2. **Tweak first — adjust wording / drop an entry / re-route docs target** — wait for the user's tweak instruction, recompose preview, re-enter Step 6
3. **Cancel — drop all compress patches** — abort the compress phase; prune-phase changes (if any) stay landed; skip to Step 8 wrap-up

The `<ask tool>`'s auto-appended "Other" fallback covers free-form responses (e.g. "apply 1 / 3 / 5, drop 2 / 4"). Option labels stay concise.

## Step 7: Compress apply

> **Language**: disk-bound — compress patches (ai_context entry shrinks + docs/ rationale landings + new-doc files) all written in `content_language` per `ai_context/skills_config.md §Language`. Snapshot files are byte-copies of source.

> **Compactness Requirements**: the compressed ai_context bodies written here follow the universal contract —
> - Shorter is better than longer. Each entry is a summary, not a detail dump.
> - Compactness must not sacrifice accuracy or completeness — never drop important information just to fit the length target.
> - Aim for ≤ 5 lines and push longer detail to the linked source (`docs/<topic>.md`, schemas, script docstrings).
> - Do not compress or touch content unrelated to the current edit.

a. **Snapshot before write**: `take_snapshot(target_root, slug='compress-ai-context-compress', file_paths=[touched ai_context + docs files])`. Invoked **immediately before** the first `Edit` of this phase. Capture the returned snapshot dir path for the wrap-up.

b. **Apply patches**:
   - For classification (a): one `Edit` per entry replacing the long form with the compressed form.
   - For classification (b): one `Edit` on the docs target landing the rationale, then one `Edit` on the ai_context entry compressing it.
   - For classification (c): one `Write` creating the new `docs/architecture/<topic>.md` (header + the rationale body), then one `Edit` compressing the ai_context entry to point at the new file. Update `docs/architecture/README.md Contents` if it exists, adding the new entry per the existing alphabetical/topical order.

c. **Print apply summary**:

```
COMPRESS applied:
- 6 entries compressed in ai_context
- 4 docs/ landings (3 appended to existing files, 1 new file: docs/architecture/<topic>.md)
SNAPSHOT: logs/file_snapshots/<YYYY-MM-DD_HHMMSS>_compress-ai-context-compress/
```

## Step 8: Verify + wrap-up

> **Language**: user-facing — render verification result lines + wrap-up summary + reminder to `/commit` in `conversation_language` per `ai_context/skills_config.md §Language`. Structural prefixes (`✓`, `✗`, `SNAPSHOT:`, file paths) stay English; only summary prose translates.

a. **External-reference sanity** — for each pruned or compressed `decisions.md` entry, grep the repo (excluding `logs/` + `docs/todo_list_archived.md`) for `decisions.md #N` references where `N` is the deleted/compressed entry's number; flag any that now point at a non-existent entry. (Compress preserves numbers, so this should be empty for compress-only runs; prune-only when "leave dangling refs" was picked will show flagged refs — expected.)

b. **Drift sanity** — `python3 scripts/holo_update_check.py --target . --plugin-root . --check` should report `total_drift = 0` (this skill does not introduce structural drift; if it does, something is wrong).

c. **Import sanity** — `python3 -c "import sys; sys.path.insert(0, 'scripts'); import holo_update_check; import sentinel_parse"` exits 0.

d. **Print wrap-up**:

```
✓ /compress-ai-context complete.
Prune: <N> pruned / <M> kept / <K> skipped (snapshot: <path>)
Compress: <X> entries compressed across <Y> files (snapshot: <path>)
Follow-up todo: T-PRUNE-DANGLING-REFS-<YYYYMMDD> (if any case picked option 1)
This skill does not commit. To persist, run /commit.
```

If `prune phase = no-op` (Step 1 = no, or Step 2 = 0 stale) and `compress phase = 0 findings`, print one line `nothing to do — ai_context is within the compactness contract` and stop without snapshots.

Do not enter `/go`, do not invoke any other skill, do not stage or commit any change.

## Constraints

- **No commit / no push** (persistence delegated to `/commit`).
- **No touching code / schema / `.gitignore` / `plugin.json` / `logs/` / `templates/`** — out of scope; touches limited to `ai_context/*.md` + `docs/architecture/<topic>.md` + `docs/todo_list.md` (only when "Auto-prune + create follow-up todo" was picked).
- **Sentinel-block protection is load-bearing** — every parse goes through `scripts/sentinel_parse.py`; this skill operates only on gap-territory content. Sentinel-bearing blocks are plugin-canonical (owned by `/holo:update`); editing them is out of scope.
- **Snapshot-on-apply, not pre-emptively** — `take_snapshot` is invoked once per phase, **immediately before** that phase's first `Edit`. Skill startup does NOT snapshot.
- **No batched confirm for stale + no live refs** — the safety net is the snapshot, not user confirmation. The only ask for the prune phase is the per-case 3-option ask for `stale + has live refs`.
- **No numbering check / no auto-reorder** — `decisions.md` global-append-only numbering is enforced by `decisions.md §Format` rule text only; this skill does not validate, fix, or rearrange numbers.
- **Compactness contract is owned by `conventions.md §Compactness Requirements`** — this skill body MUST NOT re-author the rules. Edits to the contract rule itself happen via `/go` editing `conventions.md`, not via this skill.
- **No fan-out / no multi-agent review / no PRE-POST log** — single-pass scan-and-write per phase; auditing is `/full-review`'s job. `logs/change_logs/` is `/go`-only.
