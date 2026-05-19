<!--
MAINTENANCE — 编辑本文件前请先阅读。
本文件是用于快速回到项目状态的索引，不是详细手册。
1. 写"是什么 / 去哪找"；链接到权威源（代码路径、docs/*.md、schema、logs）。
2. 优先删减而非新增；新增前先检查是否能并入已有条目。
3. 只描述当前设计 —— 不写"legacy / deprecated / formerly / renamed from"。
4. 不出现真实产品 / 客户 / 私有内容名称 —— 使用结构性占位符。
越短越好；把细节推到链接的源里，而不是让本文件变长。
-->

# AI 上下文

供未来 AI 会话使用的压缩 handoff 索引。每个文件都指向
权威来源，而不是重述其内容。

先读 `instructions.md` —— 它列出会话起点的阅读顺序。
仅当任务直接需要时才加载更重的层（`logs/change_logs/`、
`logs/review_reports/`、`docs/`、原始输入）。
