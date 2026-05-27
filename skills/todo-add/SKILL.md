---
name: todo-add
description: Add an item just decided / discussed in the session to docs/todo_list.md — semantic-match decides UPDATE vs CREATE (existing entry → update; otherwise CREATE new T-XXX). $ARGUMENTS = segment (next / discuss / executing; default: UPDATE keeps existing / CREATE goes to Next). On CREATE, dedup against todo_list.md + todo_list_archived.md; on UPDATE, ID stays. Preview (CREATE full text / UPDATE field diff + segment change) → confirm → write → refresh top-of-file Index. No commit / no push (→ /commit or /go). Triggers: add to todo / register todo / todo-add / put it in next / put it in discussing / update todo.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (the todo entry inserted into `docs/todo_list.md`, the `## Index` refresh, the `**Updated**` field, any change-log lines) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / preview wrappers / wrap-up status line) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, and structural prefixes (`Step N:`, `T-XXX`, `### [T-XXX]`, segment headings like `## Next`) stay English regardless.

# /todo-add — Add session discussion result to todo_list

Add an item just discussed / decided in the current session to `docs/todo_list.md`: **if a
corresponding entry exists, update it** (switch segment if needed); **if it does not exist, create
a new one**. The target segment can be specified via `$ARGUMENTS`. **No commit** — persistence is
delegated to `/commit` or `/go`.

## Progress reporting

> **Language**: progress-tool entries (`content` field) are user-facing — write them in `conversation_language` per `ai_context/skills_config.md §Language`. The `Step N:` prefix stays English (structural label); subtitle text after the colon translates to `conversation_language`.

The flow below is split into `## Step 1:` ~ `## Step 7:`.

**Before entering Step 1**: call **<progress tool>** to pre-register all of Step 1 ~ Step 7 (one entry per step, `content` = `Step N: <sub-section title>`, `status` = `pending` for all). This is a hard requirement — **do not proceed without calling <progress tool>**.

Each time you enter a step: call **<progress tool>** to flip the current step to `in_progress` (mark the previous step `completed` in the same call), then do the real work. **Do not skip the call across step boundaries**. Progress is rendered directly by the <progress tool> UI — **do not print `[/todo-add] Step N: ...` style progress lines in the conversation**.

Skipping a step: call **<progress tool>** to mark the entry directly `completed`, and print one line `Step N skipped (reason: …)` in the conversation — "reason" is information the UI lacks, keep that line; do not silently skip.

Final step completion: call **<progress tool>** to mark the last entry `completed`.

**<progress tool> resolution**: Claude → `TodoWrite` (rendered as "Update Todos"); Codex → `update_plan`; other runtimes (no structured progress tool, e.g. Copilot agent mode) → maintain a markdown checkbox list in the response text as step state, rewriting the whole block on every state change. Semantic alignment: pre-register + flip state + mark complete.

**<ask tool> resolution**: Claude → `AskUserQuestion` (max 4 questions per call, batch beyond); other runtimes (no structured ask tool, e.g. Codex / Copilot agent mode) → enumerate questions + options per question in the response text and let the user answer in one pass (still max 4 per batch, batch beyond).

## Step 1: Parse $ARGUMENTS (target segment)

| Value | Target segment |
|---|---|
| Not passed / `next` / `next-step` | `## Next` |
| `discuss` / `discussing` | `## Discussing (Undecided)` |
| `executing` / `in-progress` | `## In Progress` (single slot, see Step 6 for limit) |

Illegal value → print "segment `<val>` not recognized, allowed: Next / Discussing / In Progress" and stop.

When `$ARGUMENTS` is not passed: UPDATE mode defaults to the existing segment; CREATE mode defaults to
"Next".

## Step 2: Lock the item to register

> **Language**: user-facing — render the gap-filling question to the user in `conversation_language` per `ai_context/skills_config.md §Language`. Structural label `T-XXX` stays English; only the question prose translates.

From the last few turns of the current session, grab the "item" to register — typically the specific
problem + conclusion + trigger that the user just decided / discussed.

When information is insufficient (missing motivation / status / trigger chain / change-direction) **actively
ask the user to fill the gap** — "Which discussion is being registered? Add a sentence or two of key
background / trigger / desired outcome." Do not guess, do not stitch on the user's behalf.

## Step 3: Decide UPDATE vs CREATE

> **Language**: user-facing — render the disambiguation `<ask tool>` prompt and option labels in `conversation_language` per `ai_context/skills_config.md §Language`. ID prefixes (`T-AAA`, `T-BBB`) stay English as file-side labels; only the question prose and option label prose translate.

