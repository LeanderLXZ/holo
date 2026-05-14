---
description: plugin 升级后的项目同步检查 — 把当前项目里跟 plugin 关联的产物（.agents/skills/ 镜像、ai_context/ 结构、CLAUDE.md/AGENTS.md、docs/logs/ 骨架）跟当前装上的 plugin (${CLAUDE_PLUGIN_ROOT}) 比对，找出 plugin 升级了但项目没跟上的 drift（.agents 镜像 STALE/MISSING/ORPHAN、模板新增文件、模板新增 section header），按类别报告并询问是否自动修。只动结构性 drift；不动用户填的内容。无参数；不 git add / 不 commit。用户说"plugin 升级了"、"holo-update"、"同步 holo 更新"、"检查 holo 是否最新" 时触发。
---

# /holo-update — plugin 升级后的项目同步检查

把当前项目里跟 plugin 关联的产物（`.agents/skills/` 镜像、`ai_context/` 结构、`CLAUDE.md` / `AGENTS.md`、`docs/` / `logs/` 骨架）跟当前装上的 plugin (`${CLAUDE_PLUGIN_ROOT}`) 比对，找出"plugin 升级了但项目里没跟上"的地方，按类别报告并询问是否自动修。

无参数。**只动 plugin 升级带来的结构性 drift**（缺文件、缺 section header、镜像 stale）；**不动用户填进去的内容**。

## Progress reporting

下方流程分为 `## Step 0:` ~ `## Step 4:`。

**进入 Step 0 之前**：调 **<进度工具>** 把 Step 0 ~ Step 4 全部预登记（`status` 全为 `pending`）。**不调 <进度工具> 不许往下走**。

每进入一个 step：把当前 step 改 `in_progress`、上一个标 `completed`。

**<进度工具> 解析**：Claude → `TodoWrite`；Codex → `update_plan`；其他 runtime → 在 response 文本里维护 markdown checkbox 列表。

## Step 0: 前置检查

**0.1 plugin 信息**

- 解析 `${CLAUDE_PLUGIN_ROOT}`（若未设置，从本命令所在路径反推到 plugin 根）
- 读 `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` 的 `name` + `version`，打印 `Checking project against <name> v<version>...`

**0.2 项目是否已被 /holo-init 过**

判定条件（任一存在即认为已初始化）：

- `CLAUDE.md` 顶层存在
- `AGENTS.md` 顶层存在
- `ai_context/` 目录存在

都没有 → 打印 `Project has not been initialized — run /holo-init first` 并退出（不报错，正常返回）。

**0.3 工作树状态**

- `test -d .git && git status --short`；dirty → 打印警告但不停手（`/holo-update` 不 commit，跟 `/holo-init` 一致）

## Step 1: `.agents/skills/` 镜像 drift 检查（双源）

仅当 `<workdir>/.agents/skills/` 存在时执行；不存在 → 整段跳过并打印 `Skipped (.agents/skills/ not in this project)`。

`.agents/skills/` 的源是 plugin 的 commands/ + skills/ 两个目录（参考 `/holo-init` Step 1.2 的双源生成逻辑）。drift 检查要把这两个源都覆盖：

**1.1 commands 源（注入 `name:` 后期望的 SKILL.md）**

对每个 `${CLAUDE_PLUGIN_ROOT}/commands/<name>.md`：

- 按 `/holo-init` Step 1.2 同款逻辑算出"期望的 SKILL.md 内容"（frontmatter 注入 `name: <name>`）
- 跟 `.agents/skills/<name>/SKILL.md` 比对：
  - 文件不存在 → `MISSING`（plugin 新加了 command）
  - 存在但内容不一致 → `STALE`（plugin 改了 command body 或 frontmatter）
  - 一致 → 跳过

**1.2 skills 源（byte-for-byte）**

对每个 `${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md`：

- 跟 `.agents/skills/<name>/SKILL.md` byte-compare：
  - 文件不存在 → `MISSING`
  - 不一致 → `STALE`
  - 一致 → 跳过

**1.3 反向枚举（ORPHAN）**

对每个 `.agents/skills/<name>/SKILL.md`：

- plugin 既没有 `commands/<name>.md` 也没有 `skills/<name>/SKILL.md` → `ORPHAN`（plugin 移除了该 command/skill）

汇总 `STALE / MISSING / ORPHAN` 三个列表的数量，进入 Step 4 一起报告。

## Step 2: `templates/project-skeleton/` drift 检查

枚举 `${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton/` 下全部文件，对每个相对路径 `<rel>`：

**2.1 文件级**：

- 项目里 `<rel>` 不存在 → `MISSING_TEMPLATE`（plugin 新增了模板文件，需要 copy 进项目）

**2.2 Section 级**（仅对 `*.md` 文件，且项目里 `<rel>` 已存在）：

不做 byte-级 diff（用户已经填了内容，行级 diff 全是 noise）。改成**比对 `^## ` header 集合**：

