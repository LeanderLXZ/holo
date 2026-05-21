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
   - 目标 ≤ 5 行，更长的细节推到链接的来源里（docs/<topic>.md）。
   - 不要压缩或改动与当前编辑无关的内容。
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
