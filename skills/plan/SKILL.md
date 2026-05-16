---
name: plan
description: 锁定本轮消息为只讨论模式 — 仅在用户当前消息字面含 `/plan` 时激活，禁 Write/Edit/NotebookEdit 及一切 mutating Bash（git add/commit/push/merge/checkout/写文件/网络写），只允许只读查询（cat/grep/ls/find/git log/diff/status/head/tail），不开 plan.md/draft.md/notes.md 临时文件。作用域 = 一条消息，不跨延续；会话历史出现过 /plan 不算激活。$ARGUMENTS = 讨论主题（可选）。讨论收敛后用户自行调 /go 等写 skill 落盘。触发：/plan / 纯讨论 / 只讨论不动文件 / 分析一下方案 / 先讨论再说。
---

# /plan — 锁定为只讨论模式（仅本轮消息）

**仅在用户当前发送的这条消息中包含 `/plan` 时**生效，强制进入"只讨论
方案"模式：**禁止任何写文件 / 改动操作**，专注在会话里分析、列方案、
提问、权衡。**作用域 = 本轮一条消息**——下一条消息里若不再出现
`/plan`，默认行为立即恢复，不延续锁定状态。讨论收敛后由用户自己再用
`/go` / `/commit` / `/todo-add` 等独立 skill 落盘——本 skill 不主动触发。

## 规则

- **作用域硬约束**：只有用户在**本轮发出的消息字面**里出现 `/plan`
  才进入本模式；模式不跨消息延续。下一条用户消息没有 `/plan` →
  默认行为恢复，所有写工具解锁。会话历史里出现过 `/plan` 不算激活
- **零写**：禁用 Write / Edit / NotebookEdit
- **Bash 仅只读**：cat / grep / ls / find / git log / git diff /
  git status / wc / head / tail 等查询命令可用；**禁止** git add /
  commit / push / pull / merge / checkout / reset / rm / mv / mkdir /
  touch / 任何写文件 / 任何 mutating 命令；网络写请求（POST / PUT /
  DELETE）也禁止
- **不调用写 skill**：`/go` / `/commit` / `/todo-add` / `/post-check` /
  `/full-review` 等都可能动文件，不要主动触发
- **不开临时文件**：plan.md / draft.md / notes.md / .scratch 都不要

## 讨论时的姿态

- **范围收敛**：用户问范围 N → 答范围 N。若 N+1 顺手能解决再点一句，不主动扩到 N+2 / N+3。讨论阶段最常见的过度工程是堆"顺便"
- **不预实现**：不写完整 pseudocode / 整段函数草案。需要示意时最多写 1-2 行签名或 1 个数据结构骨架
- **简单优先 + 主动 push back**：发现"按用户提议做最简，X / Y 加进来反而复杂"时，主动说"建议不做 X" + 一句理由；不要默认接受用户的所有 framing
- **显式标注不确定性**：哪些是已读到的事实（行号 / 引用）、哪些是猜的、哪些得 grep / Read 才能下判断——分开说，让用户能逐条挑战
- **不清楚就停**：发现关键前提歧义 / 缺信息 → 直接问一句而不是硬猜；猜测推回多轮成本远高于一句澄清
