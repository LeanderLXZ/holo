# TODO 清单 <!-- holo:heading -->

<!-- holo:section start -->
---
<!-- holo:section end -->

## Index (auto-generated; do not hand-edit) <!-- holo:heading -->

<!-- holo:section start -->
> 本段是下方三个子表的缓存，由编辑某条目正文的人在正文段
> 进行任何 add / edit / segment-move / completion / abandonment
> 之后**立即**刷新。刷新规则参见 `## File guide → Index maintenance`。
> `/todo` skill（若使用）不解析正文 —— 它只读这份 Index，所以
> 本段必须与正文保持同步；这里漂移意味着 `/todo` 会给出错误答案。
<!-- holo:section end -->

### 🟢 In Progress (0)

| ID | Title | Start time | Updated | Status |
|---|---|---|---|---|

### 🟡 Next (0)

| ID | Brief | Importance | Ready | Scope | Updated | Deps |
|---|---|---|---|---|---|---|

### ⚪ Discussing (0)

| ID | Brief | Open decisions | Updated | Blocked by |
|---|---|---|---|---|

**Total**: 0 — 🟢 In Progress 0 ｜ 🟡 Next 0 ｜ ⚪ Discussing 0

<!-- holo:section start -->
---
<!-- holo:section end -->

## File guide <!-- holo:heading -->

<!-- holo:section start -->
### 用途

记录**已计划但尚未完成**的具体工程任务。
与兄弟文件区分：

- `ai_context/handoff.md §Next Steps` —— 架构方向与高层路线图
  （按优先级的 2 列表格）。
- `ai_context/handoff.md §Current State` —— 当前项目状态快照
  （按方面的 2 列表格）。
- `logs/change_logs/` —— 历史（带时间戳，append-only）。
- `docs/architecture/` —— 正式架构文档。
- `docs/todo_list_archived.md` —— 已完成 / 已废弃任务的精简归档
  （完整细节存于 git 历史 + change logs）。

本文件是**工程层**的队列：文件路径、行号、
change manifest、验证步骤。

### 任务流转

```
Discussing ──(decided)──▶ Next ──(start)──▶ In Progress ──(commit done)──▶ archived ## Completed
                                                                            ▲
any node ─────────────────(abandoned)──────────────────────────── archived ## Abandoned
```

段位语义：

- **In Progress**（单槽）—— 已开始但尚未提交的任务。
  **同一时刻只有一条** —— 这样在工作被打断（ctrl-c / 暂停 /
  会话切换）时，下一个 AI 会话能直接看到"当前在做什么"，
  无需解析 git status 或进度文件。
- **Next** —— 依赖与设计均已就绪、随时可以开始的任务。
  按用户优先级排序 —— 第一条就是下一个要开始的。
- **Discussing** —— 仍有待决策项 / 外部依赖 / 设计未定的任务。
  不要开始；先把决策收敛掉。

### 记录什么

✓ 文件 / 函数级别的具体改动任务。
✓ 每条目必须包含：**Context**（动机 + 当前状态 +
  trigger）、**Change manifest**（文件路径 + 行号；在 `Discussing`
  中可以是部分的）、**Done criteria**、**Deps**。
✓ 视情况：**Open decisions**（在 `Discussing` 中必填）、
  **Estimate**、**Why not landed yet**、**Out of scope**。
✓ **Requirements**（可选；位置在 **Context** 与 **Change manifest**
  之间）：用户要做什么 / 要达成什么效果。纯文字段，无特殊格式规则。
  本会话收敛了值得保留的用户需求时填。
✓ **Solution details**（可选；位置在 **Requirements** 与
  **Change manifest** 之间）：最终落定的方案是什么、由哪些部分组成。
  **只装最终落定版** —— 不写废弃方案、不写否决备选、不写讨论历史。
  纯文字段，无特殊格式规则。本会话收敛了值得保留的具体方案时填。
✓ 在 `Discussing` 条目中，列出未解决的选项及其权衡。