Grab the full set of existing entries from the two paths declared at `ai_context/skills_config.md ## Activity sources.TODO list.Path` (live) and `## Activity sources.Archived TODO list.Path` (archive):
`grep -hoE 'T-[A-Z0-9-]+' <todo_list_path> <archived_todo_list_path> | sort -u`
to get the ID set; and read the titles + context of existing entries, do a **semantic match** to
judge whether the item to register corresponds to an existing entry (by content intent, not just
literal ID).

Decision:

- **UPDATE mode**: a matching entry found → record the existing `T-XXX` + existing segment
  + existing entry content snapshot (for Step 4/5 diff). If more than one suspected match, ask via
  **<ask tool>** — one question with each suspected match as one option (label: `Update T-AAA: <title>` / `Update T-BBB: <title>`, max 3 matches) plus a final `Create new entry instead` option.
  Do not decide for the user.
- **CREATE mode**: no match found → distill a new `T-XXX` slug from content intent (short English
  code, all uppercase + hyphens), non-colliding with the existing ID set; rename on collision.

Segment decision in UPDATE mode:

- `$ARGUMENTS` explicitly passes a segment → obey (even on cross-segment move)
- `$ARGUMENTS` not passed → default to the existing segment; but if this round's discussion
  **strongly implies** a segment change (typical: Discussing entry just decided → should move to Next / Next entry
  has `/go` started → should move to In Progress), then suggest the move in Step 5 preview and ask the user.

## Step 4: Compose entry draft / change diff

> **Language**: disk-bound — the entry draft / change diff being composed here will land in `docs/todo_list.md` at Step 6 and is therefore disk-bound from the moment of composition. Write the draft text (title, **Context**, **Done criteria**, **Dependencies**, **Updated**, segment-specific fields) in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names, segment headings (`### [T-XXX]`, `**Updated**`) stay English regardless. The Step 5 preview wraps this draft in user-facing prose — wrapper prose translates to `conversation_language`, draft content stays in `content_language`.

**CREATE mode**: compose the full entry per the target segment's field requirements. Shared by all segments:

