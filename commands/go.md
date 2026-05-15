---
description: 方案落盘 — 按上文讨论把 schema/代码/config/docs 改动按 11 步流程（加载配置 → 工作位置询问 → PRE log → 落实讨论到文档 → 实现 → smoke 测试 → 跨文档对齐+todo_list → 多线 review → POST log → commit → stash pop / worktree 收尾）推进到可交付状态。Step 1 询问当前分支原地 / 切分支 / worktree / WIP commit / stash 五选一；Step 10 只处理本轮残留（stash pop、worktree 询问），**不**再 fan-out 到其他分支——跨分支同步是 `/forward` 的事。Step 2 先把讨论/决策/计划/验证标准登记到 logs/change_logs/ 的 PRE 段，执行结束再回写 POST 段，作为 /post-check 的 intent 基线。用户说"落地"、"执行方案"、"go"、"把刚才讨论的改下来" 时触发。
---

# /go — 方案落盘

按上文讨论执行；某步本次 N/A 就明说"跳过 Step X"。`$ARGUMENTS` 存在即本次改动焦点。

## Progress reporting

下方流程分为 `## Step 0:` ~ `## Step 10:`。

**进入 Step 0 之前**：调用 **<进度工具>** 把 Step 0 ~ Step 10 全部预登记（每个 step 一条，`content` 用 `Step N: <子段标题>`，`status` 全为 `pending`）。这是硬性要求，**不调 <进度工具> 不许往下走**。

每进入一个 step：调 **<进度工具>** 把当前 step 改 `in_progress`（同一次调用里把上一个 step 标 `completed`），然后做实际工作。**step 跨越时不要漏调**。进度由 <进度工具> 的 UI 直接显示，**对话里不再打 `[/go] Step N: ...` 之类的进度行**。

跳过某 step：调 **<进度工具>** 把对应条目直接标 `completed`，并在对话里打一行 `Step N 跳过（理由：…）`——"理由"是 UI 缺失的信息，保留这一行；不要静默略过。

最后一步完成：调 **<进度工具>** 把最后一条标 `completed`。

**子任务（可选，按需启用）**：当某个 step 内部工作复杂、明显由多个独立小任务组成（如 Step 4 同批改 schema / prompt / code / config 多块）时，进入该 step 时可在 <进度工具> 里把 `Step N: <title>` **展开**为若干条 `Step Na: <子标题>` / `Step Nb: …` / `Step Nc: …`（用字母序，同次调用替换原 `Step N` 条目），按子任务推进切 `in_progress` / `completed`。**只展开当前正在做的 step 的子任务**——其他 step 保持单条 `Step M: <title>` 折叠形态，不展开。当前 step 的子任务全部 `completed` 后，**进入下一 step 时把这些子任务折回成一条** `Step N: <title>` `status=completed`，再展开下一 step（如有需要）。这样 UI 里始终是"当前 step 细粒度 + 其他 step 折叠粗粒度"。

简单 step 不必启用——直接按 `Step N: <title>` 切状态即可。子任务编号用同一字母序，**不要嵌套二层**（不要 `4a-1` / `4a-2`）。

**<进度工具> 解析**：Claude → `TodoWrite`（界面显示为 "Update Todos"）；Codex → `update_plan`；其他 runtime（无结构化进度工具，如 Copilot agent mode）→ 在 response 文本里维护一份 markdown checkbox 列表当 step 状态，每次状态切换前整段重写一遍。语义对齐：预登记 + 切状态 + 标完成（含子任务展开 / 折回）。

**<问询工具> 解析**：Claude → `AskUserQuestion`（每次最多 4 题，超过分批问）；其他 runtime（无结构化询问工具，如 Codex / Copilot agent mode）→ 在 response 文本里编号列出问题 + 每题的可选选项，让用户一次回答（仍按每批最多 4 题，超过分批问）。

## Step 0: 加载 skills 配置

`Read` `ai_context/skills_config.md`。

- 文件不存在 / 某节标题缺失 → fail loudly：打印缺失项 + 提示按 plugin 模板补全，停手
- 某节内容 `(none)` 或留空 → 跳过该节相关步骤（视为本项目无此项）
- 某节列了具体路径但路径不存在 → fail loudly：提示该节漂移到不存在路径，停手等用户修