### 不记录什么

✗ 架构方向 / 高层路线图 → `ai_context/handoff.md §Next Steps`（2 列表格）。
✗ 已完成 / 已废弃任务 → 移到 `docs/todo_list_archived.md`（精简）。
✗ 临时调试笔记 / 思考过程中的分析 → 放到对话或 plan 里，
  不要持久化。
✗ 运行时状态 / 进度 → 写到运行时进度产物里
  （参见 `ai_context/skills_config.md` §Background processes）。

### 如何更新条目

**所有段位通用**：每个 `### [T-XXX]` 块都必须有
**Updated** 时间戳（`YYYY-MM-DD HH:MM` + 时区，遵循
`ai_context/skills_config.md` §Timezone）。创建时设置；
任何正文字段被修改或条目在段位间移动时刷新。
**只刷新 Index 缓存不算** —— 该字段标记的是"正文实际变更的时间"。

**添加新任务**：放入合适的段位（Next 或
Discussing）。新条目必须包含 "What to record" 中的字段，
加上 `**Updated**`。**不要直接加进 "In Progress"** ——
该段位只有任务实际开始时才填入。

**任务开始（移入 In Progress）**：
1. 把整条目从 "Next" 移到 "In Progress"。
2. 添加 `**Start time**`（同样的时间戳格式）和 **Current state**
   （in-progress / awaiting decision / paused）。
3. 刷新 `**Updated**` = start time。
4. **单槽** —— 如果 "In Progress" 已被占用，
   先完成或显式 pause-back 那条任务。
5. 刷新 Index（参见 "Index maintenance"）。

**任务完成（已 commit + 已验证）**：
1. 把条目移到 `docs/todo_list_archived.md` `## Completed`
   （精简条目：标题 + completion form + 一行总结 + log 链接）；
   从本文件删除。
2. 如果该任务产生了持久结论 / 新的架构
   决策 / 可复用洞见，写一份
   `logs/change_logs/YYYY-MM-DD_HHMMSS_slug.md`。
3. 如果完成会改变 `ai_context/` 中的持久事实（`handoff.md` 的
   Current State / Next Steps 表，或 `decisions.md`），相应更新。
4. 刷新 Index。

**任务废弃**：写一份 `logs/change_logs/` 条目说明原因，然后
把条目移到 `docs/todo_list_archived.md` `## Abandoned`（同样的
精简格式）。刷新 Index。

**讨论落地**：当一条 `Discussing` 条目得出结论时：
- **完整决策** —— 把条目移到 `Next`，补齐缺失的
  字段（Change manifest / Done criteria / Deps）。刷新 Index。
- **部分决策** —— 把已决策的子任务拆成独立的
  `Next` 条目；未决的余下部分留在 `Discussing` 中，
  context 已更新。刷新 Index。
- **结论使现有 `Next` / `In Progress` 任务失效**
  —— 当作 "任务废弃" 处理。

### Index maintenance

文件顶部的 `## Index (auto-generated; do not hand-edit)` 段
缓存了三个子表。**在正文进行任何 add / edit /
segment-move / completion / abandonment 之后刷新。** `/todo`
skill 只读这一段。

**触发**刷新 —— 以下任一：

- 添加新条目。
- 编辑现有条目的标题、context 摘要、deps、open
  decisions、change-manifest 文件数、schema/architecture/multi-phase
  涉及范围、或 `**Updated**`。
- 段位移动：Discussing → Next、Next → In Progress、In Progress →
  archived、any → archived（废弃）。
- `In Progress` 条目内的 "Current state" 变更。

**列定义**：

**In Progress**

| Column | Source |
|---|---|
| ID | 反引号包起来的 T-XXX slug |
| Title | 方括号之后的人类可读短语 |
| Start time | 条目的 `**Start time**` 字段，完整时间戳 |
| Updated | 条目的 `**Updated**` 字段，仅日期（不含 HH:MM）；缺失 → `—` |
| Status | 条目的 `**Current state**` 值 |

