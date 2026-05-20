<!--
MAINTENANCE — 编辑本文件前请先阅读。
本文件是用于快速回到项目状态的索引，不是详细手册。
1. 写"是什么 / 去哪找"；链接到权威源（代码路径、docs/*.md、schema、logs）。
2. 优先删减而非新增；新增前先检查是否能并入已有条目。
3. 只描述当前设计 —— 不写"legacy / deprecated / formerly / renamed from"。
4. 不出现真实产品 / 客户 / 私有内容名称 —— 使用结构性占位符。
越短越好；每条都是总结后的要点，不是细节堆叠 —— 细节推到链接的源里。
-->

# 给后续 AI 智能体的指引

## 入口点

`ai_context/` 是 handoff 入口。默认不要重读整段对话历史或大型产物
目录。只有当用户的任务明确需要时，才加载更重的层（logs、原始输入、
生成产物）。

读完 `ai_context/` 后，**停下来等待**下一条指令。读 `ai_context/`
是上下文加载，不是任务说明。只在用户显式请求时行动。

## 阅读顺序

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

## 更新预期

仅在**仓库的持久事实**（长期惯例、架构、schema、决策）发生变更时
更新 `ai_context/`。短期运行时状态 / 单任务进度归 work-local 进度
文件或 TODO 列表，不归这里。

## 日志记录

`ai_context/` 之外的每次改动 → 按 `conventions.md` §Logging 的
契约在 `logs/change_logs/` 下落一条条目。负责 logging 格式的 skill
（`/go` / `/do` / `/post-check`，当本项目使用它们时）直接写文件 ——
不要在此处重复格式。

## TODO 清单

`docs/todo_list.md` —— 已规划但未完成任务的工作队列。按需读取，
**不**纳入会话起始的读取顺序。使用规则写在该文件自身的
`## File guide` 段。

## 项目焦点

_(none yet — delete this marker once content is added)_