后续步骤出现 "skills_config.md `## XX`" 时引用本配置。本 skill 用到：
`## Background processes`（Step 1 dirty 提问的关联进程探测）、
`## Do-not-commit paths`（Step 9 commit 前禁提路径扫描）、
`## Timezone`（Step 2 / Step 8 时间戳）、
`## Sensitive content placeholder rules`（Step 3 / Step 7）、
`## Data contract directories`（Step 5 / Step 7 数据契约扫描；含 JSON Schema / proto / OpenAPI / Pydantic / SQL DDL 等）。

## Step 1: 锁定工作位置（环境探测 + 询问驱动）
`/go` 的 git 交互契约：**Step 1 必问一次**（这里选定工作位置）；**Step 2 到 Step 9 中途一次都不问**；**Step 10** 视 Step 1 选择再决定是否问一次（worktree follow-up / stash pop 等）。`/go` 不再隐式"切到主分支再说"——是否切分支、是否启 worktree 由用户在 Step 1 显式选定。

- `git branch --show-current` 取当前分支 `<X>`；`git status --porcelain` 判工作区 clean / dirty；按 skills_config.md `## Background processes` 探测（pgrep 模式 + 进程产物路径；该节留空则跳过进程检测）。把 dirty 摘要 + 关联进程（如有）合并成一行 `<dirty 摘要 / 关联进程 P>`，作为 Dirty 提问的上下文
- **<问询工具>** 一题，按 clean / dirty 走不同选项集：

**Clean 路径**（工作区 clean 且无关联进程）：

提问："当前分支为 `<X>`。请选择 `/go` 的工作位置。"

1. **在当前分支 `<X>` 上原地执行（推荐）** — 留在 `<X>`，后续编辑 / PRE log / commit 全部落在该分支
2. **切换至指定分支后执行** — 需提供分支名；进入 worktree follow-up（见下）但用 `git checkout` 而非 `git worktree add`：本地分支存在则直接 checkout；不存在则追问 base 分支后 `git checkout -b <branch> <base>`
3. **在独立 worktree 中执行** — 需提供分支名；进入 worktree follow-up

**Dirty 路径**（工作区 dirty 或有关联进程）：

提问："当前分支为 `<X>`，工作区检测到 `<dirty 摘要 / 关联进程 P>`。请选择处理方式。"

1. **提交当前 WIP 进度后执行 `/go`（推荐）** — 复用 `/commit` Step 1–3 的扫描契约（禁提路径 + 未跟踪文件 + 大文件兜底；**不绕过** Step 2 的安全检查）做一次 WIP commit（message 默认 `wip: <X> snapshot before /go`，可由当前 `$ARGUMENTS` 重写主题），commit 完后留在 `<X>` 上继续 `/go`
2. **不处理直接执行 `/go`** — 未提交改动将随本次变更一并提交（用户自行确认这是想要的）
3. **在独立 worktree 中执行** — 需提供分支名；进入 worktree follow-up（worktree 与当前 dirty 工作区互不干扰）
4. **暂存当前改动（`git stash`）后执行 `/go`** — `git stash push -u -m "/go autostash <X>"` 后留在 `<X>`；Step 10 末尾自动 `git stash pop` 还原（见 Step 10）

**Worktree follow-up（仅 Clean 选项 3 / Dirty 选项 3）**：

再问一题："worktree 要 checkout 哪个分支？请填分支名。"

- 用户填的分支本地已存在 → `git worktree add ../<repo>-<branch> <branch>`；worktree 路径下后续编辑 / PRE log / commit 全走该 worktree
- 用户填的分支不存在 → 追问一题："分支 `<branch>` 不存在。请填 base 分支（默认 = 当前分支 `<X>`）"，得到 base 后 `git worktree add -b <branch> ../<repo>-<branch> <base>`
- worktree 路径冲突（目录已存在）→ 停手报告，让用户决定（手动清理后重跑 / 换分支名）

**切换至指定分支 follow-up（仅 Clean 选项 2）**：

同上的"分支名 → 不存在追问 base"流程，但用 `git checkout` / `git checkout -b <branch> <base>` 而不开 worktree。仅 Clean 路径出现该选项——Dirty 路径下直接切分支会污染工作区，由用户先用 Dirty 选项 1 / 4 把工作区清干净再换分支。

选定后打印一行策略声明，举例：
- `策略：当前分支 develop 原地`
- `策略：切到 feature/x 原地`
- `策略：../holo-main worktree 隔离（branch=main）`
- `策略：WIP commit 后留在 develop 原地`
- `策略：stash 后留在 develop 原地（Step 10 自动 pop）`

