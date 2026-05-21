---
name: full-review
description: Whole-repo alignment audit — scan ai_context / docs / schema / prompts / code / sample artifacts, find cross-file inconsistencies, legacy residue, doc-vs-implementation drift, state-machine gating gaps, latent bugs. $ARGUMENTS = focus / extra concerns for this round (optional). Findings are sorted by severity and archived to logs/review_reports/. Audit only, no code changes; to land changes → /go; for a single change → /post-check. Triggers: full repo review / alignment audit / full-review / run a review pass.
---

> **Language**: per `ai_context/skills_config.md §Language` — disk-bound output (the review report file at `logs/review_reports/...`, the commit landing it, code-comment-style notes) uses `content_language`; user-facing surface (chat prose / the in-conversation report / status lines / findings rendered in chat) uses `conversation_language`. Code identifiers, file paths, field names, frontmatter keys, and structural prefixes (`H1`, `M1`, `OQ1`, `REVIEWED-PASS`, etc.) stay English regardless.

# /full-review — Whole-repo alignment audit

Run a full "spec alignment + implementation risk" review over the entire repository. If `$ARGUMENTS` is present, take it as this round's focus or extra concerns.

## 0. Load skills config

`Read` `ai_context/skills_config.md`.

- File missing / some section title missing → fail loudly: print missing items + prompt to fill per plugin template, stop
- A section's content is `(none)` or empty → skip the related steps for that section (treat as project doesn't have this item)
- A section lists a concrete path but the path doesn't exist → fail loudly: report that the section drifted to a missing path, stop and wait for user to fix

Subsequent steps referring to "skills_config.md `## XX`" cite this config. This skill uses:
`## Source directories` (implementation-line scan scope),
`## Data contract directories` (spec-line data-contract scan; includes JSON Schema / proto / OpenAPI / Pydantic / SQL DDL etc.),
`## Example artifact directories` (artifact-line scan scope),
`## Core component keywords` (priority check items),
`## Timezone` (timestamp on result archival),
`## Language` (read both `content_language` and `conversation_language` here; print them once on the way out of §0 — see below).

