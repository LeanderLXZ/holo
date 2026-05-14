---
name: holo-init
description: 项目骨架初始化 — 把 plugin 内 templates/project-skeleton/ 的标准骨架（CLAUDE.md / AGENTS.md / ai_context/ / docs/todo_list.md / logs/）落到当前工作目录，再基于仓库探测 + 用户问询（项目名 / 描述 / 主分支 / 时区）把模板里的 <...> 占位符填成项目实际值。可选生成 .agents/skills/ 镜像（用于 Codex / 其他非 Claude runtime 的 cross-validation）。无参数；当前目录是否空 / 是否已初始化都能识别处理。绝不静默覆盖（冲突一律问用户 keep / overwrite / merge），不动非模板文件，不 git add / 不 commit。用户说"初始化项目"、"holo-init"、"装一下骨架"、"建一个空项目" 时触发。
---

# /holo-init — 项目骨架初始化

把 `${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton/` 下的模板落到当前工作目录，然后基于仓库探测 + 用户问询，把模板里的 `<...>` 占位符填成项目实际值。**不动已存在的非模板文件**；模板冲突一律停手问用户，不静默覆盖。

无参数。仓库当前状态自己探测（空目录 / 已有代码 / 已被初始化过都能处理）；不需要 mode flag。

## Progress reporting

下方流程分为 `## Step 0:` ~ `## Step 3:`。

**进入 Step 0 之前**：调 **<进度工具>** 把 Step 0 ~ Step 3 全部预登记（每个 step 一条，`content` 用 `Step N: <子段标题>`，`status` 全为 `pending`）。**不调 <进度工具> 不许往下走**。

每进入一个 step：把当前 step 改 `in_progress`、上一个标 `completed`，然后做实际工作。跳过某 step：直接标 `completed`，并在对话里打一行 `Step N 跳过（理由：…）`。

**<进度工具> 解析**：Claude → `TodoWrite`（界面显示为 "Update Todos"）；Codex → `update_plan`；其他 runtime（无结构化进度工具，如 Copilot agent mode）→ 在 response 文本里维护一份 markdown checkbox 列表当 step 状态，每次状态切换前整段重写一遍。语义对齐：预登记 + 切状态 + 标完成。

## Step 0: 探测仓库状态

目的：在动任何文件之前，把"目标目录长什么样"先打清楚，让后续步骤有准确依据。

**0.1 工作目录基本状态**

- `pwd` 确认当前工作目录绝对路径
- `ls -la` 看顶层文件 / 目录清单
- `test -d .git && git status --short` 看是否 git repo + 工作树状态。dirty → 打印警告（不停手，因为 `/holo-init` 不 commit；但提示用户先 stash / commit 已有改动能让 git 历史更清晰）

**0.2 模板清单 + 冲突预扫**

- 模板源目录：`${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton/`（若 `${CLAUDE_PLUGIN_ROOT}` 未设置，从本命令所在路径反推到 plugin 根 + `templates/project-skeleton/`）
- `find "${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton" -type f` 列出全部模板文件（含 `.gitkeep`）
- 对每个模板文件，相对路径映射到目标目录：
  - 目标不存在 → 状态 `NEW`
  - 目标存在且内容与模板**完全一致**（`diff -q`）→ 状态 `SAME`
  - 目标存在但内容不同 → 状态 `CONFLICT`
- 输出一张表（按状态分组）：每行 `状态 | 相对路径 | 字节数对比`

**0.3 仓库内容探测**（为 Step 2 问询预填值用）

- 项目名候选（按优先级取第一个非空）：
  1. `package.json` 的 `name` 字段
  2. `pyproject.toml` 的 `[project] name` 或 `[tool.poetry] name`
  3. `Cargo.toml` 的 `[package] name`
  4. `go.mod` 的 module 路径末段
  5. 仓库根目录名
- 一句话描述候选：上述 manifest 的 `description` 字段；若无 → 取既有 `README.md` 首段第一句
- Git remote URL：`git remote get-url origin 2>/dev/null`
- 主分支：`git symbolic-ref --short HEAD 2>/dev/null` + `git branch --list main master`（默认 `main`）
- 顶层目录清单（除 `.git/` / `node_modules/` / `__pycache__/` / `.venv/` 等明显噪声）：作为 `architecture.md` 的 Top-Level Structure 候选 + `skills_config.md` 的 Source / Data contract / Example artifact 候选
- 时区：本机 `date +%Z` 作为 `skills_config.md` §Timezone 默认值

**0.4 询问是否生成 `.agents/skills/` 镜像**

用 **<问询工具>** 问一题：

> 生成 `.agents/skills/` 镜像？（把 plugin 的 14 个 SKILL.md 复制到本项目 `.agents/skills/<name>/SKILL.md`。用途：让 Codex / 其他非 Claude runtime 也能识别本套 commands / skills 做 cross-validation。不需要的话选 No——本仓库里只用 Claude / Claude Code 调用 plugin 就够了，不必冗余一份本地副本。）