- 抽出模板的 `^## ` headers 集合 `T`
- 抽出项目同名文件的 `^## ` headers 集合 `P`
- 差集 `T - P` = 模板有、项目没有 → `MISSING_SECTION`，每条记录为 `<rel>:<header>`
- 差集 `P - T` 不报（用户可能自己加了 section，不算 drift）

参考实现：

```bash
python3 <<'PYEOF'
import os, re, glob
SKEL = os.environ.get('CLAUDE_PLUGIN_ROOT', '.') + '/templates/project-skeleton'
missing_file, missing_section = [], []
for f in glob.glob(f'{SKEL}/**/*', recursive=True):
    if not os.path.isfile(f): continue
    rel = os.path.relpath(f, SKEL)
    if not os.path.exists(rel):
        missing_file.append(rel); continue
    if not rel.endswith('.md'): continue
    def headers(path):
        return {l.rstrip() for l in open(path) if re.match(r'^## ', l)}
    delta = headers(f) - headers(rel)
    for h in sorted(delta):
        missing_section.append(f'{rel}: {h}')
print('MISSING_TEMPLATE:', missing_file)
print('MISSING_SECTION:', missing_section)
PYEOF
```

## Step 3: `CLAUDE.md` / `AGENTS.md` 头部完整性

**3.1** 项目顶层 `CLAUDE.md` 第一行是否还是模板占位 `# <project-name> — Claude Entry Point` —— 是 → 警告"`/holo-init` 时没填项目名"。`AGENTS.md` 同。

**3.2** `diff CLAUDE.md AGENTS.md` —— 除以下三处模板预期 diff 外的差异都警告（说明用户只更新了一边，两边失同步）：

- 第一行 Entry Point 类型（`Claude` vs `Agent`）
- "auto-loaded by ... at session start" 段
- "Sync with X" 段互指

## Step 4: 报告 + 询问 + 自动修

**4.1 汇总打印**

按类别打印 Step 1 / 2 / 3 的发现：

```
Plugin: <name> v<version>

.agents/skills/ 镜像 drift:
  STALE   (N):  <name list>
  MISSING (M):  <name list>
  ORPHAN  (K):  <name list>

模板 drift:
  MISSING_TEMPLATE (X):  <relative-path list>
  MISSING_SECTION  (Y):  <file>:<header> list

CLAUDE.md / AGENTS.md:
  <findings or "OK">
```

若全部为 0 → 打印 `✅ Project is in sync with <name> v<version>; nothing to do.` 并退出。

**4.2 询问**

用 **<问询工具>** 问最多 4 题，每题给一个类别的 `Auto-fix / Skip`：

1. `.agents/skills/` STALE + MISSING + ORPHAN —— `Auto-fix` = 对 STALE/MISSING 用 `/holo-init` Step 1.2 同款双源逻辑重新生成对应 `<name>`（commands 源注入 `name:` 转写；skills 源 byte copy），对 ORPHAN 跑 `rm -rf .agents/skills/<name>/`；`Skip` = 不动
2. MISSING_TEMPLATE —— `Auto-fix` = 对每个 rel 跑 `cp ${CLAUDE_PLUGIN_ROOT}/templates/project-skeleton/<rel> <rel>`（含 `mkdir -p` 父目录）；`Skip` = 不动
3. MISSING_SECTION —— `Auto-fix` = 在对应文件末尾 append 缺失的 header + 一行 `_(TODO — added by /holo-update; fill via /go or direct edit)_`；`Skip` = 不动
4. CLAUDE/AGENTS unsync —— **永远不自动修**（自动 merge 太危险），只列差异让用户手工处理；本题略

类别数量为 0 的题直接跳过不问。所有题都为 0 → 整个 4.2 跳过。

**4.3 应用 + 验证**

按用户答案执行。完成后**跑一次 `/holo-init` Step 3.1 的 placeholder grep**（Python 版） —— 确认 4.2 的 fix 没引入新的 `<...>` 残留。

## Step 5: 总结打印（编号是 5 但位置在 Step 4 之后；不需要预登记）

```
✅ /holo-update 完成

Plugin: <name> v<version>
.agents/skills/:        STALE→A | MISSING→B | ORPHAN→C  (fixed: F1)
模板：                  MISSING_TEMPLATE→D | MISSING_SECTION→E  (fixed: F2)
CLAUDE/AGENTS sync:     <OK / N warnings (manual fix needed)>

下一步建议（若有 _(TODO)_ append 或 manual sync）：
  1. 检查 _(TODO — added by /holo-update)_ 标记，按需填入实际内容
  2. CLAUDE.md ↔ AGENTS.md 手工 sync 后跑 `diff` 验证
  3. `/commit` 把 sync 改动落盘
```

## 约束

- **只动 plugin 升级带来的结构性 drift**（缺文件、缺 section header、镜像 stale）；不动用户已填的内容
- **不 `git add` / 不 commit**：跟 `/holo-init` 一致，提交由用户用 `/commit` 处理
- **CLAUDE/AGENTS 不自动 merge**：只报告差异，不动文件