**Language-axes anchor (after skills_config load)**: print one line `Language axes: conversation_language=<value> · content_language=<value> (source: ai_context/skills_config.md §Language)`. Both axis values echoed verbatim from §Language; the natural-language prefix translates to `conversation_language` (rendered in the project's chosen language). This anchor is planted before the four parallel audit lines fan out in "How to work" below.

## Goals

First read `ai_context/` and `docs/` to follow the current project truth, then review the whole repository and judge:
1. Whether docs, ai_context, schema, prompts and implementation are aligned
2. Whether there are conflicts, ambiguities, stale descriptions, unfulfilled promises
3. Whether there are bugs, behavioral risks, state-machine / flow gating issues, data consistency risks
4. Whether the architecture and implementation have obvious problems, hazards, fragile points
5. Whether there is a "doc says A, code does B, sample data is C" situation
6. Whether there is legacy logic, half-migrated state, dead code, broken checks, no-op validations
7. Whether committed samples / artifacts conflict with the repo's claimed status

## How to work

- Read `ai_context/` first, treating it as the default handoff entry point
- Then read `docs/requirements.md` and `docs/architecture/`
- Do not read `logs/change_logs/` by default unless a conflict has surfaced and historical decisions must be traced
- Then scan the whole repository, including but not limited to:
  - directories listed in skills_config.md `## Source directories`
  - directories listed in skills_config.md `## Data contract directories` (skip if `(none)`), and the prompt-sources path from skills_config.md `## Activity sources.Prompt sources.Path` (skip when `(none)`)
  - directories listed in skills_config.md `## Example artifact directories`
  - `README.md`, `.gitignore`
> **Language (sub-agent dispatch)**: when the runtime supports parallelism and the four audit lines below run as sub-agents, the parent MUST inject the language axes into each sub-agent's prompt explicitly. Include verbatim: "Reply in `conversation_language`=`<value>`; write any disk artifacts in `content_language`=`<value>`; both values from `ai_context/skills_config.md §Language`." Sub-agents do not inherit the parent's language config — they must be told. Sub-agent report-back to the parent is a USER surface; the consolidated review report file is DISK surface. **Place this injection at the end of the sub-agent prompt** (recency-favorable position), not in the header / middle — sub-agents have just read English source files in their audit scope, so the dispatch directive needs recency advantage over the scanned content to keep the reply in `conversation_language`.

- If the runtime supports parallelism, run at least four audit lines in parallel:
  1. **Spec line (mandatory)**: `ai_context/`, `docs/`, directories listed in skills_config.md `## Data contract directories` (skip that section's scan if `(none)`), the prompt-sources path from skills_config.md `## Activity sources.Prompt sources.Path` (skip when `(none)`)
  2. **Implementation line**: scan directories listed in skills_config.md `## Source directories` + scripts / state machines / validations / retries / rollback logic. If the section is `(none)` / empty, degrade to "every subdirectory under the project root except ai_context / docs / logs / .git / directories already listed in `## Data contract directories` / prompts"
  3. **Risk line**: scope = implementation line, but a different lens — implementation line asks "does it still hook up / are fields drifting / is gating aligned with the docs", risk line asks "is what it does correct": edge cases, null / None, exception paths, concurrency, retry / rollback, error handling that hides bugs; whether new behavior or long-unreviewed code risks data loss / security holes / performance regression; whether the state machine / gates / invariants leave uncovered branches; produce entries under bug / behavior-risk categories under "priority check items" and the same-named Findings sub-section
  4. **Sample artifact line**: scan directories listed in skills_config.md `## Example artifact directories`, check whether committed progress / artifacts match the spec. Skip this line if the section is `(none)` / empty and print "No example artifact directories declared, sample line skipped"

## Priority check items

- Are `ai_context` and `docs` consistent
- Are `docs/requirements.md` and `docs/architecture/*` consistent
- Do directories listed in skills_config.md `## Data contract directories` (data contract layer including schema / proto / openapi / pydantic / SQL DDL etc.) cover the core data structures promised in docs (skip if section is `(none)`)
- Do prompt templates still reference stale fields, old flows, deprecated files
- Do components listed in skills_config.md `## Core component keywords` actually deliver the gating and validation promised in docs (skip if `(none)` / empty)
- Are there gaps in Phase / state machine / recovery / rollback / retry / commit gate
- Is there a "doc claims it will block, code doesn't actually block" situation
- Is there field name drift or schema-field / code-field mismatch
- Are programmatic checks actually no-ops, missing checks, empty checks
- Do `.gitignore`, local artifacts, tracked files contradict each other
- Do committed samples under skills_config.md `## Example artifact directories` match `ai_context/current_status.md`, README, docs descriptions
- Is there content claimed externally as "done / verified" that the repo state does not actually support

## Audit requirements

> **Language**: disk-bound — write this section's audit findings and output-structure prose (folded into the eventual report file at "Result archival") in `content_language` per `ai_context/skills_config.md §Language`. Code identifiers, file paths, field names stay English regardless.

- This is a review, **not a code change**; aside from the new review report from "Result archival (mandatory)" which must be committed, do not modify, commit or push any other file
- Prioritize "high-value problems" over generic remarks; cover the whole repo but focus on items that genuinely affect follow-up development / extraction quality / runtime correctness
- Do not lead with a summary, lead with findings
- Findings are sorted by severity: High / Medium / Low
- Each finding should include where possible:
  - Conclusion
  - Why this is a problem
  - Scope of impact
  - Evidence files and specific line numbers
- If it is "inference" rather than "direct evidence", explicitly label "this is inference"
- If no problem is found, explicitly say "no clear problem found" and list residual risks and uncovered areas
- Do not pad with low-value opinions
- Do not lump "future optimization" into bugs; keep bugs / conflicts / risks / architectural hazards separate
- When reporting findings: cross-doc conflict → explicitly call out which doc should be treated as the higher-priority truth; `ai_context` is stale → explicitly call out how it will mislead future AI

## Output format

> **Cross-skill protocol ownership**: this Section defines the review-report 5-section body order (`Findings` → `Alignment Summary` → `Residual Risks` → `Open Questions / Ambiguities` → `Recommendations`) and the finding ID prefix conventions (`H1` / `M1` / `L1` / `OQ1`, stable across merge / withdraw). This is consumed by `/check-review` Step 0 (file pick by pattern), Step 1 (body parse by section names), and Step 3 (per-finding re-check that reuses the original IDs). Renaming any section, reordering them, or changing the ID prefix scheme requires a lockstep edit in `/check-review` per `ai_context/conventions.md §Cross-File Alignment` (row: "Review-report protocol").

> **Language**: user-facing — render the `Findings` / `Alignment Summary` / `Residual Risks` / `Open Questions` / `Recommendations` sections **as printed into the conversation** in `conversation_language` per `ai_context/skills_config.md §Language`. Section headings and finding ID prefixes (`Findings`, `H1`, `M1`, `L1`, `OQ1`, `Recommend:`, etc.) stay English; only the descriptive prose / evidence / recommendation text translate.

> **Language anchor reset (render-time)**: before emitting the in-chat report below, re-echo the language axes verbatim — `conversation_language=<value>` · `content_language=<value>` from `ai_context/skills_config.md §Language`. The "Result archival" step writes a substantial `content_language`-bound report file to disk; this reset refreshes recency at the entry of the USER-facing render so the in-chat sections below stay in `conversation_language` even when the template's structural scaffold (section headings + ID prefixes `H1` / `M1` / `OQ1` / `Recommend:`) is English.

> **Language**: disk-bound — the same sections **as written into the report file** at "Result archival" use `content_language` per `ai_context/skills_config.md §Language`. The on-disk report is the canonical archival surface and stays in `content_language` regardless of `conversation_language`; the in-chat render above is the user-facing surface. Code identifiers, file paths, field names stay English regardless.

1. `Findings`
   - Sorted by severity: High → Medium → Low
   - **Numeric ID required**: within each priority, increment from 1 (`H1` / `H2` / `H3`...; `M1` / `M2`...; `L1` / `L2`...). Follow-up `/check-review` / conversation references must use this ID; once issued, IDs are not reordered (on merge / withdraw, the original ID stays as a placeholder, other entries are not renumbered). Bold in markdown, e.g. `**H1** path/file.py:42 — ...`
   - Every entry carries a file path and line number
2. `Alignment Summary`
   - Brief summary of which layers are aligned and which are most misaligned
3. `Residual Risks`
   - Places worth watching even if not confirmed as bugs yet
4. `Open Questions / Ambiguities`
   - List points the repo itself cannot uniquely decide and that need product / architecture clarification; number each OQ as `OQ1` / `OQ2`...
5. `Recommendations`
   - **Reference only, the user decides**. Before issuing each recommendation, run a three-question self-check:
     1. **Necessary?** — what happens if we don't fix it? Just an eyesore / OCD → lean "skip" or "leave as todo"
     2. **Can it be simpler?** — if a 3-line change solves it, do not extract a helper / add a layer / add a config / add a flag
     3. **Outside this review's scope?** — is the opportunistic "related fix" overflowing this round's goal
   - One flat list: each finding ID (H1 / M1 / L1...) + each OQ gets "recommend {fix / leave todo / skip}: {one-sentence reason / preferred approach}"

## Result archival (mandatory)

> **Cross-skill protocol ownership**: this Section defines the review-report filename pattern + file-header structure (line `**Review model**: <full model name> (`<model-id>`)`). Filename path + pattern themselves come from `ai_context/skills_config.md ## Activity sources.Review reports.*`; this Section pins down the file-header line and the `{model}` / `{slug}` slug conventions. Consumed by `/check-review` Step 0 (file enumeration via the pattern, filter via `{model}` slug). Renaming the file-header label, changing the slug conventions, or altering the verdict label set (`REVIEWED-PASS` / `REVIEWED-PARTIAL` / `REVIEWED-FAIL`) requires a lockstep edit in `/check-review` per `ai_context/conventions.md §Cross-File Alignment` (row: "Review-report protocol").

> **Language**: disk-bound — write this review report file at `logs/review_reports/{ts}_{model}_{slug}.md` in `content_language` per `ai_context/skills_config.md §Language`. The file header label `**Review model**:`, the filename's `{model}` slug, and the `REVIEWED-*` verdict labels stay English (structural). The commit message that lands this file follows `content_language`. Code identifiers, file paths, field names stay English regardless.

After review, write the complete round's findings (including False Positives, Open Questions,
Alignment Summary, Residual Risks, recommended landing order) into the path declared at
`ai_context/skills_config.md ## Activity sources.Review reports.Path`, using the filename pattern
declared at `## Activity sources.Review reports.Filename pattern` (defaults: `logs/review_reports/`
+ `{YYYY-MM-DD_HHMMSS}_{model}_{slug}.md`):

```
<review_reports_path>/<filename pattern with {model} and {slug} substituted>
```

- **Timestamp**: execute the command template from skills_config.md `## Timezone` (on §Timezone failure, follow the fallback declared in that section body — system-tz `date '+%Y-%m-%d_%H%M%S'`)
- **`{model}`**: the model slug that executed this review, lowercase, joined with `-`. Examples:
  `opus-4-7`, `sonnet-4-6`, `haiku-4-5`, `gpt-5`, `codex`. Forbid spaces,
  underscores, vendor prefixes (do not write `claude-opus-4-7`, just `opus-4-7`)
- **`{slug}`**: short English or pinyin name describing this round's theme (e.g.
  `t-token-watch_review_findings`, `post-phase3_audit`)
- **File header** must have a line `**Review model**: <full model name> (`<model-id>`)`,
  matching `{model}` in the filename, for later searching / distinguishing different models' judgments
- One review = one file; do not append, do not overwrite an old file
- The review-reports directory only stores review result snapshots; non-overlapping with the change-logs directory (path per `## Activity sources.Change logs.Path`, historical decision records) and the TODO list (path per `## Activity sources.TODO list.Path`)

After writing, **immediately commit this review report file** — do not leave a dirty working tree, otherwise the next `/go` Step 1 prompt will fold this residue into the dirty summary, forcing the user to spend extra attention, with zero benefit to leaving it dirty.

- Commit on the **current branch** (`/full-review` is usually run on the user's current branch, no need to switch)
- Only `git add` this review report file — do not casually bundle other unrelated dirty files into the commit
- Commit message style: `log(review_reports): /full-review {slug} ({model})`
- No push, no branch switch; end this review round once committed