选项：

- `No`（默认推荐）：跳过 `.agents/` 生成
- `Yes`：Step 1 额外把 plugin 内 `${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md` 全部 14 个（5 个 query skill + 9 个 command 镜像）复制到目标目录 `.agents/skills/<name>/SKILL.md`，Step 3 加镜像校验

记录用户选择（下文记为 `<.agents-opt>`）。

**0.5 打印 plan**

把上面汇总成"将要执行的计划"打印一次：

```
模板文件：NEW=X | SAME=Y | CONFLICT=Z
冲突文件（需用户决定）：<list>
.agents/skills/ 镜像：<yes / no>
探测到的预填值：
  - 项目名候选：<value>
  - 一句话描述：<value>
  - 主分支：<value>
  - 时区：<value>
  - 顶层目录：<list>
```

## Step 1: 复制模板（含冲突处理）

目的：把模板文件落到目标目录。

**1.1 模板文件复制**

对每个文件根据 Step 0.2 的状态决策：

**`NEW`**：直接复制。父目录不存在则先 `mkdir -p`。

**`SAME`**：no-op，跳过。在对话里打一行 `Skipped (already identical): <path>`。

**`CONFLICT`**：**全部一次性问用户**——不要一个文件一个文件问。

使用 **<问询工具>** 给出每个冲突文件的 diff 摘要（`diff -u` 前 10 行 + 后 10 行，过长用 `... (N more lines)` 截断），让用户对每个文件选：

- `keep`：保留现状，跳过该模板
- `overwrite`：用模板覆盖
- `merge`：把模板内容追加到现有文件末尾（用 `\n\n<!-- ↓ holo-skeleton template content ↓ -->\n\n` 分隔）；仅对 markdown 文件可选

**<问询工具> 解析**：Claude → `AskUserQuestion`（每次最多 4 题，超过分批问）；其他 runtime（无结构化询问工具，如 Codex / Copilot agent mode）→ 在 response 文本里编号列出问题 + 每题的可选选项，让用户一次回答（仍按每批最多 4 题，超过分批问）。

用户回答后逐文件执行决策。

**1.1 收尾**：再跑一次 Step 0.2 的状态扫描，确认所有模板文件状态变为 `SAME`（除用户选 `keep` 的）；任何残留 `CONFLICT` → 报错停手（说明用户的选择没生效）。

打印结果：`Created: A | Skipped (identical): B | Skipped (kept existing): C | Overwritten: D | Merged: E`。

**1.2 `.agents/skills/` 镜像复制**

仅当 Step 0.4 用户选了 `Yes` 时执行；选 `No` 跳过本子段。

- 源目录：`${CLAUDE_PLUGIN_ROOT}/skills/`，共 14 个 `<name>/SKILL.md`（5 个 query skill：`branch-inventory` / `monitor` / `recent-activity` / `run-prompt` / `todo`；9 个 command 镜像：`check-review` / `commit` / `full-review` / `go` / `holo-init` / `plan` / `post-check` / `push` / `todo-add`）
- 目标：`<workdir>/.agents/skills/<name>/SKILL.md`
- 对每个 `<name>`：
  - `mkdir -p .agents/skills/<name>`
  - `cp "${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md" ".agents/skills/<name>/SKILL.md"`
  - 若目标已存在：用 Step 1.1 同款冲突处理 (`keep` / `overwrite`)；不支持 `merge`（YAML frontmatter 合并易出错）
- 复制完成后逐个 `diff` 校验目标 == 源（byte-for-byte），任一不一致 → 报错停手

打印结果：`.agents/skills/: Copied N | Skipped (identical) M | Kept existing K | Overwritten W`。

## Step 2: 探测 + 问询 + 填充

目的：把模板里的 `<...>` 占位符替换成项目实际值。

**2.1 grep 出待填占位符**

```bash
grep -rn '<[^>]*>' CLAUDE.md AGENTS.md README.md ai_context/ docs/ 2>/dev/null | grep -v '^[^:]*:[^:]*:<!--'
```

排除注释里的 `<!--` 开头行（那是 MAINTENANCE 注释）。剩下的每条 `<...>` 都是待填占位符。按文件分组打印一次。

**2.2 必填问询（Round 1）**

用 **<问询工具>** 一次问 4 题（Step 0.3 探测到的值作为 `Recommended` 选项；用户可选 `Other` 自填）：

1. 项目名（用于 CLAUDE.md / AGENTS.md / README.md 的 `<project-name>`）
2. 一句话项目描述（用于 README.md 的 `<one-line project description>`）
3. 主分支名（用于 `ai_context/skills_config.md` §Main branch policy；默认 `main`）
4. 时区命令模板（用于 `ai_context/skills_config.md` §Timezone；默认 `TZ='UTC' date '+%Y-%m-%d_%H%M%S'`）