`git checkout` / `git worktree add` / WIP commit / `git stash` 中任一失败 → 停手报告原因，等用户决定。**Step 1 之后不再询问**，直到 Step 10 末尾。

## Step 2: PRE log 登记（先登记再动手）
**任何代码 / schema / prompt / docs / ai_context / skill 改动之前**，先创建本次改动的 log 文件并写入 PRE 段。这是 `/post-check` 的 intent 基线来源，强制。

- 文件名：`logs/change_logs/{YYYY-MM-DD}_{HHMMSS}_{slug}.md`。HHMMSS 强制，按 skills_config.md `## Timezone` 的命令模板执行（该节缺失则 fallback 到 `date '+%Y-%m-%d_%H%M%S'` 系统时区）；slug 语义化英文短名
- 回显路径给用户（一行 `LOG: logs/change_logs/...md`），便于后续 `/post-check` 显式引用

PRE 段必须包含：

```markdown
# {slug}

- **Started**: {YYYY-MM-DD HH:MM:SS} {时区缩写：按 skills_config.md `## Timezone` 的设定}
- **Branch**: {/go 进入时的工作分支}
- **Status**: PRE

## 背景 / 触发
{会话上下文、用户原始需求、上游讨论链条摘要}

## 结论与决策
{/go 进来时已拍板的方案：选了哪个方向、改什么、不改什么}

## 计划动作清单
- file: {path} → {改动要点}
- ...

## 验证标准
- [ ] {如 Import 无报错}
- [ ] {如 数据契约校验通过}
- [ ] {如 grep 残留为 0}
- ...

## 执行偏差
（执行中追加；无偏差则写"无"）
```

写完 PRE 段**再进入 Step 3**。中途发现偏离计划 → 在 log 里追加 `## 执行偏差` 段落记新决定，**不默默改**。

## Step 3: 把讨论结论落到文档（内容创作）

把会话里已拍板的方案翻译成文档语言。**这一步只做"写入"**——跨文档对齐校验留给 Step 6，全库 review 留给 Step 7；本步任何"某文件 A 写完发现文件 B 也得改"的连带感觉，**先记进 PRE log 的「执行偏差」段**，留给 Step 6 系统补齐，不要边写边四处串改。

按本次讨论触及的范围筛取（不要无脑全跑）：

- **`docs/requirements.md` + `ai_context/requirements.md`**（一对，lockstep）：本次涉及**用户可见的功能契约 / 验收标准 / 边界情况约束**变化时更新对应节
- **`docs/architecture/` + `ai_context/architecture.md`**（一对，lockstep）：本次涉及以下任一时更新对应节 —— **新模块 / 新接口 / 新状态机 / 调用关系变化 / 新分支策略 / 新工作流契约 / 新入口点**
- **`ai_context/decisions.md`**：本次产生的 durable 决策立刻落条目，不要拖到 Step 6 / Step 8；**若决策涉及上一行的触发词，必须同步在 architecture / requirements 加一节描述**（决策是 "why"，architecture / requirements 是 "what"）
- **`prompts/`**：讨论结论包含 prompt 行为契约 / 模板变化时更新
- **`README.md`**：仅当目录 / 入口 / 启动方式有变化

写作约束：

- **按 skills_config.md `## Sensitive content placeholder rules` 用占位符替换真实内容**（该节留空则跳过该项扫描）
- 描述只写当前设计，不写"旧 / legacy / 已废弃 / 原为"

## Step 4: 实现代码 / schema / prompt / 配置
按讨论改 schema、prompt template、架构代码、配置。**先确认 PRE log「验证标准」段已有 ≥ 1 条具体可执行项**（如 `import 无报错` / `grep 残留 = 0` / `smoke X 全过`；非"做对了就行"这类含糊）；含糊 → 立刻补具体的再继续。对照 `ai_context/conventions.md` 的 Cross-File Alignment 表列出连带文件（该表不存在则跳过本项，仅按本次改动直觉判断）。

