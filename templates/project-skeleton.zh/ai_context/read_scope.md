<!-- holo:section start -->
<!--
MAINTENANCE — 编辑本文件前请先阅读。
本文件是用于快速回到项目状态的索引，不是详细手册。
1. 写"是什么 / 去哪找"；链接到权威源（代码路径、docs/*.md、schema、logs）。
2. 优先删减而非新增；新增前先检查是否能并入已有条目。
3. 只描述当前设计 —— 不写"legacy / deprecated / formerly / renamed from"。
4. 不出现真实产品 / 客户 / 私有内容名称 —— 使用结构性占位符。
5. 精简要求：
   - 越短越好。每条都是总结，不是细节堆叠。
   - 精简的同时也要保证信息的准确性和有效性，不要为了精简而漏掉重要信息。
   - 目标 ≤ 5 行，更长的细节推到链接的来源里（docs/<topic>.md）。
   - 不要压缩或改动与当前编辑无关的内容。
-->
<!-- holo:section end -->

# 阅读范围 <!-- holo:heading -->

<!-- holo:section start -->
告诉未来的 AI 会话默认先读什么、默认跳过什么、何时读得更深。
作为 `ai_context/` 读取顺序的一部分，在会话开始时加载进上下文。
<!-- holo:section end -->

## 默认优先级 <!-- holo:heading -->

<!-- holo:section start -->
启动会话时优先读：

- `ai_context/`
- <在此随项目演进追加专属的"小而高信号"目录 —— 例如
  `docs/architecture/` 索引、顶层 `README.md`>
<!-- holo:section end -->

## 默认不读 <!-- holo:heading -->

<!-- holo:section start -->
大型或以写为主的目录 —— 仅当任务明确要求时才加载：

- `logs/change_logs/` —— 完整历史
- `logs/review_reports/` —— 过往审计快照
<!-- holo:section end -->

## 何时深入阅读 <!-- holo:heading -->

<!-- holo:section start -->
- 用户明确要求
- 任务依赖来自更重源的特定证据
- `ai_context/` 中的压缩上下文不足以回答当前问题
- 某个冲突需要 provenance 校验
<!-- holo:section end -->

## 实用规则 <!-- holo:heading -->

<!-- holo:section start -->
优先做定向读取：具体文件、最小摘录、先看摘要。避免扫描整个大目录、
加载全部会话历史、读取全部 logs，或将源内容大段粘进回答。
<!-- holo:section end -->