- T-XXX ID + short title (in this project's `content_language`)
- **Context**: motivation + status + trigger chain
- **Requirements** (optional; positioned between **Context** and **Change manifest**): what the user wants done / what effect to achieve. Plain prose, no special format rules. Include when this session converged user-facing requirements worth preserving.
- **Solution details** (optional; positioned between **Requirements** and **Change manifest**): the final converged plan — what the solution is, what parts compose it. **Only the final converged version** — do NOT include rejected alternatives or debate history. Plain prose, no special format rules. Include when this session converged a concrete plan worth preserving.
- **Done criteria**
- **Dependencies**
- Updated-time field (label per `ai_context/skills_config.md ## Activity sources.TODO list.Per-entry updated-time field`, typically `**Updated**`): YYYY-MM-DD HH:MM timezone abbreviation (per skills_config.md `## Timezone`), on CREATE = current moment

Per-segment differences:

- **Next**: must include **change list** (file paths / line numbers / change points), single source, no gaps
- **Discussing**: must include **open decisions** (numbered list, 1–2 sentences each); change list may be deferred
- **In Progress**: requires **start time** (YYYY-MM-DD HH:MM timezone abbreviation — per
  skills_config.md `## Timezone`) + **current status** (in progress / awaiting user decision / paused)

Add as appropriate: **estimate** / **why not landed** / **not doing for now**.

Follow the format of existing entries in `docs/todo_list.md` ("### \[T-XXX\] short title" header,
field titles as `**field name**`).

**UPDATE mode**: take the existing entry as baseline and merge the new info from this round in.
Unchanged fields **stay verbatim**, do not restate; changed fields are explicitly marked. On
segment change, fill in any missing fields per **target segment** field requirements (e.g. Discussing → Next must add **change list**).
**The updated-time field (label per `ai_context/skills_config.md ## Activity sources.TODO list.Per-entry updated-time field`, typically `**Updated**`) is always refreshed = current moment** (per skills_config.md `## Timezone`); if the existing entry lacks the field (legacy format), backfill it in the same pass.

## Step 5: Preview to user + wait for confirmation

> **Language**: user-facing — render the preview wrapper (the "will register / will update" lead-in prose, the field-level diff narration, the segment-change narration) in `conversation_language` per `ai_context/skills_config.md §Language`. The draft entry text **shown inside** the wrapper is disk-bound — it stays in `content_language` (the language it will land in at Step 6); do not retranslate the draft to match the wrapper.

> **Language**: user-facing — render the `<ask tool>` prompt and option labels in `conversation_language` per `ai_context/skills_config.md §Language`. Segment names and entry IDs quoted inside the prompt / labels (`"In Progress"` / `T-XXX`) stay English as file-side labels; only the surrounding prose translates.

First print the preview, then ask via **<ask tool>** — one question, options differ per mode. The "Other" fallback that the ask tool auto-appends covers any free-form tweak the structured options don't enumerate (field add / field rename / ID rewrite / segment override etc.) — option labels stay concise rather than enumerating every possible edit.

**CREATE mode**: print the full composed entry + target segment, then ask via **<ask tool>**:

Question: `Register to "<target segment>" like this?`

1. **Confirm — write entry as previewed (recommended)** — proceed to Step 6 and write to the target segment
2. **Tweak first — fields / ID / segment** — wait for user's tweak instruction, recompose draft, re-enter Step 5
3. **Cancel — drop the draft** — abort the skill, no write

**UPDATE mode**: print **change summary** — explicitly say "will update existing entry `T-XXX`",
listing:

- **Field-level diff**: which fields changed, concise before/after (do not restate the full text
  of unchanged fields, one-liner is enough)
- **Segment change** (if any): explicit `from <original segment> → to <target segment>`
- **ID unchanged** (unless user explicitly asks to change the ID)

Then ask via **<ask tool>**:

Question: `Update T-XXX like this?`

1. **Confirm — apply update as previewed (recommended)** — proceed to Step 6 and write the merged entry
2. **Tweak first — fields / cancel segment change / change ID** — wait for user's tweak instruction, recompose, re-enter Step 5
3. **Force CREATE instead — register as new T-YYY** — flip to CREATE mode, re-enter Step 4 then Step 5
4. **Cancel — drop the update** — abort the skill, no write

**Neither mode writes the file before confirmation**.

## Step 6: Write to todo_list.md

> **Language**: disk-bound — write this entry inserted into `docs/todo_list.md` segment + the `## Index` section refresh in `content_language` per `ai_context/skills_config.md §Language`. Segment headings (`## Next`, `## Discussing (Undecided)`, `## In Progress`, `## Index (auto-generated; do not hand-edit)`), the `### [T-XXX]` entry heading, the `**field name**` labels, and the `T-XXX` ID stay English regardless. Code identifiers, file paths, field names stay English regardless.

After confirmation:

**CREATE mode**:

a. Locate the target segment (`## In Progress` / `## Next` / `## Discussing (Undecided)`), append
   the entry under `### [T-XXX] short title` heading to the **end** of that segment (within-segment
   priority is user-driven; new entries default to the tail unless the user says "insert at the front").
   Entries are separated by `---` (consistent with existing convention)

b. **In Progress** segment single slot: before writing, grep the segment's existing `### \[T-` count;
   if non-zero, **refuse to write** and prompt "In Progress segment is occupied, finish committing the
   current one or move it back to Next before starting a new task"

**UPDATE mode**:

a. **Same-segment update**: locate the `### [T-XXX]` block (including all its fields, up to the next
   `### [T-` or segment end), replace the whole block with the new version. Other segments untouched.

b. **Cross-segment move**: delete the whole `### [T-XXX]` block from the original segment (along with
   any redundant surrounding `---` separator), append to the end of the target segment per CREATE
   mode a. The **In Progress** single-slot limit applies equally — refuse the move if the target
   segment is non-empty, with the same prompt as above.

**Unified refresh**: segments that changed (CREATE target segment / UPDATE same segment or source+target segments)
+ the top-of-file `## Index (auto-generated; do not hand-edit)` segment — refresh the relevant
sub-table rows + summary row per the column rules and field-inference rules defined in
`docs/todo_list.md` "## File guide → Index maintenance" section; this skill **does not restate the rules**,
that section is the single source of truth.

## Step 7: Wrap-up report

> **Language**: user-facing — render the wrap-up status line (✓ registered / ✓ updated / ✓ moved), the Index-refresh delta line, and the "no commit; run /commit or /go" reminder in `conversation_language` per `ai_context/skills_config.md §Language`. Structural prefixes (`✓`, `T-XXX`, segment headings quoted from the file like `"In Progress"`) stay English; only surrounding prose translates.

Print (pick one based on this round's mode):

- **CREATE**: ✓ registered `T-XXX` into "<segment>"
- **UPDATE same-segment**: ✓ updated `T-XXX` ("<segment>")
- **UPDATE cross-segment**: ✓ updated `T-XXX` and moved (<original segment> → <new segment>)

Followed by:

- Index refresh: changed sub-table row count X → Y, summary N → N' (CREATE: N+1; UPDATE same-segment: unchanged; UPDATE cross-segment: each sub-table ±1)
- Reminder: "This skill does not commit. To persist, run /commit or /go."

Do not enter /go, do not commit, do not push.

## Constraints

- **No commit / no push** (persistence delegated to `/commit` or `/go`)
- **UPDATE takes priority over CREATE**: if an existing entry can be matched, update; on multiple suspected matches or CREATE
  missing key fields, **actively ask the user**, do not decide for them
- **In Progress single slot**: refuse to write (CREATE) / refuse the move (UPDATE cross-segment) if the segment is non-empty
- **Index rules single source**: see `docs/todo_list.md` "Index maintenance" section
