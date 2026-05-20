# Translation Glossary (zh ↔ en)

Canonical Chinese ↔ English term mapping for the `holo` plugin's translation work. Single source of truth for any translation between the plugin's canonical-English source and a non-English consumer project's content.

**Primary consumers**:

1. Phase 6 translation sub-agents (templates / ai_context / docs translation with full 4-agent review) — agent prompts must embed this glossary by reference.
2. Any future maintainer adding new content to plugin source (`commands/`, `skills/`, `templates/project-skeleton/`) that originated in another language.

**Pointer**: This glossary is the working artifact. The architectural / configuration source-of-truth for language behavior is `ai_context/skills_config.md §Language` (per-project `content_language` / `conversation_language` plus `auto` semantics).

**Maintenance contract**:

- **Append-only**: do not rewrite an existing canonical mapping in place. To deprecate, add a new entry referencing the old (e.g. add a "supersedes" Notes column).
- **Trigger to add an entry**: when a translation sub-agent coins a new term it had to invent, OR when `/full-review` / terminology consistency review flags a repeated term not in this glossary.
- **Conflict resolution**: if a context demands a translation different from the canonical, prefer the canonical; if forced to deviate, add a Notes column entry explaining the context-specific choice.
- **No real customer / product names**: structural placeholders only. The plugin source is project-agnostic.

---

## §1 Process / workflow terms

Concepts about how the workflow flows, what stages exist, what a step's role is.

| 中文 (zh) | English (en) | Notes |
|---|---|---|
| 前置校验 | pre-check | The verification pass before a destructive action (`/holo-release` Step 1, `/forward` Step 2 候选预检). |
| 落地 / 落盘 | land | Verb form ("land the change"). "Land" preferred over "deploy" / "ship" / "implement" / "materialize" in plugin contexts. |
| 复审 | review | The general term for any audit / re-examination pass. Compare with §re-check (revisit a stored review report). |
| 复核 / 再复查 | re-check | Specific to `/check-review` — revisiting a stored `logs/review_reports/` finding against current state. |
| 对齐 | alignment | Cross-file / cross-doc / cross-spec consistency. See `ai_context/conventions.md §Cross-File Alignment`. |
| 收尾 | wrap-up | Final cleanup step of a flow (e.g. `/go` Step 10, `/post-check` Step 7). |
| 触发 | trigger | The event chain that surfaced a task / decision (todo_list `**触发链** → **Trigger**`). |
| 决议 / 决定 / 拍板 | decided / decision | Final position locked in. Verb "拍板" = "lock". |
| 收敛 | converge | Decisions converge during `/plan` discussion. |
| 漂移 | drift | Spec-vs-code or file-vs-file inconsistency surfaced by audits. |
| 自适应 | self-adaptive | The mirror drift check is self-adaptive: adding a section to template propagates automatically. |
| 自描述 | self-describing | A file is self-describing if its content makes its role obvious (e.g. CLAUDE.md). |
| 自检 | self-check | `/holo:init` Step 3 self-check; the Dilution Self-Check in CLAUDE.md / AGENTS.md. |
| 加载 | load | "Load skills config" = Step 0 of most skills. Distinct from "read" (one-shot file access). |
| 探测 | probe | Probing repo state (e.g. `/holo:init` Step 0 repo probing). |
| 抓取 | fetch / grab | Inside-flow data gathering. Distinct from `git fetch`. |
| 解析 | parse / resolve | Parse `$ARGUMENTS`, resolve a path stem to a file. |
| 阅读顺序 | Reading Order | `ai_context/instructions.md` H2 — ordered list of files to read at session start. |
| 更新预期 | Update Expectations | `ai_context/instructions.md` H2 — when to update `ai_context/`. |
| 每个里程碑之后 | After Each Milestone | `ai_context/handoff.md` H2 — post-milestone routine (log + update durable files). |

---

## §2 Engineering action terms

Concrete operations the AI or user performs.

