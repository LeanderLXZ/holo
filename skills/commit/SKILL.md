---
name: commit
description: 提交当前 working tree 改动 — 校验追踪状态（禁提路径 / 大文件 / 未跟踪文件），按逻辑单元分 commit，message 对齐仓库惯例（drawn from git log）。$ARGUMENTS = commit 主题（可选）。不 push / 不 force / 不 amend / 不 --no-verify；跨文件 ai_context/docs 对齐 → /go，跨分支同步 → /forward。触发：commit / 提交一下 / 提交当前改动。
---

# /commit — 快速确认并提交当前改动

对当前 working tree 做一次轻量校验，确认改动有效、追踪状态无误后 commit。**不做全仓 review、不动 ai_context / docs 对齐**（那是 `/go` 的事）；**不做跨分支同步**（那是 `/forward` 的事）。

## Progress reporting

下方流程分为 `## Step 0:` ~ `## Step 3:`（前置一段 `## $ARGUMENTS 解析` 是参数解析，不算正式 step）。

**进入 Step 0 之前**：调用 **<进度工具>** 把 Step 0 ~ Step 3 全部预登记（每个 step 一条，`content` 用 `Step N: <子段标题>`，`status` 全为 `pending`；`$ARGUMENTS` 解析不计入）。这是硬性要求，**不调 <进度工具> 不许往下走**。

每进入一个 step：调 **<进度工具>** 把当前 step 改 `in_progress`（同一次调用里把上一个 step 标 `completed`），然后做实际工作。**step 跨越时不要漏调**。进度由 <进度工具> 的 UI 直接显示，**对话里不再打 `[/commit] Step N: ...` 之类的进度行**。

跳过某 step：调 **<进度工具>** 把对应条目直接标 `completed`，并在对话里打一行 `Step N 跳过（理由：…）`——"理由"是 UI 缺失的信息，保留这一行；不要静默略过。

最后一步完成：调 **<进度工具>** 把最后一条标 `completed`。

**<进度工具> 解析**：Claude → `TodoWrite`（界面显示为 "Update Todos"）；Codex → `update_plan`；其他 runtime（无结构化进度工具，如 Copilot agent mode）→ 在 response 文本里维护一份 markdown checkbox 列表当 step 状态，每次状态切换前整段重写一遍。语义对齐：预登记 + 切状态 + 标完成。

## `$ARGUMENTS` 解析

`$ARGUMENTS` 整体作为 commit message 的提示 / 主题（参见 Step 3）；为空时由 diff 自动归纳消息。**不再含 sync 触发词**——跨分支同步请用 `/forward`。

## Step 0: Load skills config

`Read` `ai_context/skills_config.md`。

- 文件不存在 / 某节标题缺失 → fail loudly：打印缺失项 + 提示按 plugin 模板补全，停手
- 某节内容 `(none)` 或留空 → 跳过该节相关步骤（视为本项目无此项）
- 某节列了具体路径但路径不存在 → fail loudly：提示该节漂移到不存在路径，停手等用户修

后续步骤出现 "skills_config.md `## XX`" 时引用本配置。本 skill 用到：
`## Do-not-commit paths`（Step 2 追踪状态扫描）。

## Step 1: 改动有效性

- `git status` + `git diff --stat` 看 working tree 与 index
- **若完全没有改动**（working tree 干净 + index 空）：本轮无 commit 可造，打印"无改动可提交"并结束；后续 step 全部跳过
- 扫改动列表，判断是否值得独立 commit（不是空白 / 误保存 / 临时 debug 打印）；有可疑 → 先问用户

## Step 2: 追踪状态

- 扫禁提路径：按 skills_config.md `## Do-not-commit paths` 列表 +（`.gitignore` + `ai_context/conventions.md`）兜底
- `git ls-files --others --exclude-standard` 看未跟踪文件，判断是否应该一并加入 / 加入 .gitignore / 留着
- 大文件（>1MB）或二进制单独列出，请用户确认是否入库
- 任一项可疑 → 停手问用户，不要擅自 `git add -A`

## Step 3: Commit

- 按逻辑单元分 commit（若单次改动跨多个独立主题）；一次别塞太多
- message 风格对照 `git log --oneline -10`，保持仓库惯例（中英文 / prefix / 动词时态）
- `$ARGUMENTS` 非空 → 以此为主题扩写；否则根据 diff 归纳
- 执行 `git add <具体文件>` + `git commit`（**不用 `git add -A` / `git add .`**，避免误入敏感文件）
- commit 后 `git status` 确认干净

完成后打印一行 `commit OK：<short-sha> <subject>` 收尾。如需 forward 到其他分支，由用户随后显式调用 `/forward`。

## 约束

- 不 `git push`、不 `--force`、不 `--amend`、不切分支、不 merge（除非用户明确要求）
- 发现可疑（禁提路径、巨型 diff、未解决冲突）→ 停手问，不绕过
- 不做跨分支同步——这部分能力已迁移到 `/forward`