**Next**

| Column | Source |
|---|---|
| ID | 反引号包起来的 T-XXX slug |
| Brief | Context 的第一句 + 1–2 行关键背景。**总长度 ≤ 150 字符。** 去掉 markdown 链接反引号以便表格渲染，但保留 `[text](url)` 形式。 |
| Importance | 🔴 High / 🟡 Medium / 🟢 Med-Low（规则见下） |
| Ready | ✅ Ready / 💬 Discuss first / ⏸ Blocked（规则见下） |
| Scope | 🟢 Small / 🟡 Medium / 🔴 Large·Arch / —（规则见下） |
| Updated | 条目的 `**Updated**` 字段，仅日期 |
| Deps | 条目 `**Deps**` 字段的第一句 |

**Discussing**

| Column | Source |
|---|---|
| ID | 反引号包起来的 T-XXX slug |
| Brief | 同 Next，≤ 150 字符 |
| Open decisions | `**Open decisions**` 下 bullet 项的数量；缺该段 → 0 |
| Updated | 条目的 `**Updated**` 字段，仅日期 |
| Blocked by | `**Deps**` 的第一句 |

**推断规则**（确定性 —— 不要自由发挥）：

**Importance**（仅 Next）

| Level | Trigger |
|---|---|
| 🔴 High | 用户已标记为高优先级 OR 阻塞其他任务 |
| 🟡 Medium | 既未标 High 也未标 Med-Low 的默认 |
| 🟢 Med-Low | Deps 被阻塞 OR open decisions ≥ 2 OR 用户未标过优先级 |

**Ready**

| Tag | Trigger |
|---|---|
| ✅ Ready | Deps 已就绪 AND open decisions = 0 |
| 💬 Discuss first | Open decisions ≥ 1 |
| ⏸ Blocked | Deps 中含具体阻塞项（外部 CLI、未实现模块、待发生事件） |

优先级：⏸ > 💬 > ✅。

**Scope**

| Size | Trigger |
|---|---|
| 🟢 Small | Change manifest ≤ 2 个文件 AND 无 schema / interface 改动 |
| 🟡 Medium | Change manifest 3–6 个文件 OR 模块内多函数 refactor；无架构层改动 |
| 🔴 Large·Arch | Change manifest ≥ 7 个文件 OR 触及：新 phase / schema field / 核心 interface / 跨模块协议 / 新依赖 |
| — | 缺 change manifest（在未拆解的 `Discussing` 条目中常见） |

**Brief 写作规则**：用大白话写 —— 这件事解决什么
问题、为什么值得做。**避免代号 / 函数名 /
schema 路径 / 行号 / 决策编号 / 行话**，除非
它们本身就是问题。总长度 ≤ 150 字符；超出时砍掉
细节，直到只剩 "what + why"。

**Summary line**：三个表之后，打印一行：
`Total: N — 🟢 In Progress a ｜ 🟡 Next b ｜ ⚪ Discussing c`。

### 何时阅读

- 用户问待办 / 接下来做啥 → `/todo` skill（只读
  Index）。
- 开始任何改动之前，**读一次**避免
  重复规划。
- 在讨论某个可能已在此跟踪的话题时。
- **默认不加载** —— 不属于 `ai_context/`
  会话启动阅读顺序。

---
<!-- holo:section end -->

## In Progress <!-- holo:heading -->

<!-- holo:section start -->
<!-- Single-slot. Filled only when a task is actually started.
     Format: see "How to update entries → Task starts". -->
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_

## Next <!-- holo:heading -->

<!-- holo:section start -->
<!-- Ordered by user priority. First entry is the next to start.
     Format: see "What to record". -->
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_

## Discussing (Undecided) <!-- holo:heading -->

<!-- holo:section start -->
<!-- Tasks with open decisions / external deps / unsettled design.
     Don't start; converge the decision first.
     Format: see "What to record" + "Open decisions" section mandatory. -->
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_