| 中文 (zh) | English (en) | Notes |
|---|---|---|
| 写盘 | write to disk | Distinct from "print to console". Files committed to disk = `content_language` per §Language. |
| 落档 | record / log | "Record an entry" / "log a finding". Distinct from "落地" (land). |
| 提交 | commit | Always means git commit in this codebase. |
| 推 / 推到 | push / push to | git push; `/forward` pushes commits across branches by merge. |
| 切 / 切换 | switch / cut | "Switch branches" (`git checkout`) vs "cut a section". |
| 跑 | run | "Run `/go`" / "run sub-agent". |
| 串跑 | run serially | Single-pass execution, no parallelism. |
| 并行 | in parallel | Sub-agent fan-out. |
| 排序 | ordering / sort | Phase ordering; finding ordering by severity. |
| 兜底 | fallback / safety net | "Use `/ultrareview` as fallback" / "the do-not-commit scan as a safety net". |
| 拒掉 / 拒写 / 拒移入 | reject / refuse to write / refuse the move | `/todo-add` single-slot enforcement: refuse to write into In Progress when occupied. |
| 折回 / 折叠 | fold back / collapsed | "Fold back" = collapse expanded sub-tasks back into one entry (verb). "Collapsed" = visual UI state (adjective). |
| 展开 | expand | Expand sub-tasks under a step (TodoWrite). |
| 渲染 | render | `/todo` renders the Index section to the user. |
| 优雅降级 | graceful degradation | The SessionStart hook's sole-exception clause: missing config → still emit `[git] branch:` line, exit 0. |
| 静默 / 静默跳过 | silent / silently skip | "Silently skip the [lang] line when §Language section is absent". |
| 强制 | enforced / mandatory | "Hard requirement" (Tier B canonical form). |
| 严守 | strictly follow | "Strictly follow the spec phase order". |
| 命中 / 不命中 | match / hit · miss | "/run-prompt stem fuzzy-matches against `prompts/` tree": "0 命中" = "0 matches"; "1 命中" = "1 hit". |
| 锚定 | anchor | "L4 — output template anchoring": templates anchor language by structure. |
| 复述 | restate | "L3 directives restate the language contract at each output step". |
| 反向翻译 | back-translation | The 4th review-agent role: translate the English back to Chinese and diff against the original. |
| 行动 vs. 加载 | Acting vs. Loading | CLAUDE.md / AGENTS.md H2 — distinguishing action on user request vs. context-loading reads. |
| 稀释自查 | Dilution Self-Check | CLAUDE.md / AGENTS.md H2 — long-session forgetting check before file edits. |
| 范围检查 | scope check | Dilution Self-Check sub-question 1 — am I doing exactly what the user asked. |
| 对齐检查 | alignment check | Dilution Self-Check sub-question 3 — Cross-File Alignment table consult. |

---

## §3 Control flow / state terms

| 中文 (zh) | English (en) | Notes |
|---|---|---|
| 显式 | explicit | "Explicit user authorization required". |
| 隐式 | implicit | Avoid implicit behaviors in skill design. |
| 默认 | default | "Default = current branch" (`/push` $ARGUMENTS). |
| 选项 | option | Step 1 of `/go` presents 3 / 4 options. |
| 槽 / 单槽 | slot / single slot | "In Progress single slot" — only one task in-flight at a time. |
| 状态机 | state machine | Phase / segment transitions in todo_list. |
| 失败模式 | failure mode | Risk-line audit examines failure modes. |
| 不变量 | invariant | Things that must always hold (e.g. `## In Progress` ≤ 1 entry). |
| 边界条件 | boundary condition | Risk-line audit checklist item. |
| 异常路径 | exception path | Error handling correctness. |
| 重试 / 回滚 | retry / rollback | Failure-recovery semantics. |
| 门控 | gating | A check that blocks a flow until satisfied. |
| 上游 | upstream | Callers / dependents that consume a downstream change. |
| 下游 | downstream | Callees / dependents that propagate from an upstream change. |
| 跨分支 | cross-branch | `/forward` is cross-branch sync. |
| 跨文档 | cross-file | `ai_context/conventions.md §Cross-File Alignment`. |
| 跨范围 | cross-range / out-of-scope | A finding "spans beyond this round's scope". |
| 候选 | candidate | Pre-fill candidate (e.g. `/holo:init` Step 0.3 project-name candidates). |
| 默认优先级 | Default Priority | `ai_context/read_scope.md` H2 — files to load first at session start. |
| 默认不读 | Do Not Read By Default | `ai_context/read_scope.md` H2 — heavy / write-mostly directories to skip by default. |
| 何时深入阅读 | When To Read Deeper | `ai_context/read_scope.md` H2 — escalation triggers from default scope. |
| 实用规则 | Practical Rule | `ai_context/read_scope.md` H2 — targeted-read principle. |

