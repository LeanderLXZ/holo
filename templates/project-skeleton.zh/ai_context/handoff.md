<!--
MAINTENANCE — 编辑本文件前请先阅读。
本文件是用于快速回到项目状态的索引，不是详细手册。
1. 写"是什么 / 去哪找"；链接到权威源（代码路径、docs/*.md、schema、logs）。
2. 优先删减而非新增；新增前先检查是否能并入已有条目。
3. 只描述当前设计 —— 不写"legacy / deprecated / formerly / renamed from"。
4. 不出现真实产品 / 客户 / 私有内容名称 —— 使用结构性占位符。
越短越好；把细节推到链接的源里，而不是让本文件变长。
-->

# 交接

会话起始读取顺序的最后一个文件。向未来的 AI 会话交付一个可工作的
心智模型、一份 quick-start 指南，以及一份"用户在意的事"清单 ——
这些不是正式 requirement，但塑造每一次调用。

## 思维模型

<2–4 句简短描述当前项目在概念层面的位置 —— 设计已对齐、骨架已搭、
首个 feature 已完成等。这是 `current_status.md` 的人类可读版本。>

## 快速上手

<3–6 步编号列表：按什么顺序读哪些文件、入口文档在哪、如何运行 /
查看系统。每步一行。>

## 常用操作命令

<本项目最常用命令的简短列表 —— CLI 调用、构建 / 测试命令、部署
触发。每条一行。如果项目还没有，写 `(none yet)`。>

## 用户在意的事

<偏好、品味与"软"规则的项目列表 —— 这些不在正式 requirement 里，
但一旦违反必定触发用户反馈。示例：

- "Behavior consistency over surface tone"
- "No raw inputs pasted into logs / docs"
- "Incremental updates, never restart from scratch"
- "No real product / customer names in canonical docs"

每条一行。每当用户给出指向持久偏好（而非一次性修复）的反馈时，
更新此处。>

## 每个里程碑之后

1. 按 `conventions.md` §Logging 落一条 `logs/change_logs/` 条目。
2. 仅当变更是持久的，更新 `current_status.md`、`next_steps.md`
   与本文件。
