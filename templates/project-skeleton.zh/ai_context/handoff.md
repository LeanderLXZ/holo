<!-- holo:section start -->
<!--
MAINTENANCE — 编辑本文件前请先阅读。
本文件是用于快速回到项目状态的索引，不是详细手册。
1. 写"是什么 / 去哪找"；链接到权威源（代码路径、docs/*.md、schema、logs）。
2. 优先删减而非新增；新增前先检查是否能并入已有条目。
3. 只描述当前设计 —— 不写"legacy / deprecated / formerly / renamed from"。
4. 不出现真实产品 / 客户 / 私有内容名称 —— 使用结构性占位符。
5. 精简要求：
   - 越短越好。每条都是总结，不是细节堆叠。
   - 精简的同时也要保证信息的准确性和有效性，不要为了精简而漏掉重要信息。
   - 目标每条 ≤ 5 行，更长的细节推到链接的来源里（docs/<topic>.md）。
   - 不要压缩或改动与当前编辑无关的内容。
6. 表格形式是永久的 —— 直接填 cell。若某 cell 内容溢出可读性，把细节推到链接的文档（`docs/<topic>.md`）并把 cell 摘要保持一行。
7. Sentinel 纪律（参见 CLAUDE.md §plugin 管理段）：sentinel `<!-- holo:section start/end -->` 内的内容是 plugin canonical，`/holo:update` 会覆写；项目专属新增内容写在 sentinel 之外的 gap 里。
-->
<!-- holo:section end -->

# 交接 <!-- holo:heading -->

<!-- holo:section start -->
会话起始读取顺序的最后一个文件。快照当前项目状态、下一步方向，
以及塑造每一次决策的用户偏好。替代旧的 `current_status.md` +
`next_steps.md` + `handoff.md` 三件套。
<!-- holo:section end -->

## 当前状态 <!-- holo:heading -->

<!-- holo:section start -->
项目**当下**所在位置的实时快照。每当项目进入新阶段、里程碑落地、
或重大 gap 被关闭 / 打开时更新。易变但持久 —— 它为未来的 AI 会话
回答"仓库现在是什么状态"。单任务进度归 `docs/todo_list.md`，不在
这里。
<!-- holo:section end -->

| 方面 | 详情 |
|---|---|
| 项目阶段 | _(none yet — current phase / version state)_ |
| 已有 | _(none yet — key components, entry points)_ |
| 当前 gap | _(none yet — open issues, unfinished pieces)_ |
| 生效规则 | _(none yet — active conventions, constraints)_ |

## 下一步 <!-- holo:heading -->

<!-- holo:section start -->
按优先级分组的方向级路线图。这是**方向**层，不是任务层。文件 /
函数级工程任务归 `docs/todo_list.md`；当某个方向具体到能写出路径
和行号时，把它升级到 `docs/todo_list.md`。
<!-- holo:section end -->

| 优先级 | 条目 |
|---|---|
| 高 | _(none yet — multi-task initiatives the project should build next)_ |
| 中 | _(none yet — secondary directions)_ |
| 后续 | _(none yet — deferred exploration)_ |

## 用户在意的事 <!-- holo:heading -->

<!-- holo:section start -->
塑造每次决策的软偏好和品味规则，不是正式 requirements。这些是
新 AI 会话需要继承的"用户在意的事"。在对话中浮现新偏好时追加
bullet；不再适用的删掉。
<!-- holo:section end -->

- _(none yet — delete this marker once content is added)_