---

## §4 Document structure terms

Markdown / file structure vocabulary.

| 中文 (zh) | English (en) | Notes |
|---|---|---|
| 段 | section | A top-level / sub-level markdown heading region. |
| 段位 | segment | Todo_list segments: `## In Progress` / `## Next` / `## Discussing`. Distinct from §section. |
| 索引 | index | `docs/todo_list.md` top-of-file `## Index` cache. |
| 字段 | field | Frontmatter field, todo entry field (e.g. `**Updated**`). |
| 字段名 | field name | The field's identifier (always English regardless of `content_language`). |
| 模板 | template | `templates/project-skeleton/` / PRE log template / commit message template. |
| 占位符 | placeholder | `<project-name>` / `_(TODO)_` markers. |
| 词条 | entry | A glossary entry; a todo_list entry. |
| 全文 | full text / whole file | "Translate the full text" (Phase 2'). |
| 顶部 / 末尾 | top / bottom | Top of file (frontmatter / L1 directive); bottom (last entry). |
| 既有 | existing | "Match existing entry style". |
| 注记 | note | Inline annotation; the Notes column in this table. |
| 表格 | table | Markdown table. |
| 编号列表 | numbered list | `1. ...` |
| 项目符号列表 / 项目列表 | bulleted list | `- ...` |
| 代码块 / 围栏 | code block / fence | Triple-backtick blocks. |
| 缩进 | indentation | 2 / 3 / 4 space markdown indents. |
| 交接 | Handoff | `ai_context/handoff.md` H1 — final entry in `ai_context/` reading order; hands off mental model + quick-start to next session. |
| 思维模型 | Mental Model | `ai_context/handoff.md` H2 — human-readable version of `current_status.md`. |
| 快速上手 | Quick Start | `ai_context/handoff.md` H2 — 3–6 step quick-orientation list. |
| 常用操作命令 | Operational Commands | `ai_context/handoff.md` H2 — project's most-used CLI / build / test / deploy commands. |
| 用户在意的事 | What The User Cares About | `ai_context/handoff.md` H2 — soft preferences / taste rules outside formal requirements. |
| 入口点 | Entry Point | `ai_context/instructions.md` H2 — initial loading scope (`ai_context/` itself). |
| 项目焦点 | Project Focus | `ai_context/instructions.md` H2 — single highest-signal pointer summarizing project's primary engineering focus. |
| TODO 清单 | TODO List | `ai_context/instructions.md` H2 — pointer block to `docs/todo_list.md`. Distinct from §8 `## TODO List` as a heading literal — this entry is the translated H2 form when used as content-language section header. |
| 日志记录 | Logging | `ai_context/instructions.md` H2 — section about per-change `logs/change_logs/` contract. **Distinct from `conventions.md §Logging` anchor**: that one stays English (§-referenced protocol anchor); this one is a display-only H2 in instructions.md. |
| 阅读范围 | Read Scope | `ai_context/read_scope.md` H1 — default-load / default-skip / when-to-escalate scope contract. |
| AI 上下文 | AI Context | `ai_context/README.md` H1 — compressed handoff index for future AI sessions. |
| 给后续 AI 智能体的指引 | Instructions For Future AI Agents | `ai_context/instructions.md` H1 — index header for AI-agent-facing instructions. |
| 语言 | Language | CLAUDE.md / AGENTS.md H2 — block with hardcoded `content_language` + `conversation_language` literal bullets (read-cache per `ai_context/decisions.md` §Language Configuration #17; no longer a pointer paragraph). **Distinct from `skills_config.md §Language` anchor**: that one stays English (§-referenced protocol anchor); this CLAUDE/AGENTS H2 is display-only. |
| 会话开始：通读 ai_context/ 一次 | Session Start: Read ai_context/ Once | CLAUDE.md / AGENTS.md H2 — session-start reading routine. |
| 默认不加载的内容 | What Not To Load By Default | CLAUDE.md / AGENTS.md H2 — pointer to `read_scope.md`. |
| 与 AGENTS.md 保持同步 | Sync with AGENTS.md | CLAUDE.md H2 — pair-doc sync rule. Pair literal — the `AGENTS.md` token stays English (filename). |
| 与 CLAUDE.md 保持同步 | Sync with CLAUDE.md | AGENTS.md H2 — pair-doc sync rule. Pair literal — the `CLAUDE.md` token stays English (filename). |
| 用途 | Purpose | `docs/todo_list.md` `## File guide` H3 — what the file records. |
| 任务流转 | Task flow | `docs/todo_list.md` `## File guide` H3 — task lifecycle diagram (Discussing → Next → In Progress → archived). |
| 记录什么 | What to record | `docs/todo_list.md` `## File guide` H3 — entry-content checklist. |
| 不记录什么 | What NOT to record | `docs/todo_list.md` `## File guide` H3 — exclusions. |
| 如何更新条目 | How to update entries | `docs/todo_list.md` `## File guide` H3 — entry edit / move / archive rules. |
| 何时阅读 | When to read | `docs/todo_list.md` `## File guide` H3 — when to consult this file. |

---

## §5 Boilerplate canonical forms (Tier B locked)

These phrases were locked across the 7 multi-output skill bodies after `/full-review` flagged terminology drift between parallel sub-agent translations. All future translations of these phrases MUST use the canonical English form.

| 中文 (zh) | English (en) | Notes |
|---|---|---|
| 子段标题 | sub-section title | Hyphenated. Used in §Progress reporting pre-register prose. |
| 硬性要求 | hard requirement | "This is a hard requirement — **do not proceed without calling <progress tool>**." |
| 跨步骤别漏调用 | Do not skip the call when crossing steps | Used after each step's flip-to-`in_progress` instruction. |
| 界面显示为 | rendered as | "Claude → `TodoWrite` (rendered as 'Update Todos')". |
| 每次状态切换前整段重写 | rewriting the whole block on every state change | Other-runtime fallback for the <progress tool>. |
| 语义对齐 | Semantic alignment | "Semantic alignment: pre-register + flip state + mark complete". |
| 顺手改的"相关项" | opportunistic "related fix" | Recommendations self-check item — avoid opportunistic fixes outside the round's scope. |
| 还连得上吗 | does it still hook up | Implementation-line audit question — distinct from risk-line "is what it does correct". |
| 做的事对吗 | is what it does correct | Risk-line audit question. |
| 一次性翻译 | one-shot translation | Existing-content translation strategy from Phase 2'. |
| 决议要点 | decided points | Heading of the converged-decisions block in a todo Discussing entry once landed. |
| 改动清单 | Change list | Todo entry mandatory field for Next-segment entries. |
| 完成判准 / 完成标准 | Done criteria | Todo entry mandatory field. |

---

## §6 Output template section headings

The canonical English section names used in skill body templates after Phase 2'. When a non-English `content_language` consumer's `/go` (or other multi-output skill) writes one of these templates, the headings render in that consumer's `content_language` — but the canonical reference is the English form below.

| 中文 (zh) | English (en) | Notes |
|---|---|---|
| 背景 / 触发 | Background / Trigger | PRE log first section. |
| 结论与决策 | Conclusion and decisions | PRE log second section. |
| 计划动作清单 | Planned action list | PRE log third section. |
| 验证标准 | Verification standards | PRE log fourth section. |
| 执行偏差 | Execution deviations | PRE log fifth section (appended during execution). |
| 已落地变更 | Landed changes | POST log first section. |
| 与计划的差异 | Differences from plan | POST log second section. |
| 验证结果 | Verification results | POST log third section. |
| 上下文 | Context | Todo entry field. |
| 完成判准 / 完成标准 | Done criteria | Todo entry field. |
| 依赖 | Dependencies | Todo entry field. |
| 更新时间 | Updated | Todo entry field. Note: the FIELD NAME varies per project per `skills_config.md ## Activity sources Per-entry updated-time field` (canonical default = `**Updated**`); this row documents the canonical default heading, not a hardcoded value. |
| 待决策项 | Open decisions | Todo Discussing-segment mandatory field. |
| 开始时间 | Start time | Todo In Progress-segment mandatory field. |
| 当前状态 | Current state | Todo In Progress-segment mandatory field (`in progress` / `awaiting user decision` / `paused`). |
| 预估 | Estimate | Optional todo field. |
| 未落地原因 | Why not landed | Optional todo field. |
| 暂不做的事 | Out of scope / Not doing for now | Optional todo field. |
| 总结 | Summary | `/go` final summary print. |
| 建议 / 建议落地顺序 | Recommendations | `/full-review` § Recommendations. |
| 残余风险 | Residual risks | `/full-review` § Residual Risks. |
| 待决问题 / 开放问题 | Open Questions | `/full-review` § Open Questions. |
| 完成 | Completed | PRE/POST/REVIEW log status block name. |

---

## §7 Naming conventions

Rules that are not direct translations but are project-wide locks.

| Rule | Canonical | Notes |
|---|---|---|
| Language code | ISO 639-1 (`en`, `zh`, `ja`, `ko`, ...) — NEVER use ISO 3166-1 country codes (`cn`, `us`) for language | `zh`, not `cn`. Locale variants (`zh-CN`, `zh-TW`) reserved for future regional splits. |
| Sub-task naming in TodoWrite | Hyphenated `sub-task` (not `subtask`); use single-letter ordinal (Step 4a / Step 4b ...); no nested second-level (no Step 4a-1) | Per `/go` §Progress reporting. |
| Sub-section title | Hyphenated `sub-section title` (not `subsection title`) | Per Tier B remediation. |
| Skill heading | `# /<slug> — <title>` with em-dash separator (U+2014) | Used by every commands/*.md and skills/*/SKILL.md. |
| Status block | `## Status` enum values: `PRE` / `POST` / `REVIEWED-PASS` / `REVIEWED-PARTIAL` / `REVIEWED-FAIL` / `DONE` / `BLOCKED` — always English regardless of `content_language` | These are protocol values consumed by `/post-check` and `/check-review`. |
| Log filename | `logs/change_logs/{YYYY-MM-DD}_{HHMMSS}_{slug}.md` and `logs/review_reports/{ts}_{model}_{slug}.md` — `slug` is short English / pinyin | Per `ai_context/conventions.md §Logging`. |
| Todo ID | `T-XXX` all-uppercase + hyphens, English short code, globally unique across `docs/todo_list.md` + `docs/todo_list_archived.md` | Per `/todo-add` Step 3. |
| Commit message style | `<type>(<scope>): <subject>` lowercased; types: `feat / fix / docs / refactor / chore / bump / log` | Per `git log --oneline -10` repo style. |

---

## §8 Project-specific literal terms — NOT to translate

These tokens stay literal regardless of `content_language` — they are protocol identifiers, not prose.

| Category | Examples |
|---|---|
| Slash commands | `/holo:init` `/holo:update` `/go` `/post-check` `/full-review` `/commit` `/push` `/forward` `/plan` `/todo` `/todo-add` `/run-prompt` `/recent-activity` `/monitor` `/branch-inventory` `/check-review` `/holo-release` `/ultrareview` |
| Frontmatter keys | `name:` `description:` |
| Top-level config sections | `## Background processes` `## Protected branch prefixes` `## Main branch policy` `## Do-not-commit paths` `## Source directories` `## Data contract directories` `## Example artifact directories` `## Core component keywords` `## Sensitive content placeholder rules` `## Timezone` `## Language` `## Activity sources` |
| Cross-file anchor headers (§-referenced) | `## Logging` `## Cross-File Alignment` `## Identifier Renames` `## Single Source of Truth` `## Generic Placeholders` `## Naming and Identifiers` `## Data Separation` `## Git` `## Post-Change Checklist` (`ai_context/conventions.md`); `## Format` (`ai_context/decisions.md`) — referenced as `§<name>` from other files; translating breaks the anchor. |
| Todo_list protocol headers | `## In Progress` `## Next` `## Discussing (Undecided)` `## Index (auto-generated; do not hand-edit)` `## File guide` `### Index maintenance` `## Completed` `## Abandoned` `## Format` (`docs/todo_list.md` / `docs/todo_list_archived.md`) — literal-matched by `/todo-add`, `/todo`, `/go`, `/holo:init` grep filters. |
| CLAUDE / AGENTS expected pairs literals | `Claude Entry Point` ↔ `Agent Entry Point`; `auto-loaded by Claude` ↔ `auto-loaded by coding agents`; `Sync with AGENTS.md` ↔ `Sync with CLAUDE.md`; `` This file and `AGENTS.md` `` ↔ `` This file and `CLAUDE.md` ``; `"Claude Entry Point"` ↔ `"Agent Entry Point"` — the canonical EN form (`scripts/holo_update_check.py:_EN_EXPECTED_PAIRS`, the fallback when no variant skeleton ships CLAUDE/AGENTS). Variant CLAUDE/AGENTS pairs are derived per-variant via `_derive_expected_pairs` from that variant's own line-by-line diff; the **structural invariant** is "CLAUDE.md and AGENTS.md differ at exactly the same N line positions" — the token `AGENTS.md` / `CLAUDE.md` inside the H2 stays English (filename literal) but the rest of the H2 phrasing may be translated. |
| §Language fields | `content_language` `conversation_language` `auto` |
| Plugin payload paths | `.claude-plugin/` `commands/` `skills/` `hooks/` `scripts/` `templates/project-skeleton/` `.agents/skills/` |
| Develop-only paths | `ai_context/` `docs/` `logs/change_logs/` `logs/review_reports/` |
| Branch names | `main` `develop` |
| Env vars | `${CLAUDE_PLUGIN_ROOT}` `$ARGUMENTS` |
| Tool / function names | `TodoWrite` `AskUserQuestion` `Read` `Edit` `Write` `Bash` `expected_mirror_content` `claude_agents_check` `run_check` `run_fix` |
| Drift-check categories | `agents_sync` `missing_template` `missing_section` `claude_agents` `stale` `missing` `orphan` |
| Status icons | 🟢 🟡 ⚪ 🔴 ✅ ❌ ⚠️ ⏸ 🔒 ⚙️ 💾 💬 ✓ ✗ 🚫 ✨ 🛡 |
| Markdown / code syntax | `## ` `### ` `**bold**` `*italic*` `` ` `` `` ``` `` |

---

## §9 Maintenance & extension

**Adding a new entry**:

1. Pick the right section (§1-§7). If none fits, add a new section at the end with a one-line purpose statement.
2. New row: `| zh source | English canonical | Notes (optional) |`.
3. If the new term supersedes an existing entry, mark the old entry's Notes column with `superseded by <new term>`; do NOT delete the old row (append-only).
4. If the new term is ambiguous (multiple senses), add separate entries with distinct Notes (e.g. "段" vs "段位" — both translated, different senses).

**When a translation sub-agent coins a new term**:

1. The sub-agent reports the coined term in its findings (per Phase 2' precedent).
2. The /go that runs the translation includes a Step 6 alignment item to append the coined term to this glossary.
3. Subsequent rounds reuse the canonical form.

**Cross-references**:

- Architecture-level decision on the language system: `ai_context/decisions.md §Language Configuration`.
- Config schema for `content_language` / `conversation_language`: `ai_context/skills_config.md` §Language (project-side). Required-header table + fail-loud rules: `ai_context/conventions.md` §`skills_config.md` schema.
- Cross-file alignment row for this file: `ai_context/conventions.md §Cross-File Alignment`.
- T-LANG-CONFIG-SYSTEM phase ordering and rollout history: `docs/todo_list_archived.md` T-LANG-CONFIG-SYSTEM (archived after all 6 phases landed).

**Out of scope (not yet codified)**:

- Locale variants (`zh-CN` vs `zh-TW`, `en-US` vs `en-GB`) — when needed, add a §Locale conventions section.
- Non-zh / non-en language translations — add new bilingual columns or a separate glossary file per target language.
- Tone / formality register matching — currently translations target a "formal, imperative, terse" register matching the existing English in `docs/requirements.md` and `ai_context/decisions.md`; if this register changes, update the maintenance contract above.
