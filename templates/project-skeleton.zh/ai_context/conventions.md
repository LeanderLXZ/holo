<!-- holo:section start -->
<!--
维护说明 — 编辑本文件前请先阅读。
本文件是用于快速项目跟进的索引，不是详细手册。
1. 写"是什么 / 在哪找"；链向权威来源（代码路径、docs/*.md、schema、日志）。
2. 优先删除而非新增；新条目加入前先检查是否能合并进已有条目。
3. 只描述当前设计 — 不写 "legacy / deprecated / formerly / renamed from"。
4. 不出现真实产品 / 客户 / 私有内容名称 — 使用结构性占位符。
5. 精简要求：
   - 越短越好。每条都是总结，不是细节堆叠。
   - 精简的同时也要保证信息的准确性和有效性，不要为了精简而漏掉重要信息。
   - 目标每条 ≤ 5 行，更长的细节推到链接的来源里（docs/<topic>.md）。
   - 不要压缩或改动与当前编辑无关的内容。
6. Sentinel 纪律（参见 CLAUDE.md §plugin 管理段）：sentinel `<!-- holo:section start/end -->` 内的内容是 plugin canonical，`/holo:update` 会覆写；项目专属新增内容写在 sentinel 之外的 gap 里。
-->
<!-- holo:section end -->

# 操作规范 <!-- holo:heading -->

<!-- holo:section start -->
长会话中容易忘记的规则。Dilution self-check 触发条目放在
`CLAUDE.md` / `AGENTS.md`。
<!-- holo:section end -->

## Logging <!-- holo:heading -->

<!-- holo:section start -->
`logs/change_logs/` 对每次改动写一条活动日志，按文件头中的 `Type`
字段分两种形态：

- **`Type: GO`** — 由 `/go` 拥有；三时间点契约（PRE / POST /
  REVIEW），一个日志文件覆盖一次完整改动的生命周期。
- **`Type: DO`** — 由 `/do` 拥有；面向无需 PRE 阶段的快速修改，
  事后单段日志，不含 REVIEW。

通用：

- 文件名：`YYYY-MM-DD_HHMMSS_slug.md`（HHMMSS 必填；使用
  `skills_config.md` §Timezone 中的时区命令）。
- 头部携带 `Type` + `Status` 字段（确切 token 集见对应 skill 定义）。

`Type: GO` 规则：

- **PRE** — 背景 / 决策 / 计划动作清单 / 验证标准，在任何文件改动
  之前写好。
- **POST** — 已落地变更 / 与计划的差异 / 验证结果 /
  DONE|BLOCKED，在 commit 之前写好。
- **REVIEW** — 复审摘要 + REVIEWED-PASS|PARTIAL|FAIL，在 post-merge
  复审之后写。
- 无 PRE 日志 → 不准开始改文件。

`Type: DO` 规则：

- 单段日志，改动落地后、可选 commit 之前写。子段：`## Motivation` /
  `## Change list` / `## Verification summary` /
  `## Execution deviations`。
- 不要求 PRE（这是上面"无 PRE → 无改动"规则的显式例外）；纪律
  转移到用户在调用 `/do` 前先口头交代要改的范围。
- `/do` 不允许中途升级到 `/go`；改动面超出 `/do` 范畴
  （≥ 3 个文件 / 需要跨文件对齐）时，退出并改用 `/go` 重跑。

早于本约定的旧式单时间点日志保持原样；不要回溯改写或回填
`Type` 字段。

当项目使用内置的 `/go` / `/do` / `/post-check` 时，这三个 skill
拥有确切的日志格式；以它们的定义为准。
<!-- holo:section end -->

## Cross-File Alignment <!-- holo:heading -->

<!-- holo:section start -->
当一个概念发生变化，更新其所在行的每个文件。表格初始为空；每次
发现一个必须随上游改动同步变化的下游文件，就增加一行。表格单元
只列 lockstep 文件 —— 是逗号分隔的文件清单（必要时带 anchor），不
是 inline how-to；实现细节归目标文件自己的 maintenance comment。

下方表格的形状（仅表头 —— 用户在下方 gap 内补行）：

| Changed | Also update |
|---------|-------------|

任何改动之后，grep 旧措辞以捕获残留引用。
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_

## Single Source of Truth <!-- holo:heading -->

<!-- holo:section start -->
当同一个值（一个数值边界、一个路径前缀、一个 enum、一个 regex
模式）出现在多个地方时，把它写在**一个权威位置**，让其余每处都
引用或派生自该处。按项目类型常见的权威位置：

- **Schema**（`*.schema.json`、Pydantic、Protobuf、SQL DDL）用于
  数据形状边界：`maxLength`、`maxItems`、`required`、enum 值。
- **Config 文件**（TOML / YAML / `.env`）用于运行时常量。
- **代码常量**用于共享行为阈值。

反例：在 prompt 模板里硬编码 "150–200 chars" 散文，同时在 schema
里写 `maxLength: 200`。两者会静默漂移 — 有人改了一处，忘了另一处，
不一致几个月后才以令人困惑的 bug 形式浮出。

当重复无法机械消除时（例如文档里的散文示例），把这条关联作为一行
记录到 §Cross-File Alignment，让镜像更新成为清单项，而不是依赖
记忆。
<!-- holo:section end -->

## Identifier Renames <!-- holo:heading -->

<!-- holo:section start -->
跨仓重命名标识符时，单一字面量 grep **不够** — 标识符会渗透进多
种语法形态。声明"无残留"之前，跑完全部四种扫描：

1. **字面量名称** — 项目使用的每种命名形式中的旧名
   （`old_name`、`OldName`、`OLD_NAME`）。
2. **模式内引用** — regex 字符串、schema `pattern` 字段、glob 模式、
   路由路径，或任何硬编码旧名或其前缀的字符串。零填充的数字 ID
   常藏在像 `"^\\d{4}$"` 这样的 regex 里。
3. **格式化字符串模板** — `f"...{var:fmt}..."`（Python）、模板字面量
   （JS）、`printf` / `format!`（Rust）。用**通用的** regex 抓取
   任何变量名绑定（例如 `\{[a-z_]+:04d\}` 抓零填充整数）— 千万
   不要用特定变量名。否则使用不同变量名的同类代码会静默漏掉。
4. **散文 / 示例提及** — 文档、README、ai_context 条目、commit 消息
   示例中在正文里引用旧名的地方。

将历史冻结目录从扫描中排除：`logs/change_logs/`、
`logs/review_reports/`、已归档 todo、git 历史本身。

规划重命名时把这四种扫描编入 PRE 日志的验证标准段，便于改动后
复审独立校验每一种。
<!-- holo:section end -->

## Generic Placeholders <!-- holo:heading -->

<!-- holo:section start -->
权威文档（本目录、`docs/`、schema、prompt）在语气上保持
项目无关：

- 不出现真实客户 / 产品 / 私有内容名称。
- 示例使用结构性占位符。
- 不写历史叙事（"legacy"、"deprecated"、"formerly"、
  "renamed from"）— 只描述当前设计。

例外（历史本身就是重点）：`logs/change_logs/`、
`logs/review_reports/`、归档 todo、本文件的 `decisions.md`
同伴、git commit 消息。
<!-- holo:section end -->

## Naming and Identifiers <!-- holo:heading -->

_(none yet — delete this marker once content is added)_

## Data Separation <!-- holo:heading -->

_(none yet — delete this marker once content is added)_

## Git <!-- holo:heading -->

_(none yet — delete this marker once content is added)_

## Post-Change Checklist <!-- holo:heading -->

<!-- holo:section start -->
1. 所有对齐文件都更新了吗？（上方 Cross-File Alignment 表）
2. 改动之前写了 PRE 日志、commit 之前写了 POST 日志吗？
3. `ai_context/` 仅在改动具有持久性时才更新了吗？
4. grep 过对旧名 / 旧路径 / 旧值的残留引用吗？
   （标识符重命名请使用 §Identifier Renames 的四种扫描。）
5. 如果代码或 schema 改了，跑了 smoke test 或类型检查吗？
<!-- holo:section end -->