## Step 5: Smoke 测试 + 数据契约校验（仅当代码 / 数据契约改动时）
Import 检查 + 关键函数 smoke test；如本次改动触及 skills_config.md `## Data contract directories` 列出的目录（schema / proto / openapi / pydantic / SQL DDL 等数据契约），按项目对应的校验工具跑一次（例：JSON Schema → `jsonschema` / `ajv`；OpenAPI → `openapi-spec-validator` / `redocly lint`；proto → `protoc --lint_out`；pydantic → 模型 import + `model_rebuild()`；SQL DDL → migration dry-run）。该节 `(none)` 时跳过本步契约校验。有错立即修。

## Step 6: 跨文档对齐 + todo_list 维护

到这里 Step 3 / 4 / 5 已分别把内容写进文档与代码。**本步只做"对齐校验 + 维护收尾"**，不做内容创作——若发现某项需要重新写一段需求 / 架构描述，回到 Step 3 重写而不是在本步硬塞。

**跨文档对齐**：

- 对照 `ai_context/conventions.md` 的 Cross-File Alignment 表（不存在则按 Step 3 / Step 4 实际触及的文件直觉判断），核对 schema / prompt / code / docs / ai_context / README 在以下维度是否一致：
  - 字段名 / 参数 / 返回值 / 状态值 / 错误码
  - 流程描述 / 状态机 / 门控时序
  - 术语 / 概念命名
- 发现某文件本应同步却没动 → **查漏补缺**式补上；改动量小（一两行同步）就地修，改动量大（要重写整段需求 / 架构描述）→ 回 Step 3 重做

**ai_context durable 维护**：

- `ai_context/current_status.md`：当前状态行是否需要更新
- `ai_context/next_steps.md`：本次产生的新方向 / 阻塞是否需要登记
- `ai_context/handoff.md`：是否需要给下一会话留一句话

**todo_list 维护**：

- `docs/todo_list.md`：本次完成的条目**整条移到 `docs/todo_list_archived.md`** 的 `## Completed` 段（瘦身：标题 + 完成形式 + 1 行摘要 + 本次 log 链接）；状态变化更新
- 任务移段 / 增改后**同步刷新顶部 `## Index` 段**（规则在 `docs/todo_list.md` 顶部"Index maintenance"小节）。`/todo` skill 只读索引，不刷新就会给出过期信息
- ⚠️ 仅维护"本次改动直接产生 / 完成"的条目；Step 7 review 期间发现的新问题**不在本步登记**，按 Step 7 的处理规则走

## Step 7: 全库多线 review（并行）

并行扫描全仓与本次改动相关 / 受牵连的文件，**至少四条线，可派 sub-agent 并行**；改动面小则单线串跑。

**四条线**（每条都先重读 PRE log 再扫描）：

1. **规范线**：`ai_context/` / `docs/` / skills_config.md `## Data contract directories` 列出的目录（`(none)` 时跳过该节扫描）/ `prompts/` —— 描述 vs. 本次改动是否一致，有无残留旧描述 / 旧字段 / 旧流程；顺查有无违反 skills_config.md `## Sensitive content placeholder rules` 的真实内容、`旧 / legacy / 已废弃 / 原为` 字样
2. **实现线**：本次改过的代码 + 其上下游（调用方 / 被调用方 / 导入方）—— 字段名 / 参数 / 返回值 / 状态机 / 门控 / 异常路径是否连贯，import 是否还能跑
3. **风险线**：本次改过的代码 + 受其牵连的相关代码（调用方 / 被调用方 / 共享状态 / 共享数据流）—— 边界条件、空值 / None、异常路径、并发、重试 / 回滚、错误处理是否藏 bug；新行为是否引入数据丢失 / 安全口子 / 性能回退；状态机 / 门控 / 不变量是否有漏覆盖分支。**与实现线区分**：实现线问"还连得上吗"（签名 / import 一致性），风险线问"做的事对吗"（语义正确性 + 失败模式）
4. **结构线**：README / 目录结构 / 已提交样例产物 / artifact 目录 是否与本次变化对齐；改了文件名 / 目录结构 → 追查所有引用点

**Findings 处理**（**重要**：本步发现的问题不要直接写进 `docs/todo_list.md`）：

- **一行能修的小问题**（错别字、漏占位符、漏一个 import、明显笔误、悬挂引用一处）→ **发现即修**，不留尾
- **大问题 / 跨范围 / 需要重新讨论 / 不在本次 intent 范围内的发现** → **不自己写进 `docs/todo_list.md`**；在对话里列一段「**建议登记到 todo_list**」清单，每条带：文件 + 行号、问题摘要、建议归到哪个分段。等用户拍板后由 `/todo-add` 或下一轮 `/go` 落条目——避免本次 intent 之外的发现污染 todo_list 历史

