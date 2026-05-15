---
description: 把当前分支的最新 commit 显式 forward / merge 到指定（或全部候选）目标分支 — 加载配置 → 前置校验（dirty 即停） → 候选预检（不存在 / 受保护 / 已同步 / dirty / 进程 / 冲突 分类） → 批量无障碍 merge → 障碍分支逐条询问（仅 ⚠️ 才问） → 最终结果列表。$ARGUMENTS = 目标分支列表（空格分隔；省略 = 所有候选非当前分支）。源分支恒等于当前分支；不 push / 不 force / 不 amend。用户说"/forward"、"forward 一下"、"把当前分支同步到 develop"、"把 commit 推到其他分支" 时触发。
---

# /forward — 显式分支同步

把当前分支（= 源分支）的最新 commit `git merge` 到一或多个目标分支。
**纯 merge，不 push / 不 --force / 不 --amend / 不 rebase**——只是把当前分支
fast-forward / merge commit 进各目标。

## Progress reporting

下方流程分为 `## Step 0:` ~ `## Step 5:`（前置一段 `## $ARGUMENTS 解析` 是参数解析，不算正式 step）。

**进入 Step 0 之前**：调用 **<进度工具>** 把 Step 0 ~ Step 5 全部预登记（每个 step 一条，`content` 用 `Step N: <子段标题>`，`status` 全为 `pending`；`$ARGUMENTS` 解析不计入）。这是硬性要求，**不调 <进度工具> 不许往下走**。

每进入一个 step：调 **<进度工具>** 把当前 step 改 `in_progress`（同一次调用里把上一个 step 标 `completed`），然后做实际工作。**step 跨越时不要漏调**。进度由 <进度工具> 的 UI 直接显示，**对话里不再打 `[/forward] Step N: ...` 之类的进度行**。

跳过某 step：调 **<进度工具>** 把对应条目直接标 `completed`，并在对话里打一行 `Step N 跳过（理由：…）`——"理由"是 UI 缺失的信息，保留这一行；不要静默略过。

最后一步完成：调 **<进度工具>** 把最后一条标 `completed`。

**<进度工具> 解析**：Claude → `TodoWrite`（界面显示为 "Update Todos"）；Codex → `update_plan`；其他 runtime（无结构化进度工具，如 Copilot agent mode）→ 在 response 文本里维护一份 markdown checkbox 列表当 step 状态，每次状态切换前整段重写一遍。语义对齐：预登记 + 切状态 + 标完成。

**<问询工具> 解析**：Claude → `AskUserQuestion`（每次最多 4 题，超过分批问）；其他 runtime（无结构化询问工具，如 Codex / Copilot agent mode）→ 在 response 文本里编号列出问题 + 每题的可选选项，让用户一次回答（仍按每批最多 4 题，超过分批问）。

## `$ARGUMENTS` 解析

`$ARGUMENTS` = 目标分支名列表（空格分隔），按以下规则处理：

1. **`$ARGUMENTS` 为空** → 目标 = 所有"候选非当前分支"，定义为：
   `git branch --format='%(refname:short)'` 列出的全部本地分支，排除当前分支
2. **`$ARGUMENTS` 非空** → 拆 token 取每个 token 作为目标分支名；token 全部加入候选清单（不在此处校验存在 / 同步状态，留给 Step 2）

源分支恒等于 `git branch --show-current`（**当前分支**）——`/forward` 不接受
"源" 参数。要换源 → 用户先 `git checkout <source>` 再跑 `/forward`。

## Step 0: Load skills config

`Read` `ai_context/skills_config.md`。

- 文件不存在 / 某节标题缺失 → fail loudly：打印缺失项 + 提示按 plugin 模板补全，停手
- 某节内容 `(none)` 或留空 → 跳过该节相关步骤（视为本项目无此项）
- 某节列了具体路径但路径不存在 → fail loudly：提示该节漂移到不存在路径，停手等用户修

后续步骤出现 "skills_config.md `## XX`" 时引用本配置。本 skill 用到：
`## Background processes`（Step 2 候选预检：进程检测）、
`## Protected branch prefixes`（Step 2 候选预检：保护分支分类）、
`## Main branch policy`（Step 2 候选预检：主分支保护提示）。

## Step 1: 前置校验

- `git branch --show-current` 取源分支；游离 HEAD（detached）→ 停手报告，让用户先 checkout
- `git status --porcelain` 检查工作区：
  - **dirty**（任何 staged / unstaged / untracked-not-ignored 改动）→ **停手报告**，让用户先 `/commit` 或 `git stash`；`/forward` 不接受 dirty 源
  - clean → 进 Step 2
- 源分支 commit 计数为 0（空仓库 / 新建分支无任何 commit）→ 停手报告

## Step 2: 候选预检（分类）

对 `$ARGUMENTS` 解析得到的每个目标分支，逐条分类：

