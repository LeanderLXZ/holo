# <project-name> — Agent Entry Point

本文件由 coding agents 在会话开始时自动加载。保持简短 ——
详细上下文放在 `ai_context/`，不在此处。

## 语言

`ai_context/skills_config.md §Language` 携带两条轴 ——
`content_language`（落盘类输出：docs / logs / commits / skill
输出 / 新增代码注释）与 `conversation_language`（AI ↔ 用户对话）。
会话开始时读取，本次会话内一律按此应用。代码标识符与字段名
保持英文。

## 会话开始：通读 ai_context/ 一次

在**每个新会话**开始时，按 `ai_context/instructions.md` 指定的
顺序通读整个 `ai_context/` 目录：

1. `conventions.md`
2. `project_background.md`
3. `requirements.md`
4. `read_scope.md`
5. `current_status.md`
6. `architecture.md`
7. `decisions.md`
8. `next_steps.md`
9. `handoff.md`

读完后，**停下来等待用户指令。** 不要自行开始修改代码、schema 或
文档。

## 默认不加载的内容

参见 `ai_context/read_scope.md` 中本项目专属的清单。

通用规则：除非任务明确要求，否则不要扫描大型原始输入、完整对话
历史、整个日志目录、生成产物、数据库、向量库及索引。

## 行动 vs. 加载

读 `ai_context/` 是上下文加载，不是任务说明。只在用户显式请求时
行动。如果在阅读过程中发现异常，记录下来并等待 —— 不要主动修复。

## 稀释自查

长会话会导致静默遗忘。在编辑代码、schema 或文档之前 —— 以及任何
任务类型切换之后 —— 暂停并回答：

1. **范围检查**：我做的是用户要求的那件事，还是扩展到了主动重构
   /"顺手改一下"？若扩展了 → 停下来先问。
2. **正确层级**：我即将编辑的文件是否位于此关注点所属的正确模块 /
   层？若不确定 → 重读 `ai_context/architecture.md`。
3. **对齐检查**：在收尾一组改动前，对照 `ai_context/conventions.md`
   中的 Cross-File Alignment 表 —— 是否更新了每一个下游文件？

如果任一答案是"我不记得了"或"我在猜" → 在继续之前重读相关的
`ai_context/` 文件。

## 与 CLAUDE.md 保持同步

本文件与 `CLAUDE.md` 保持**完全一致**，仅标题行不同（"Agent
Entry Point" vs. "Claude Entry Point"）。对其中之一的任何改动
必须在同一次 commit 中镜像到另一文件。
