---
description: plugin 升级后的项目同步检查 — 把当前项目跟当前装上的 plugin 比对（`.agents/skills/` 镜像、模板新增文件 / 段 header、`CLAUDE.md` / `AGENTS.md` 头部），找 plugin 升级带来的结构性 drift。**所有检测逻辑由 `${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py` 单一脚本完成**，skill body 不重写规则。≥ 1 drift 时单题汇总询问 Auto-fix all / Skip all；0 drift 静默通过。CLAUDE / AGENTS 类 finding 永远只显示、不自动 merge。无参数；当前目录是否空 / 是否已初始化都能识别处理。不动用户已填的内容，不 git add / 不 commit。用户说"plugin 升级了"、"holo-update"、"同步 holo 更新"、"检查 holo 是否最新" 时触发。
---

# /holo-update — plugin 升级后的项目同步检查

把当前项目里跟 plugin 关联的产物（`.agents/skills/` 镜像、`templates/project-skeleton/` 文件 + section header、`CLAUDE.md` / `AGENTS.md` 头部）跟当前装上的 plugin (`${CLAUDE_PLUGIN_ROOT}`) 比对，找出"plugin 升级了但项目里没跟上"的 drift，单题汇总询问后批量 fix。

**检测规则的 single source of truth = `${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py`**。skill body **不重写检测逻辑**；若需调整规则，改脚本并按 `ai_context/conventions.md` §Cross-File Alignment 同步本文件 + `commands/holo-init.md` Step 1.2。背景见 `ai_context/decisions.md` §Skill Implementation #5。

无参数。**只动 plugin 升级带来的结构性 drift**；**不动用户填进去的内容**。CLAUDE/AGENTS 类 finding 永远只显示、不自动 merge。

## Progress reporting

下方流程分为 `## Step 0:` ~ `## Step 3:`。

**进入 Step 0 之前**：调 **<进度工具>** 把 Step 0 ~ Step 3 全部预登记（`status` 全为 `pending`）。**不调 <进度工具> 不许往下走**。

每进入一个 step：把当前 step 改 `in_progress`、上一个标 `completed`。

**<进度工具> 解析**：Claude → `TodoWrite`；Codex → `update_plan`；其他 runtime → 在 response 文本里维护 markdown checkbox 列表。

**<问询工具> 解析**：Claude → `AskUserQuestion`；其他 runtime → 在 response 文本里编号列出问题 + 选项让用户一次回答。

## Step 0: 前置检查

**0.1 plugin 信息**

- 解析 `${CLAUDE_PLUGIN_ROOT}`（若未设置，脚本会从自身路径反推到 plugin 根；fail loudly 时停手）
- 读 `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` 的 `name` + `version`，打印 `Checking project against <name> v<version>...`

**0.2 项目是否已被 /holo-init 过**

判定条件（任一存在即认为已初始化）：

- `CLAUDE.md` 顶层存在
- `AGENTS.md` 顶层存在
- `ai_context/` 目录存在

都没有 → 打印 `Project has not been initialized — run /holo-init first` 并退出（不报错，正常返回）。

**0.3 工作树状态**

- `test -d .git && git status --short`；dirty → 打印警告但不停手（`/holo-update` 不 commit，跟 `/holo-init` 一致）

## Step 1: 跑检测脚本

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py" --json
```

脚本输出 JSON 结构（**接口契约**，skill body 按此键名解析；变更见 conventions.md §Cross-File Alignment）：

```json
{
  "plugin_root": "...", "target_root": "...",
  "agents_sync": {
    "skipped": false,
    "stale":   [{"name": "...", "source_path": "...", "source_type": "command|skill", "target_path": "..."}],
    "missing": [/* 同 stale */],
    "orphan":  [{"name": "...", "target_path": "..."}]
  },
  "missing_template": [{"rel": "...", "source_path": "...", "target_path": "..."}],
  "missing_section":  [{"rel": "...", "header": "## ..."}],
  "claude_agents": {
    "present": true,
    "first_line_placeholder": false,
    "unexpected_diffs": [{"line": N, "CLAUDE": "...", "AGENTS": "..."}]
  }
}
```

**`agents_sync.skipped == true`** = 项目里没 `.agents/skills/` 目录，跳过镜像检查（消费项目可以不要镜像）。

**重要**：本步**不允许 skill body 重新写检测规则** —— 不写自己的 grep / Python 比对、不加 filter / 排除。若发现某 case 检测不准、漏报或误报，**改脚本而不是 skill body**。这是 `ai_context/decisions.md` §Skill Implementation #5 的 hard 约束。

## Step 2: 报告 + 询问 + 自动修

**2.1 汇总打印**

按脚本 JSON 输出转成自然语言报告：

```
Plugin: <name> v<version>

