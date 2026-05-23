# Skills Config（项目实例） <!-- holo:heading -->

<!-- holo:section start -->
按需由 skill 加载，不在会话开始时默认加载。每个 `## …` 标题
必须存在 — 缺失即大声失败（段级例外在段体内自行声明；详见
`## Timezone`）。段体写 `(none)` = skill 跳过相关步骤；列出的
路径在磁盘上不存在则大声失败。

布局（Option A）：描述性 prose + 契约句留在
`<!-- holo:section start/end -->` 内（plugin canonical，
`/holo:update` 时被覆盖）；可配置 bullet / 字段值放在 sentinel
外（用户领地，smart-merge 保留）。迁移到新项目时只编辑 gap 中
的 bullet。
<!-- holo:section end -->

## Background processes <!-- holo:heading -->

<!-- holo:section start -->
供 skill 检测"本分支 / worktree 上是否有在跑的长任务？"，避免
打扰它。
<!-- holo:section end -->

- pgrep patterns:
  - `(none)`
- Process artifacts:
  - `(none)`
- Process logs:
  - `(none)`

## Protected branch prefixes <!-- holo:heading -->

<!-- holo:section start -->
供 skill 识别那些不可被自动 forward 或自动合并的分支。
<!-- holo:section end -->

- Prefixes:
  - `(none)`

## Main branch policy <!-- holo:heading -->

<!-- holo:section start -->
驱动与 main 分支相关的 skill 决策（`/go` 中的 worktree 询问、
push 默认值等）。skill 不再跨分支自动合并 —
跨分支同步是用户通过 `/forward` 显式发起的动作。
<!-- holo:section end -->

- Main branch: `main`
- Rule: _(none yet — delete this marker once content is added)_

## Do-not-commit paths <!-- holo:heading -->

<!-- holo:section start -->
在 `.gitignore` 默认之上，本项目专属、绝不可被 commit 的路径。
<!-- holo:section end -->

- `(none)`

## Source directories <!-- holo:heading -->

<!-- holo:section start -->
供复审类 skill 圈定代码级扫描范围。
<!-- holo:section end -->

- `(none)`

## Data contract directories <!-- holo:heading -->

<!-- holo:section start -->
承载数据形状契约的项目专属目录 —
JSON Schema、Protobuf、OpenAPI、Pydantic models、SQL DDL、Avro、
GraphQL schemas 等。许多项目没有专门目录（契约内联在代码里）—
保持 `(none)` 即可，相关扫描会优雅降级。
<!-- holo:section end -->

- `(none)`

## Example artifact directories <!-- holo:heading -->

<!-- holo:section start -->
供复审类 skill 圈定示例输出 / fixture 数据扫描范围。
<!-- holo:section end -->

- `(none)`

## Core component keywords <!-- holo:heading -->

<!-- holo:section start -->
供复审类 skill 定位用于对齐审计的关键架构组件。
<!-- holo:section end -->

- `(none)`

## Sensitive content placeholder rules <!-- holo:heading -->

<!-- holo:section start -->
绝不可出现在 docs / prompts / ai_context 中的真实世界内容；
必须被结构性占位符替换。
<!-- holo:section end -->

- `(none)`

## Timezone <!-- holo:heading -->

<!-- holo:section start -->
驱动时间戳生成（日志文件名、报告文件名、每周期时间戳）。本段
缺失或 command template 执行失败 → 回退到
`date '+%Y-%m-%d_%H%M%S'` 使用系统时区（契约的一部分）。
<!-- holo:section end -->

- Command template: `TZ='UTC' date '+%Y-%m-%d_%H%M%S'`

## Tmp directory <!-- holo:heading -->

<!-- holo:section start -->
smart-merge 临时工作空间，由 `## Reconcile core` SOP
（`commands/update.md`）用于翻译模板树和 Agent 1 staging。bullet
值与 `target_root`（仓根，**不是** skill CWD）拼接。本段缺失或
`(none)` → 回退到
`${TMPDIR:-/tmp}/holo-tmp-<YYYY-MM-DD>_<HHMMSS>/`。区别于
`logs/file_snapshots/`（用户可恢复的持久备份）。完整设计：
`docs/architecture/smart-merge.md`。
<!-- holo:section end -->

- Smart-merge tmp root: `./tmp/holo/`

## Language <!-- holo:heading -->

<!-- holo:section start -->
两个项目级语言轴，被每个写产物或向用户提问的 skill、以及
SessionStart banner 消费。

- `content_language` 管辖每一份书面产物（`ai_context/` / `docs/` /
  `logs/` / commits / README / skill 输出 / AI 写的代码注释）。
  代码标识符与字段名不论如何保持英文。
- `conversation_language` 管辖 AI ↔ 用户对话。`auto` = 每回合匹配
  用户最近一条消息；任何显式取值都是带单消息逃生通道的硬规则
  （"respond in `<other>`" 只影响那一回合）。
- 使用 ISO 639-1 编码（`zh` 而非 `cn`、`en` 而非 `eng`）；locale
  变体（`zh-CN`、`zh-TW`）保留。
<!-- holo:section end -->

- `content_language: zh`
- `conversation_language: auto`

## Activity sources <!-- holo:heading -->

<!-- holo:section start -->
逐源 ledger 注册表，由 `/recent-activity`、`/todo-add`、`/go`、
`/post-check`、`/full-review`、`/check-review`、`/fix`、
`/run-prompt` 消费。列出路径 + 文件名 pattern + 逐条字段名。
git commit 是隐式的，不在此处列出。
<!-- holo:section end -->

- Change logs:
  - Path: `logs/change_logs/`
  - Filename time pattern: `{YYYY-MM-DD}_{HHMMSS}_{slug}.md`
- TODO list:
  - Path: `docs/todo_list.md`
  - Per-entry updated-time field: `**Updated**`（或项目自选的
    标签；挑一个并保持一致）
- Archived TODO list:
  - Path: `docs/todo_list_archived.md`
- Review reports:
  - Path: `logs/review_reports/`
  - Filename pattern: `{YYYY-MM-DD_HHMMSS}_{model}_{slug}.md`
- Prompt sources:
  - Path: `(none)`
