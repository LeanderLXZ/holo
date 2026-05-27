<!-- holo:section start -->
<!--
MAINTENANCE — 编辑本文件前请先阅读。
稳定的项目元规则。保持精简；仅在规则本身变化时更新。
Sentinel 纪律（参见 CLAUDE.md §plugin 管理段）：sentinel `<!-- holo:section start/end -->` 内的内容是 plugin canonical，`/holo:update` 会覆写；项目专属新增内容写在 sentinel 之外的 gap 里。
-->
<!-- holo:section end -->

# 给后续 AI 智能体的指引 <!-- holo:heading -->

## 入口点 <!-- holo:heading -->

<!-- holo:section start -->
`ai_context/` 是 handoff 入口。默认不要重读整段对话历史或大型产物
目录。只有当用户的任务明确需要时，才加载更重的层（logs、原始输入、
生成产物）。

读完 `ai_context/` 后，**停下来等待**下一条指令。读 `ai_context/`
是上下文加载，不是任务说明。只在用户显式请求时行动。
<!-- holo:section end -->

## 阅读顺序 <!-- holo:heading -->

<!-- holo:section start -->
1. `instructions.md`（本文件）
2. `project_background.md`
3. `requirements.md`
4. `architecture.md`
5. `conventions.md`
6. `decisions.md`
7. `handoff.md`

Dilution self-check（何时重读哪个文件）写在 `CLAUDE.md` /
`AGENTS.md`。
<!-- holo:section end -->

## 阅读范围 <!-- holo:heading -->

<!-- holo:section start -->
默认先读什么 / 默认跳过什么 / 何时读得更深。

**默认优先级** —— 启动会话时优先读（`ai_context/` 永远最先读）。
随项目演进，把专属的"小而高信号"目录追加到下方 user-territory 列表。

**默认不读** —— 大型或以写为主的目录：`logs/change_logs/`（完整
历史）、`logs/review_reports/`（过往审计快照）、`logs/file_snapshots/`
（smart-merge 备份归档）。仅当任务明确要求时才加载。把项目专属的
跳过路径追加到下方 user-territory 列表。

**何时深入阅读** —— 用户明确要求；任务依赖来自更重源的特定证据；
`ai_context/` 中的压缩上下文不足以回答当前问题；某个冲突需要
provenance 校验。

**实用规则** —— 优先做定向读取：具体文件、最小摘录、先看摘要。
避免扫描整个大目录、加载全部会话历史、读取全部 logs，或将源内容
大段粘进回答。
<!-- holo:section end -->

项目专属默认优先级路径（例如顶层 `README.md`）：

- _(none yet — delete this marker once content is added)_

项目专属默认跳过路径：

- _(none yet — delete this marker once content is added)_

## 更新预期 <!-- holo:heading -->

<!-- holo:section start -->
仅在**仓库的持久事实**（长期惯例、架构、schema、决策）发生变更时
更新 `ai_context/`。短期运行时状态 / 单任务进度归 work-local 进度
文件或 TODO 列表，不归这里。
<!-- holo:section end -->

## 日志记录 <!-- holo:heading -->

<!-- holo:section start -->
`ai_context/` 之外的每次改动 → 按 `conventions.md` §Logging 的
契约在 `logs/change_logs/` 下落一条条目。负责 logging 格式的 skill
（`/go` / `/do` / `/post-check`，当本项目使用它们时）直接写文件 ——
不要在此处重复格式。
<!-- holo:section end -->

## TODO 清单 <!-- holo:heading -->

<!-- holo:section start -->
`docs/todo_list.md` —— 已规划但未完成任务的工作队列。按需读取，
**不**纳入会话起始的读取顺序。使用规则写在该文件自身的
`## File guide` 段。
<!-- holo:section end -->

## 项目焦点 <!-- holo:heading -->

_(none yet — delete this marker once content is added)_