| 分类标签 | 触发条件 | 后续处理 |
|---|---|---|
| ❌ 不存在 | `git rev-parse --verify <branch>` 失败 | Step 3 / Step 4 全跳过；最终结果列表标注 |
| 🔒 受保护 | 分支匹配 skills_config.md `## Protected branch prefixes` 列出的前缀（`(none)` 时本类不触发） | 进 Step 4 询问（默认建议跳过） |
| ⚙️ 有进程 | 按 skills_config.md `## Background processes` 检测到 pgrep 模式命中（`(none)` 时本类不触发） | 进 Step 4 询问（默认建议跳过） |
| 💾 dirty | 该分支对应 worktree 工作区有未提交改动（`git -C <worktree> status --porcelain` 非空；非 worktree 形态的分支退化为"未实际 checkout 过的分支 → 视为干净"） | 进 Step 4 询问 |
| ✅ 已同步 | `git merge-base --is-ancestor <source> <branch>` 返回 0（即 source 是 branch 的祖先） | Step 3 / Step 4 全跳过；最终结果列表标"已同步，跳过" |
| ⚠️ 预检冲突 | dry-run 检测 merge 会冲突——git ≥ 2.38 优先用 `git merge-tree --write-tree --no-messages <source> <branch>` 退出码非零即冲突；旧 git 退回 `git merge-tree $(git merge-base <source> <branch>) <source> <branch>` 扫描输出的 `<<<<<<<` 标记 | 进 Step 4 询问 |
| 🟢 可直接 merge | 上述全部不触发 | 进 Step 3 批量执行 |

打印分类小表（一行一分支：`<branch> | <标签> | <一句话说明>`），让用户在 Step 3 / Step 4 前有完整视图。

## Step 3: 批量无障碍 merge

对所有标 🟢 的目标分支**逐个无询问**执行 merge：

- 若该分支 = 当前 HEAD（不可能——已在 Step 2 排除当前分支；保留这条防御性判断）→ 跳过
- 否则 `git checkout <branch> && git merge <source>`
  - fast-forward 通过 → 打印一行 `✅ <branch>: ff-merge OK`
  - 形成 merge commit → 沿用 git 默认 commit message（`Merge branch '<source>'`），打印一行 `✅ <branch>: merge commit OK`
  - 运行中**意外**冲突（与 Step 2 dry-run 不一致；可能因外部状态变化）→ `git merge --abort` 回到干净状态，把该分支标为 ⚠️ 后续询问；不停手往下走
- 全部处理完后 `git checkout <source>` 回到源分支

## Step 4: 障碍分支逐条询问（仅 ⚠️ 类才问）

按分类标签处理：

- **❌ 不存在 / ✅ 已同步** → **不问**，直接归入最终结果列表
- **🔒 受保护 / ⚙️ 有进程 / 💾 dirty / ⚠️ 预检冲突 / Step 3 意外冲突** → 逐条用 **<问询工具>** 问，每题 3 选项：
  1. **跳过此分支（推荐）** — 不动该分支，列入最终结果"已跳过：<原因>"
  2. **仍然合并** — 执行机制按分类分支：
     - **🔒 受保护 / ⚙️ 有进程 / ⚠️ 预检冲突 / Step 3 意外冲突** → `git checkout <branch> && git merge <source>`；冲突则 `git merge --abort` 回原状态并标"⚠️ 冲突待人工处理"；合并完后回 `git checkout <source>`
     - **💾 dirty**（目标 = 另一 worktree 的 dirty 工作区，目标分支已 checked out 在该 worktree，源端 `git checkout <branch>` 会被 git 拒绝）→ **不**做 source 端 checkout，改用 `git -C <worktree-path> merge <source>` 直接在目标 worktree 里合并；目标的 dirty 改动保持原样（git 自身会因合并涉及未提交改动而拒绝，此时回到询问让用户先在目标 worktree commit / stash 后重试）；冲突则 `git -C <worktree-path> merge --abort` 回原状态并标"⚠️ 冲突待人工处理"
  3. **停手让我手动处理** — 终止 `/forward`，打印当前已完成 / 待处理状态，**整个 skill 结束**

问完所有 ⚠️ 分类后，无论用户怎么选，都进 Step 5。

## Step 5: 最终结果列表

打印一张结果表（**始终打印，不要省略**）：

```
源分支：<source>

目标分支 | 状态
--------|-----
<b1>    | ✅ 已合并（ff）
<b2>    | ✅ 已合并（merge commit）
<b3>    | ✅ 已同步，跳过
<b4>    | ⏭ 用户选择跳过（原因：<标签>）
<b5>    | ⚠️ 冲突待人工处理
<b6>    | ❌ 分支不存在
```

末尾打印 `当前 HEAD：<source>` 确认 `/forward` 没把用户留在别的分支。**不 push**（`/push` 是独立操作）。

## 约束

- **纯 merge**：不 `git push`、不 `--force` / `--force-with-lease`、不 `--amend`、不 `git rebase`、不 `git reset`（除冲突时 `git merge --abort` 外不动 git ref）
- **源恒等于当前分支**：换源由用户先 `git checkout`，`/forward` 不接受 source 参数
- **dirty 源 = 停手**：不"先 stash 再 forward"，由用户自己决定 stash / commit
- **冲突 = 停手询问**：不自动解决冲突；用户选"仍然合并"遇真实冲突也只是 abort，不留半合并状态