> **进入本步之前，自己先重读 Step 2 创建的 PRE log**——经过前几步的编辑上下文，已经离"原始 intent"有距离；以 PRE 的"结论与决策 / 计划动作清单 / 验证标准"重新校准，再开始扫描。
>
> **派出的每个 sub agent 也必须先重读同一份 PRE log**：把 `LOG:` 路径塞进它的 prompt，并**明示要求它开工前先读完该 log 的 PRE 段**再做事。sub agent 是独立 context，不强制它读 PRE 就只会按 prompt 里的 brief 空转，容易脱离本次 intent。

## Step 8: POST log 收尾
更新 **Step 2 创建的同一份 log**，追加 POST 段：

```markdown
<!-- POST 阶段填写 -->

## 已落地变更
{实际改了哪些文件、每份改了什么，文件 + 行号或 diff 摘要}

## 与计划的差异
{对比 PRE 的"计划动作清单"，新增 / 删除 / 修改了什么；无则写"无"}

## 验证结果
- [x] {PRE 验证标准 1} — {输出摘要}
- [ ] {PRE 验证标准 2} — {失败原因}
- ...

## Completed
- **Status**: DONE | BLOCKED
- **Finished**: {timestamp，按 skills_config.md `## Timezone` 的命令模板取，与 PRE Started 同时区}
```

不要新建 log 文件；就地更新 PRE 段那份。

## Step 9: Git commit
Step 1 已经把工作位置锁定（当前分支原地 / 切换后的分支 / worktree 内的分支），commit **落到 Step 1 选定的分支**。worktree 是否清理留给 Step 10——本步不动。

- `git status` 只剩本次改动；按 skills_config.md `## Do-not-commit paths` 列表 +（`.gitignore` + `ai_context/conventions.md`）兜底扫描
- message 风格对齐 `git log --oneline -10`
- **本次改动 + PRE/POST log 文件合并为单次 commit**——不再拆 `<slug>: ...` + `log(<slug>): /go PRE+POST` 两次
- 提交后 `git status` 确认干净
- **若 Step 1 走了 worktree 路径**：commit 在该 worktree 内执行；commit 完成后**不自动清理** worktree（清理由 Step 10 末尾询问）。`/go` 始终留在 Step 1 选定的工作位置（worktree / 切到的分支 / 原分支），不背着用户切回别处

## Step 10: 收尾（stash pop + worktree follow-up）

`/go` **不再 fan-out 到其他分支**——跨分支同步是 `/forward` 的事，由用户在本轮 `/go` 完成后显式调用。本步只处理 Step 1 选择遗留的状态。

按 Step 1 实际走的路径分支处理：

- **Clean 选项 1（当前分支原地）/ Clean 选项 2（切到指定分支原地）/ Dirty 选项 1（WIP commit 后原地）/ Dirty 选项 2（不处理直接执行）** → 无遗留状态，直接打印"`/go` 完成，当前在 `<branch>`，commit 已落地。后续如需同步到其他分支，请 `/forward`"，**不询问**，结束
- **Dirty 选项 4（stash 后执行）** → 在源分支 `<X>` 上自动 `git stash pop` 还原工作区。pop 失败（冲突 / stash 丢失）→ 停手报告，让用户决定；成功则打印一行 `stash 已 pop 还原`，**不询问**，结束
- **Clean 选项 3 / Dirty 选项 3（worktree 路径）** → 用 **<问询工具>** 问一次："`/go` 已完成，本次 commit 已落到 `<branch>`。worktree `../<path>` 如何处理？"
  1. **保留 worktree（推荐——便于后续在该分支继续工作）** — 不动 worktree；打印当前 worktree 路径供用户下次使用
  2. **立即清理（`git worktree remove`）** — 在源仓库根目录执行 `git worktree remove ../<path>`；commit 已落到分支 ref，worktree 目录删除不丢数据。`git worktree remove` 因脏文件失败 → 停手报告，让用户决定（不自动加 `--force`）

打印一行最终状态：`/go` 完成，当前 HEAD = `<branch>`；worktree 处理结果（保留 / 清理）。**不切回任何"主分支"**——`/go` 始终尊重 Step 1 选定的工作位置，把"我现在在哪个分支" 的决定权留给用户。