收到回答后**立即**用 `Edit` 写入对应文件（不要攒一批后批量写——中断也保留进度）。

**2.3 顶层目录分类问询（Round 2）**

如果 Step 0.3 探测到顶层有除 `.git/` / `ai_context/` / `docs/` / `logs/` 之外的其他目录，用 **<问询工具>** 问最多 4 题，每题给一个探测到的目录，让用户分类：

- `source` → 写入 `skills_config.md` §Source directories
- `data-contract` → 写入 `skills_config.md` §Data contract directories
- `example-artifact` → 写入 `skills_config.md` §Example artifact directories
- `do-not-commit` → 写入 `skills_config.md` §Do-not-commit paths
- `skip` → 不写入任何 section

超过 4 个目录 → 分批问。没有这类目录（空目录初始化场景）→ 整个 Round 2 跳过。

**2.4 探测可推断的填充（不问，直接写）**

以下值可以从 Step 0.3 直接派生，不再问用户：

- `architecture.md` 的 Top-Level Structure：把 Step 0.3 的顶层目录清单展开成 `- \`<dir>/\` — <推断说明 / 留空待用户填>` 形式（推断说明留 `<...>` 让用户补）
- `read_scope.md` 的 Default Priority：自动加入既有的 `docs/` / 顶层 README.md（如有）

**2.5 不填的占位符**

剩下的 `<...>` —— 项目背景、需求、当前状态、决策、next steps、handoff 等具体内容 —— 一律**不在 `/holo-init` 内问**。这些应该由用户后续通过 `/go` 或直接编辑慢慢填充。

## Step 3: 收尾验证

**3.1 占位符残留扫描**

再跑一次 Step 2.1 的 grep，把还剩的 `<...>` 列成清单：

```
还需手动填写（N 处）：
  ai_context/project_background.md:12  <one or two sentences naming the project's primary goal>
  ai_context/project_background.md:16  <3–5 short bullets …>
  ...
```

**3.2 skills_config.md 自检**

`Read` `ai_context/skills_config.md`，检查以下 11 个 section header 是否全部存在：

```
## Background processes
## Protected branch prefixes
## Main branch policy
## Do-not-commit paths
## Source directories
## Data contract directories
## Example artifact directories
## Core component keywords
## Sensitive content placeholder rules
## Timezone
## Activity sources
```

任一 header 缺失 → 报错停手（说明 Step 1 / Step 2 把文件弄坏了）。

**3.3 CLAUDE.md / AGENTS.md 同步校验**

`diff CLAUDE.md AGENTS.md` —— 应只有第一行（`# <project-name> — Claude Entry Point` vs `Agent Entry Point`）不同。其他行 diff → 警告（说明 Step 2 只更新了一边）。

**3.4 `.agents/skills/` 镜像验证**（仅当 Step 0.4 选 `Yes`）

- 对 14 个 `<name>` 逐个 `diff .agents/skills/<name>/SKILL.md "${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md"` —— 必须完全一致；不一致 → 报错列出差异路径（说明 1.2 的 copy 没生效或被中途篡改）
- 顺手做一次 plugin 内部对齐 spot check：对 9 个 command 镜像，校验 `${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md` 的 body（去掉前 5 行 frontmatter）与 `${CLAUDE_PLUGIN_ROOT}/commands/<name>.md` 完全一致。**任一不一致只警告不停手**（这是 plugin 本身的问题，不是 /holo-init 能修的；提示用户上报 plugin issue）

**3.5 总结打印**

```
✅ /holo-init 完成

模板：Created A | Skipped (identical) B | Kept existing C | Overwritten D | Merged E
.agents/skills/ 镜像：<生成 14 / 跳过>

下一步建议：
  1. 填写剩余占位符（见上方 N 处清单）—— 建议先填 ai_context/project_background.md + handoff.md
  2. 用 git add + commit 把骨架先提交一次，再分次填内容（git 历史更干净）
  3. 后续用 /go / /commit / /todo-add 等 skill 维护项目
```

## 约束

- **绝不静默覆盖**：任何模板冲突必须问用户
- **不动非模板文件**：模板路径之外的现有文件一律不碰
- **不 `git add` / 不 commit**：`/holo-init` 只生成 / 修改文件，提交由用户自己用 `/commit` 处理
- **占位符语法固定 `<...>`**：grep / Edit 都依赖这个约定；不要引入 `{{...}}` / `$VAR` 等其他形态
- **中断保留进度**：Step 2 的每个填充值收到回答后立即写盘，不批量延后

---

**镜像约束**：`commands/holo-init.md` ↔ `skills/holo-init/SKILL.md` 必须**逐字镜像** —— 从一级标题 `# /holo-init` 起到本约束段之前的正文两侧完全一致；任一侧修改必须在同 commit 内镜像到另一侧。`skills/holo-init/SKILL.md` 额外带 YAML frontmatter（`name` / `description`），其余无差异。
