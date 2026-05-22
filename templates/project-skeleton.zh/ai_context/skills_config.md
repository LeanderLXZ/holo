# Skills Config（项目实例） <!-- holo:heading -->

<!-- holo:section start -->
按需由需要项目专属锚点的 skill 加载。**不**在会话开始时默认加载 —
只有需要它的具体 skill 才会读取。

下方每个段都有固定标题。**段标题（`## …` 行）默认必须存在** —
缺失任一标题意味着配置结构不完整；skill 会大声失败并停手。例外由
段体自行声明（当前仅 `## Timezone` 在段体内声明了系统时区 `date`
回退；详见该段）。若本项目对某段没有取值，请在段体内写 `(none)`，
skill 会跳过相关步骤。若某段列出了具体路径但这些路径在磁盘上不存
在，skill 会大声失败并报告漂移。

**段内布局（Option A）**：每个段把纯描述性 prose + 契约段
留在 `<!-- holo:section start/end -->` 块内（plugin canonical；
升级时被 smart-merge 覆盖），并把可配置 bullet / 字段值 /
逐源块挪到 sentinel 外的 gap 区域（用户领地；smart-merge 完整
保留）。迁移到新项目时只编辑 gap 中的 bullet；skill body 保持
不动。
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
驱动各 skill 的时间戳生成（日志文件名、报告文件名、每周期
时间戳）。

Fallback: 若本段缺失或 command template 执行失败，skill 回退到
`date '+%Y-%m-%d_%H%M%S'`，使用系统时区。该回退是契约的一部分
（见文件顶部规则）—— skill 无需为时间戳生成自行编写
`try / except`。
<!-- holo:section end -->

- Command template: `TZ='UTC' date '+%Y-%m-%d_%H%M%S'`

## Language <!-- holo:heading -->

<!-- holo:section start -->
两个项目级语言轴，被每个写产物或向用户提问的 skill、以及
SessionStart hook banner 消费。

Notes:

- `content_language` 管辖 AI 在本项目中产出或维护的每一份书面
  产物：`ai_context/` / `docs/` / `logs/` /
  commit messages / README / skill 控制台输出 / 错误消息 /
  AI 写的代码注释。代码标识符与字段名不论如何都保持英文。
  接受任意 ISO 639-1 编码。
- `conversation_language` 管辖 AI ↔ 用户对话回合
  （`AskUserQuestion` prompt、自由形式回复、确认）。接受
  `auto | <ISO 639-1>`。`auto` = 每回合匹配用户最近一条消息的
  语言。任何显式取值都是带单消息逃生通道的硬规则（用户说
  "respond in `<other>`" → 该回合用 `<other>` 回复，下一回合
  回到配置）。
- 语言编码遵循 ISO 639-1（`zh`，不是国家代码 `cn`；
  `en`，不是 `eng`）。Locale 变体（`zh-CN`、`zh-TW`）保留给
  未来的区域细分。
- 下方默认值（`zh` / `auto`）是模板起点；现在就编辑为本项目
  偏好值，或让 `/holo:init` 在项目初始化时交互式设定它们。
<!-- holo:section end -->

- `content_language: zh`
- `conversation_language: auto`

## Activity sources <!-- holo:heading -->

<!-- holo:section start -->
逐源注册表，由 `/recent-activity`、`/todo-add`、`/go`、
`/post-check`、`/full-review`、`/check-review`、`/run-prompt` 消费。
列出 workflow skill 触及的每个 ledger 的路径 + 文件名 pattern +
逐条字段名。git commit 是隐式的（始终可从当前 repo 取得）；下方
条目列出是为了让非默认项目布局可以覆盖。段体写 `(none)` 视为
"未配置" —— 消费该段的 skill 跳过相关扫描（按文件顶部规则优雅
跳过）。
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
