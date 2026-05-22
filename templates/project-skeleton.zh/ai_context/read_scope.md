<!-- holo:section start -->
<!--
MAINTENANCE — 编辑本文件前请先阅读。
稳定的项目元规则。保持精简；仅在规则本身变化时更新。
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
