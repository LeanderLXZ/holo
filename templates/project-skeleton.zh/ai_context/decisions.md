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

# 关键决策 —— 压缩版 ADR <!-- holo:heading -->

<!-- holo:section start -->
持久性工程决策的压缩日志。每条决策一个条目：一行决策正文 +
一行理据 + 一个指向权威来源（代码路径、文档段、日志文件）的指针。
entry 只记 "决策了什么 + 一句话为什么"；完整讨论历史存放于
`logs/change_logs/<slug>.md`，不在这里。本文件是索引，不是讨论
本身。
<!-- holo:section end -->

## 格式 <!-- holo:heading -->

<!-- holo:section start -->
每条 entry 是一个编号块，总体 ≤ 5 行，典型形式：

```
N. <决策陈述>。
   <理据>。
   → <指向权威来源的指针>
```

精简不应牺牲信息的准确性或完整性 —— 不要为了精简而漏掉重要信息。

**编号 —— 整文件全局 append-only：**

- 编号是全局的，不分节。
- 追加前扫整文件 `max(N)`；新条 = `max + 1`。
- 永不重号已有 entry —— 下游代码 / docs / log 用 `#N` 引用。
- 永不填洞；append-only 下 gap 是正常的。
- 节内视觉顺序不是数字顺序（节按主题聚，编号按落地时间聚）。

**示例。** 文件当前末尾是 `18. Section version sentinel ...`。
新增：`grep -E '^[0-9]+\. ' decisions.md`，取 `max(N) = 18`，把
`19. <决策>...` 写到目标主题节末尾 —— 哪怕那个节最后可见编号是 `#15`
而不是 `#18`。

**就地替换**（决策变了，主题还相关）：用新决策替换 entry 的
内容。编号不变。前提：(a) 旧信息确认已失效；(b) 下游引用旧决策的
文件已更新到新决策。

**删除条目**（主题完全不相关了）：删掉 entry；gap 保留（永不重号
填洞）。前提：(a) 信息确认已失效；(b) `grep -rn "decisions.md #<N>"
. --exclude-dir=logs` 返回 0 live 引用。若信息已失效但 `logs/` 之外
仍有 live 引用 → 询问用户决定。
<!-- holo:section end -->

## 段（按主题组织） <!-- holo:heading -->

<!-- holo:section start -->
随决策日志增长，挑选稳定的主题化标题 —— 例如
"Data Separation"、"Runtime Loading"、"Schema Bounds"。
同一章节内的决策仍按全局（整文件）编号。
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_
