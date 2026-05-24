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
1. `conventions.md`
2. `project_background.md`
3. `requirements.md`
4. `read_scope.md`
5. `current_status.md`
6. `architecture.md`
7. `decisions.md`
8. `next_steps.md`
9. `handoff.md`

Dilution self-check（何时重读哪个文件）写在 `CLAUDE.md` /
`AGENTS.md`。
<!-- holo:section end -->

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
