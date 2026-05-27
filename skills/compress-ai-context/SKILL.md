---
name: compress-ai-context
description: Maintenance skill — scans 6 ai_context files (decisions / conventions / requirements / architecture / handoff / next_steps), optionally prunes stale entries (LLM-judged + per-case 3-option ask for `stale + has live refs`), then compresses bloated entries with rationale landing in docs/architecture/<topic>.md. Coordinator + scatter-gather flow (per-file sub-agents above threshold); sentinel-aware via sentinel_parse.py; snapshot-on-plan-freeze via take_snapshot (one per phase, before any Edit); completion-gate re-scan + multi-axis verify (semantic / density / compliance) + 3-option rollback ask. Reuses conventions.md §Compactness Requirements (does NOT re-author rules). No commit / no push. Triggers: /compress-ai-context / compress ai_context / prune stale ai_context entries.
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
docs.

**Architecture (post-T-COMPRESS-AI-CONTEXT-PARALLEL refactor)**:
coordinator + scatter-gather. The main agent owns gateway asks /
plan freeze / snapshot / docs landings / completion gate /
verification aggregation; per-file work (scan + classify + apply
on ai_context files) is dispatched to sub-agents in parallel when
total work ≥ threshold. Sub-agents never write to shared files
(docs/, README.md Contents) — those are coordinator-serial. Plan
freezes before any Edit; one `take_snapshot` per phase captures the
frozen-plan file set; rollback after the run is one `cp` away.
Sentinel-aware throughout (won't touch plugin-canonical territory).

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
> - Aim for ≤ 5 lines per entry, and push longer detail to the linked source (`docs/<topic>.md`, schemas, script docstrings).
> - Do not compress or touch content unrelated to the current edit.

a. **Snapshot-on-plan-freeze**: by the end of Step 3 the prune plan is frozen (which entries delete + whether a follow-up todo is needed). Before any `Edit`, call `take_snapshot(target_root, slug='compress-ai-context-prune', file_paths=[touched ai_context files + docs/todo_list.md if a follow-up todo will land])` **once**, covering all files in the frozen plan. Not pre-emptively at skill startup, and not piecemeal per-Edit. Snapshot root is resolved by the helper from `ai_context/skills_config.md ## File snapshots` (default `<target_root>/logs/file_snapshots/`); callers do not pass the root, the helper reads it. Capture the returned snapshot dir path for the wrap-up.

b. **Apply each pruned entry via `Edit`** (one `Edit` per entry; no batched `replace_all`). For `decisions.md` entries: do NOT renumber surviving entries (per `decisions.md §Format` global-append-only rule); just delete the offending block. For `conventions.md` rows: delete the table row only. For all 6 files: also remove any redundant surrounding `---` separator or trailing blank line if the surrounding structure breaks. Prune-phase apply stays coordinator-serial (no sub-agent dispatch) — prune touches at most a handful of entries per file and the safety bias dominates parallelism gain.

c. **Create bundled follow-up todo** (only if ≥ 1 case picked "Auto-prune + create follow-up todo"): append ONE new entry to `docs/todo_list.md ## Next` with slug like `T-PRUNE-DANGLING-REFS-<YYYYMMDD>`, body listing each dangling ref as a change-manifest bullet (file:line + short context). Update the top `## Index` Next sub-table per `docs/todo_list.md "## File guide → Index maintenance"` rules.

d. **Print apply summary**:

```
PRUNE applied:
- 1 orphan entry deleted (no live refs)
- 1 entry deleted + dangling refs (logged in T-PRUNE-DANGLING-REFS-20260521)
- 1 entry kept (user picked Skip)
SNAPSHOT: <snapshot_root>/<YYYY-MM-DD_HHMMSS>_compress-ai-context-prune/   (default snapshot_root = logs/file_snapshots/)
```

## Step 5: Compress scan + plan freeze (scatter-gather)

> **Language**: user-facing — render the scan summary printed to the conversation in `conversation_language` per `ai_context/skills_config.md §Language`. Structural labels stay English.

**Trigger** (per file): file > 150 lines OR any single entry > 5 lines. Files matching neither are skipped silently.

a. **Coordinator pre-scan**: parse each of the 6 ai_context files via `scripts/sentinel_parse.py` (gap-territory only, same as Step 2). For each file, count "bloated entries" cheaply (entries > 5 lines + whether file body > 150 lines). Sum to `<total_bloated>`.

b. **Dispatch decision**:
   - `<total_bloated> ≥ 8` → **scatter mode**: dispatch up to 6 sub-agents in parallel, one per file that has ≥ 1 bloated entry. Each sub-agent receives: (i) its file path; (ii) the gap-territory content; (iii) the §Compactness Requirements contract; (iv) the classification rubric (a)/(b)/(c) below; (v) the language-axes directive at the **tail** of its prompt per `ai_context/conventions.md §Cross-File Alignment` (sub-agent dispatch tail-position rule, decisions.md #16). Sub-agents must read `ai_context/conventions.md §Compactness Requirements` before classifying.
   - `<total_bloated> < 8` → **inline mode**: coordinator runs the per-entry classification serially. No sub-agent dispatch.

c. **Per-entry classification** (executed by sub-agent in scatter mode, by coordinator in inline mode):
   1. **Identify the linked-doc target** — typically the entry's `→` pointer line (`→ docs/architecture/<topic>.md`); or, when the entry has no explicit pointer, grep `docs/` for the entry's key terms to find a plausible existing doc. If no target exists, the new-doc creation case (rare).
   2. **Classify** as:
      - **(a) doc already covers rationale** — the linked doc already documents the design / rationale this entry contains; compression simply removes the duplication, leaving a one-line decision + one-line rationale + pointer in ai_context.
      - **(b) rationale needs landing in docs first** — the linked doc exists but does not cover this entry's rationale yet; compression includes a docs/ patch that lands the rationale **then** trims ai_context.
      - **(c) no linked doc exists** — needs a brand-new `docs/architecture/<topic>.md` file; rare; flagged in the plan so user can confirm before `Write`-ing a new file.
   3. **Propose the patch** (does NOT Edit anything in this step) — record the proposed compressed body for ai_context + the proposed docs landing block + the docs target path + classification tag.

d. **Plan merge + docs-landing conflict resolution** (coordinator-owned, executed after sub-agents return / inline mode collects all proposals):
   - Aggregate all proposals into a single plan: `{file_path: [proposed_edits], docs_landings: [{target, classification, body}], new_doc_files: [path]}`.
   - **Conflict resolution**: when multiple ai_context entries land rationale into the same `docs/architecture/<topic>.md`, the coordinator owns the merge order and produces a single combined docs Edit for that target (preserving section ordering, deduping overlapping rationale). Sub-agents do NOT see other sub-agents' proposals; conflict resolution is exclusively coordinator-side.
   - **Plan freeze**: by the end of Step 5d, the full set of files to be touched (ai_context source files + docs targets + new doc files + possibly `docs/architecture/README.md` Contents) is fixed. This frozen file list feeds Step 7's snapshot call.

e. **Print scan summary to conversation** (replaces the verbose per-entry preview that the prior design printed; full preview is moved to Step 6 in summary form only):

```
COMPRESS scan:
- ai_context/decisions.md: 8 entries scanned, 3 bloated (2 already-covered / 1 needs-docs-landing)
- ai_context/architecture.md: 4 entries scanned, 1 bloated (1 already-covered)
- ai_context/conventions.md: 6 entries scanned, 0 bloated
- ai_context/requirements.md: 3 entries scanned, 0 bloated
- ai_context/handoff.md: 5 entries scanned, 0 bloated
- ai_context/next_steps.md: 2 entries scanned, 0 bloated
Total: 4 bloated entries across 2 files (scatter mode: 6 sub-agents dispatched / inline mode)
Docs landings: docs/architecture/section-version-sentinel.md (+rationale block); docs/architecture/smart-merge.md (+rationale block); (NEW) docs/architecture/<topic>.md
```

If `Total: 0 bloated`, skip to Step 8 with a one-line `0 bloated entries found, compress phase no-op` notice.

## Step 6: Simple plan report + single batched ask

> **Language**: user-facing — render the plan report (per-file entry-ID one-liners + docs landing schedule + classification counts) and the `<ask tool>` prompt + option labels in `conversation_language` per `ai_context/skills_config.md §Language`. File paths, entry IDs, classification tags `(a)` / `(b)` / `(c)`, section headings, and the `(NEW)` marker stay English as structural labels; only surrounding prose translates.

**Print a simple plan report** (per-entry one-liner; do NOT print before/after snippets, do NOT print landing-block bodies — the safety net is the snapshot taken at Step 7a + Step 8's multi-axis verify + rollback ask, not pre-confirmation preview):

```
COMPRESS plan (<M> entries to compress: <X> already-covered / <Y> needs-docs-landing / <Z> new-doc-file):
- ai_context/decisions.md:
  - #13 → (a) docs/architecture/section-version-sentinel.md
  - #14 → (b) docs/architecture/smart-merge.md
  - #15 → (a) docs/architecture/section-version-sentinel.md
- ai_context/architecture.md:
  - §Key Boundaries.sentinel-ownership → (a) docs/architecture/section-version-sentinel.md
Docs landing schedule (coordinator-owned, serial):
- docs/architecture/section-version-sentinel.md — 3 entries (0 need new rationale)
- docs/architecture/smart-merge.md — 1 entry (1 needs new rationale appended)
- (NEW) docs/architecture/<topic>.md — only present if classification (c) appeared
docs/architecture/README.md Contents update: yes / no (yes if any (c))
Snapshot target: <snapshot_root>/<YYYY-MM-DD_HHMMSS>_compress-ai-context-compress/   (default snapshot_root = logs/file_snapshots/, configurable via ai_context/skills_config.md ## File snapshots)
```

Per-entry one-liner format: `<entry-id> → <classification>(a/b/c) <docs-target-path>`. No body text. The classification tag is sufficient for the user to spot mis-classification (e.g. an entry tagged (b) "needs docs landing" when the linked doc already covers the rationale).

Ask via **<ask tool>** — one question, three options:

Question: `Proceed with compress plan above?`

1. **Confirm — apply plan as shown (recommended)** — proceed to Step 7
2. **Tweak first — adjust specific entries** — wait for the user's free-form tweak instruction (typical: "drop entry X", "re-route entry Y to docs/<other>.md", "rework entry Z classification (b) → (a) because the rationale is already covered"); coordinator updates the plan, re-prints the simple report, re-enters Step 6
3. **Cancel — drop all compress patches** — abort the compress phase; prune-phase changes (if any) stay landed; skip to Step 8 wrap-up

The `<ask tool>`'s auto-appended "Other" fallback covers free-form responses (e.g. "apply 1 / 3 / 5, drop 2 / 4"). Option labels stay concise. **Do not regress to per-entry full-preview** — full preview defeats the simple-report contract; users who need to see the proposed body should run `/compress-ai-context`, then inspect the snapshot diff after Step 7 lands and use the Step 8 rollback ask to revert specific entries.

## Step 7: Compress apply (scatter-gather) + completion gate

> **Language**: disk-bound — compress patches (ai_context entry shrinks + docs/ rationale landings + new-doc files) all written in `content_language` per `ai_context/skills_config.md §Language`. Snapshot files are byte-copies of source. Sub-agent prompts dispatched in Step 7b include the language-axes directive at the **tail** of the prompt per `ai_context/conventions.md §Cross-File Alignment` (sub-agent dispatch tail-position rule, decisions.md #16) — reply in `conversation_language`, write disk artifacts in `content_language`.

> **Compactness Requirements**: the compressed ai_context bodies written here follow the universal contract —
> - Shorter is better than longer. Each entry is a summary, not a detail dump.
> - Compactness must not sacrifice accuracy or completeness — never drop important information just to fit the length target.
> - Aim for ≤ 5 lines per entry, and push longer detail to the linked source (`docs/<topic>.md`, schemas, script docstrings).
> - Do not compress or touch content unrelated to the current edit.

a. **Snapshot-on-plan-freeze**: by the end of Step 6 the compress plan is frozen (per-file entry list + docs landing schedule + new-doc files + `docs/architecture/README.md` Contents flag). Before any `Edit`, call `take_snapshot(target_root, slug='compress-ai-context-compress', file_paths=[every ai_context file touched + every docs/ landing target + every new-doc path + docs/architecture/README.md if Contents update is scheduled])` **once**, covering all files in the frozen plan. Not piecemeal per-sub-agent, not piecemeal per-Edit. Snapshot root resolved from `ai_context/skills_config.md ## File snapshots` (default `logs/file_snapshots/`). Capture the returned snapshot dir path for the wrap-up.

b. **Sub-agent apply (parallel, ai_context only)**: dispatch one sub-agent per ai_context file that has ≥ 1 entry in the compress plan (max 6 in parallel; threshold same as Step 5b — scatter mode dispatches sub-agents, inline mode runs Step 7b coordinator-side serially). Each sub-agent receives:
   - Its file path + the exact list of `(entry-id, classification, compressed_body)` triples for that file (from the frozen plan).
   - The §Compactness Requirements blockquote copied verbatim into its prompt.
   - The instruction: **only Edit your assigned ai_context file**; do NOT Edit docs/, README.md, or any file outside your scope. Use one `Edit` per entry (no batched `replace_all`).
   - The language-axes directive at the **tail** of the prompt (reply in `conversation_language`; disk Edits in `content_language`).
   Sub-agents return per-entry success/failure to the coordinator. **Sub-agents do NOT see other sub-agents' files** — there is no cross-agent coordination at this layer.

c. **Coordinator apply (serial, docs / new-doc / Contents)**: after all sub-agents return success, the coordinator applies the docs landing schedule **serially**:
   - For each `docs/architecture/<topic>.md` in the docs landing schedule: one `Edit` appending the combined rationale block produced by Step 5d's conflict resolution (single Edit per docs file regardless of how many ai_context entries land there).
   - For each new-doc path (classification (c)): one `Write` creating `docs/architecture/<topic>.md` with header + rationale body.
   - If any new-doc was created and `docs/architecture/README.md` exists: one `Edit` updating its Contents index, inserting the new entry per the file's existing alphabetical / topical order.
   Serial execution is deliberate — multiple parallel writers on the same docs file would last-writer-wins; serialization is the simplest correct path and docs edits are cheap.

d. **Completion gate (re-scan)**: re-run the Step 5 trigger check across the 6 ai_context files (file > 150 lines OR any single entry > 5 lines). If any bloated entry remains:
   - **Fail loudly**: print `COMPRESS completion-gate FAILED:` followed by the residual entry list (file:entry-id + reason: file-still-too-long / entry-still-too-long).
   - Do NOT silently exit. The user can choose: (i) re-run `/compress-ai-context` (will pick up the residue); (ii) accept the residue as inherently-uncompressible (e.g. a table row that legitimately exceeds 5 lines); (iii) roll back via Step 8's rollback ask.
   - This gate exists because the original single-agent design exhibited "compress only a small subset per invocation" behavior; the scatter-gather + completion gate combo is the architectural answer to that pain point.

e. **Print apply summary**:

```
COMPRESS applied:
- 6 entries compressed across 4 ai_context files (sub-agents: 4 dispatched, 0 failed / coordinator inline)
- 4 docs/ landings (3 appended to existing files, 1 new file: docs/architecture/<topic>.md)
- docs/architecture/README.md Contents updated: yes / no
Completion gate: ✓ no residue (or: ✗ N residual bloated entries — see list above)
SNAPSHOT: <snapshot_root>/<YYYY-MM-DD_HHMMSS>_compress-ai-context-compress/   (default snapshot_root = logs/file_snapshots/)
```

## Step 8: Multi-axis verify + rollback ask + wrap-up

> **Language**: user-facing — render verification result lines (✓ / ✗ per axis), the rollback `<ask tool>` prompt + option labels, the wrap-up summary, and the reminder to `/commit` in `conversation_language` per `ai_context/skills_config.md §Language`. Structural prefixes (`✓`, `✗`, `SNAPSHOT:`, file paths, `axis:`) stay English; only summary prose translates.

> **Language (sub-agent dispatch)**: sub-agents spawned in Step 8b receive the language-axes directive at the **tail** of their prompt per `ai_context/conventions.md §Cross-File Alignment` (sub-agent dispatch tail-position rule, decisions.md #16) — reply in `conversation_language`; no disk writes expected from verify sub-agents (they are read-only by contract).

### a. Scripted fast-fail (always runs)

These checks are cheap and deterministic; any failure here means the apply phase broke something structural and the user should likely rollback before proceeding.

1. **Sentinel integrity**: `python3 scripts/sentinel_parse.py --self-test` (12-group regression). Failure → flag `axis: sentinel — script self-test FAILED`.
2. **Sentinel parse on touched files**: for each ai_context file touched by this run, re-parse via `scripts/sentinel_parse.py`'s `parse(path)`; failure → flag `axis: sentinel — <path> parse FAILED`. The Edits in Step 7 are confined to gap-territory so this should not break sentinels; if it does, something went wrong.
3. **Drift sanity**: `python3 scripts/holo_update_check.py --target . --plugin-root . --json` produces a JSON dict where every finding-category list is empty (`agents_sync.stale/missing/orphan = []`, `missing_template = []`, `missing_section = []`, `missing_field = []`, `gitignore_missing_lines = []`, `claude_agents_lang_drift = []`, `missing_l1_directive = []`, `l1_directive_drift = []`, `lang_mirror_drift = []`, `legacy_skip_marker = []`, `sentinel_layout_drift = []`). Any non-empty list → flag `axis: drift — <category>: <N> findings` with the JSON snippet. (The no-arg invocation is the script's check mode; `--fix` enables the auto-fix branch — this skill does NOT pass `--fix` here.)
4. **Import sanity**: `python3 -c "import sys; sys.path.insert(0, 'scripts'); import holo_update_check; import sentinel_parse"` exits 0. Failure → flag `axis: import — <error>`.
5. **External-reference sanity** — for each pruned `decisions.md` entry, grep the repo (excluding `logs/` + `docs/todo_list_archived.md`) for `decisions.md #N` references where `N` is the deleted entry's number; flag any that now point at a non-existent entry. (Compress preserves numbers — this is empty for compress-only runs; prune with "leave dangling refs" picked produces expected flagged refs that DO NOT count as a verify failure.)

Any failure in scripts 1–4 → print the failure summary and jump directly to the **rollback ask** in Step 8c without dispatching the LLM sub-agents (their work is moot if the apply phase is structurally broken).

### b. LLM multi-axis verify (parallel sub-agents)

**Scope**: compress-phase entries only; prune-phase deletions are covered by Step 8a's external-ref grep (#5). The three axes below (semantic preservation / information density / compactness compliance) are defined for *compressed* entries — they have no meaning on deleted entries, so prune-phase changes do not enter this LLM verify.

**Threshold**: dispatch when `compress entries ≥ 5`. Below that, the coordinator runs the three LLM checks inline serially (small-batch overhead from sub-agent dispatch outweighs parallelism gain).

Three sub-agents dispatched in parallel, each read-only (no Edits, no Writes). Each sub-agent receives:
- The snapshot dir path (`<snapshot_root>/<...>_compress-ai-context-compress/`; `<snapshot_root>` resolved per `ai_context/skills_config.md ## File snapshots`, default `logs/file_snapshots/`).
- The current state of the ai_context + docs files touched this round.
- The §Compactness Requirements blockquote.
- The language-axes directive at the **tail** of its prompt.

**Sub-agent 1 — semantic preservation**: read snapshot copy of each touched ai_context file + current state. For each compressed entry, judge: did the compression drop any fact / constraint / decision / rationale that is NOT now reflected in either (a) the linked docs target or (b) the surviving compressed body? Flag any drop as `axis: semantic — <file>:<entry-id> dropped: <quote of dropped content>`.

**Sub-agent 2 — information density**: read current state of touched ai_context entries. For each compressed entry, judge: is the body over-compressed to the point of losing actionable meaning (e.g. shrunk to "see docs" with no decision summary, or a single sentence too abstract to navigate)? The contract is `≤ 5 lines aim`, NOT `1 line ceiling` — compression that ABSTRACTS without LANDING the rationale to docs is over-compression. Flag: `axis: density — <file>:<entry-id> over-compressed: <reason>`.

**Sub-agent 3 — compactness compliance**: read current state of touched ai_context entries against `ai_context/conventions.md §Compactness Requirements` 4 rules + the §Format pointer requirement + `docs/architecture/<topic>.md` existence + section presence. For each compressed entry, judge: (i) does the entry end with a `→ <pointer>` line? (ii) does the pointer target exist? (iii) if the pointer names a section (`→ docs/architecture/<topic>.md §<section>`), does that section exist in the target? Flag: `axis: compliance — <file>:<entry-id> <which-rule-failed>`.

Coordinator aggregates the three sub-agent reports into a single findings list.

### c. Rollback ask (only when any axis flagged)

If steps a–b produced **any** flagged finding (including expected dangling-refs from prune option 2; the user still gets to decide acceptance):

Print the consolidated findings list, grouped by axis, then ask via **<ask tool>** — one question, three options:

Question: `<N> verification findings flagged across <M> axes. How to handle?`

1. **Accept — keep changes as-is, warning only (recommended when findings are intentional / minor)** — the round stays landed; flagged findings echoed in the wrap-up summary as warnings; user follows up later if needed.
2. **Partial rollback — restore specific entries from snapshot** — wait for the user's per-entry instruction (e.g. "rollback decisions.md #14 + #15"); coordinator `cp` the specified entries' enclosing files from the snapshot dir back to the working tree, refreshing the affected files entirely (snapshot copies the whole file, not entry-level). Print which files were restored. After partial rollback, re-run **Step 8a scripted fast-fail only** (cheap re-validation) to confirm no new structural break; if scripted checks pass, proceed to wrap-up; if they fail, surface the failure and let the user decide.
3. **Full rollback — restore all touched files from snapshot** — `cp` the entire snapshot dir contents back over the working tree (or use the snapshot helper's restore primitive if one exists); the compress phase is effectively reverted. Prune-phase changes (if any) stay landed — they have a separate snapshot. Print `COMPRESS phase fully rolled back from snapshot <path>`. Skip directly to the wrap-up.

**No-findings path**: if both 8a and 8b are clean, print `✓ all verification axes clean` and proceed directly to wrap-up (no ask needed).

### d. Wrap-up

```
✓ /compress-ai-context complete.
Prune: <N> pruned / <M> kept / <K> skipped (snapshot: <path>)
Compress: <X> entries compressed across <Y> files (snapshot: <path>)
Completion gate: ✓ no residue (or: ✗ N residual — see Step 7d list)
Verify: <V> axes checked, <F> findings flagged (action: accept / partial rollback <files> / full rollback)
Follow-up todo: T-PRUNE-DANGLING-REFS-<YYYYMMDD> (if any prune case picked option 1)
This skill does not commit. To persist, run /commit.
```

If `prune phase = no-op` (Step 1 = no, or Step 2 = 0 stale) AND `compress phase = 0 findings` (Step 5 found nothing bloated), print one line `nothing to do — ai_context is within the compactness contract` and stop without snapshots.

Do not enter `/go`, do not invoke any other skill, do not stage or commit any change.

## Constraints

- **No commit / no push** (persistence delegated to `/commit`).
- **No touching code / schema / `.gitignore` / `plugin.json` / `logs/` / `templates/`** — out of scope; touches limited to `ai_context/*.md` + `docs/architecture/<topic>.md` (+ `docs/architecture/README.md` Contents when a new doc is created) + `docs/todo_list.md` (only when "Auto-prune + create follow-up todo" was picked).
- **Sentinel-block protection is load-bearing** — every parse goes through `scripts/sentinel_parse.py`; this skill operates only on gap-territory content. Sentinel-bearing blocks are plugin-canonical (owned by `/holo:update`); editing them is out of scope. Step 8a re-parses every touched file to catch any accidental sentinel break.
- **Snapshot-on-plan-freeze, not snapshot-on-apply** — `take_snapshot` is invoked once per phase, **after that phase's plan is frozen (end of Step 3 for prune; end of Step 6 for compress) and before any `Edit`**, covering all files in the frozen plan in a single call. Skill startup does NOT snapshot. Sub-agents in Step 7b do NOT call `take_snapshot` — the snapshot precedes their dispatch.
- **Coordinator owns shared-file writes** — sub-agents (Step 5b scan / Step 7b apply) write only to their assigned ai_context file. Docs / new-doc / `docs/architecture/README.md` Contents writes are coordinator-serial in Step 7c. This is a load-bearing invariant against parallel-writer races on shared docs targets.
- **Sub-agents do NOT call `take_snapshot` and do NOT write to shared files** — Step 5b scan sub-agents, Step 7b apply sub-agents, and Step 8b verify sub-agents are all forbidden from invoking `take_snapshot` (snapshot is coordinator-driven at the end of each phase's plan-freeze, in Step 4a / Step 7a) and from writing to shared files (`docs/`, `README.md`, `docs/architecture/README.md`, etc.). Step 7b sub-agents write only to their assigned ai_context file; Step 8b sub-agents are read-only by contract.
- **Completion contract: compress Step 7d re-scan** — after Step 7 apply, the coordinator re-runs the Step 5 trigger (file > 150 lines OR any entry > 5 lines). Residual bloated entries → fail loudly; do not silently exit. This gate makes "compressed only a small subset" failures visible.
- **No batched confirm for stale + no live refs** — the safety net is the snapshot + Step 8 verify + rollback ask, not user pre-confirmation. The only ask in the prune phase is the per-case 3-option ask for `stale + has live refs`. The only ask in the compress phase is the Step 6 simple-plan 3-option ask + the conditional Step 8c rollback ask.
- **No per-entry preview in Step 6** — the safety net is the snapshot + Step 8 multi-axis verify + rollback ask, not preview-then-confirm. Step 6 prints a simple plan report (per-entry one-liner: id + classification + docs target) without body content. Reverting to full per-entry preview is a contract regression.
- **Sub-agent dispatch thresholds** — Step 5/7 scatter mode requires `total_bloated ≥ 8`; Step 8b multi-axis verify requires `compress entries ≥ 5`. Below these, the coordinator runs the phase inline serially. Thresholds exist to avoid dispatch overhead on small jobs.
- **No numbering check / no auto-reorder** — `decisions.md` global-append-only numbering is enforced by `decisions.md §Format` rule text only; this skill does not validate, fix, or rearrange numbers.
- **Compactness contract is owned by `conventions.md §Compactness Requirements`** — this skill body MUST NOT re-author the rules. Edits to the contract rule itself happen via `/go` editing `conventions.md`, not via this skill.
- **No fan-out / no PRE-POST log** — auditing of cross-file alignment is `/full-review`'s job. `logs/change_logs/` is `/go`-only. The Step 8 multi-axis verify is THIS round's verify (scoped to the touched file set), not a cross-repo review.