.agents/skills/:    STALE=<P> | MISSING=<Q> | ORPHAN=<R>   <or "skipped (not present)">
  STALE   (P): <name list>
  MISSING (Q): <name list>
  ORPHAN  (R): <name list>

模板:
  MISSING_TEMPLATE (S): <rel-path list>
  MISSING_SECTION  (T): <"<rel>: <header>" list>

CLAUDE.md / AGENTS.md:
  first_line_placeholder: <true/false>
  unexpected_diffs (U):   <line summaries>
```

`total_drift = P + Q + R + S + T + U`。

`total_drift == 0` → 打印 `✅ Project is in sync with <name> v<version>; nothing to do.` 并退出。

**2.2 询问（单题汇总）**

`total_drift ≥ 1` → 用 **<问询工具>** 问**一题**，展示全部 finding + 每类的执行动作：

```
发现 <total_drift> 处 drift（plugin: <name> v<version>）：

.agents/skills/:
  STALE   (P): <names>   → 脚本将用 expected_mirror_content() 重新生成
  MISSING (Q): <names>   → 脚本将生成
  ORPHAN  (R): <names>   → 脚本将 rm -rf .agents/skills/<name>/   ⚠️ 删除

模板:
  MISSING_TEMPLATE (S): <paths>   → 脚本将从 templates/project-skeleton/ cp
  MISSING_SECTION  (T): <list>    → 脚本将 append `## <header>` + _(TODO)_ 标记

CLAUDE.md / AGENTS.md:
  <findings>   → 永不自动 merge（仅显示，需手工处理）

[Auto-fix all] / [Skip all]
```

选项：

- **`Auto-fix all`**（推荐）：
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/holo_update_check.py" --fix --json
  ```
  CLAUDE/AGENTS findings 不在 `--fix` 的处理范围（脚本设计上跳过），不会动这两个文件
- **`Skip all`**：不做任何修改

**2.3 应用 + 验证**

选 `Auto-fix all` → 调脚本 `--fix --json` 模式（注意 `--fix` 隐含先 `--check`）；输出 `fix_counts` JSON。再调一次 `--json`（无 `--fix`）做 post-fix 自检：

- `agents_sync.stale / missing / orphan` 应全为 0
- `missing_template` 应为 0
- `missing_section` 应为 0
- `claude_agents.unexpected_diffs` 可能仍 > 0（不在 `--fix` 范围）

post-fix 上述前 3 项任一 > 0 → 报告异常并停手（说明脚本实现有 bug 或权限问题，让用户决定）。

## Step 3: 总结打印

```
✅ /holo-update 完成

Plugin: <name> v<version>
.agents/skills/:    regenerated=A | created=B | deleted=C
模板:               template_copied=D | section_appended=E
CLAUDE/AGENTS:      <OK / U warnings (manual fix needed)>

下一步建议（仅当有 _(TODO)_ append 或 manual sync）：
  1. 检查 `_(TODO — added by /holo-update)_` 标记，按需填入实际内容
  2. CLAUDE.md ↔ AGENTS.md 如有 unexpected diffs 手工 sync 后跑 diff 验证
  3. `/commit` 把 sync 改动落盘
```

## 约束

- **检测 / fix 规则唯一来源** = `scripts/holo_update_check.py`；skill body 不重写
- **只动 plugin 升级带来的结构性 drift**（缺文件 / 缺 section header / 镜像 stale / 镜像 orphan）；不动用户已填的内容
- **不 `git add` / 不 commit**：跟 `/holo-init` 一致，提交由用户用 `/commit` 处理
- **CLAUDE/AGENTS 不自动 merge**：脚本 `--fix` 设计上不动这两文件，只在 check 输出报告它们
- 检测规则需调整 → 改 `scripts/holo_update_check.py`，按 `ai_context/conventions.md` §Cross-File Alignment 同步本文件的 Step 1 JSON 契约说明 + `commands/holo-init.md` Step 1.2（如 `expected_mirror_content` 签名变动）
