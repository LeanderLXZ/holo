---
name: todo
description: Read the `## Index` section at the top of docs/todo_list.md and render it verbatim to the user; end with "which entry do you want to see?" — trust the index (maintained by /todo-add); do not re-parse, re-bucket, or generate recommendations. $ARGUMENTS = ID keyword filter (optional). Read-only on todo_list / code; no commit. Triggers: todo / what is next / what's on the todo list / what should I do now.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (logs / docs / commit messages / code comments / files written) uses `content_language`; user-facing surface (chat prose / `AskUserQuestion` prompts and option labels / progress-tool entry `content` / status lines / strategy declarations / findings rendered in chat) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, and structural prefixes (`Step N:`, `LOG:`, etc.) stay English regardless.

# /todo — todo_list index display

Read the `## Index (auto-generated; do not hand-edit)` section at the top of `docs/todo_list.md` and render it verbatim to the user, ending with "which entry do you want to see?". **Read-only** — do not parse the body, re-bucket, generate recommendations, change todo_list, change code, or commit. `$ARGUMENTS` is an optional ID keyword filter (e.g. `schema` shows only entries whose ID contains schema); without it, show everything.

The index section is a deterministic cache, refreshed in sync by whoever maintains `docs/todo_list.md` whenever entries change (rules live in the "Index maintenance" section at the top of todo_list.md). `/todo` trusts the index and does not re-parse.

## Steps

### 1. Read the index

`Read` `docs/todo_list.md` **with `limit=100` required** — the index section is at the top of the file, and reading the whole ~700-line file slows the response significantly and wastes context. From what is read, extract the `## Index (auto-generated; do not hand-edit)` section — everything from that heading up to the next H2 heading (`## File guide`).

File missing → print "⚠️ docs/todo_list.md missing" and stop.
Index section missing (heading not found) → print "⚠️ docs/todo_list.md top is missing the index section; first backfill per the «Index maintenance» section of todo_list.md before calling /todo" and stop.
After 100 lines `## File guide` is still not seen (meaning the index section has grown past 100 lines and got truncated) → re-`Read` `docs/todo_list.md` **without `limit`** to get the full text, then extract the section from the full text; do not stop.
Index section is present but all three subtables are tagged "_(none)_" → still render normally, simply showing "no tasks yet".

### 2. Filter (optional)

If `$ARGUMENTS` is provided: in all three subtables keep rows whose ID contains the keyword (case-insensitive); drop others. If a section becomes empty after filtering, keep its heading but write "_(no matching entries)_".

No `$ARGUMENTS` → show everything.

### 3. Render

Print the index section to the user as-is. Preserve markdown tables unchanged; do not reorder, re-judge, or append recommendations.

**Skip the blockquote that immediately follows the `## Index ...` heading** (consecutive lines starting with `>` — that is meta guidance for the todo_list maintainer and is noise to `/todo` users). Subtables / summary rows after the blockquote render normally.

If filtered by `$ARGUMENTS`, append a `(filtered by keyword "<keyword>")` line at the end of the summary row.

### 4. Ask + stop

Print one final line:

```
Which entry do you want to see? Tell me the ID (e.g. `T-XXX`), or say something else.
```

After printing, **stop** — do not enter `/go`, do not change code, do not change todo_list, do not commit; wait for the user's response.

## Constraints

- **Read-only**: no file changes, no commit, no push
- **Trust the index section**: do not parse the body, re-bucket, or append recommendations; index rules have a single source of truth in the "Index maintenance" section of `docs/todo_list.md`
