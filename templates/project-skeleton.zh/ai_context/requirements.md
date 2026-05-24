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
   - 目标每条 ≤ 5 行，更长的细节推到链接的来源里（docs/<topic>.md）。
   - 不要压缩或改动与当前编辑无关的内容。
6. Sentinel 纪律（参见 CLAUDE.md §plugin 管理段）：sentinel `<!-- holo:section start/end -->` 内的内容是 plugin canonical，`/holo:update` 会覆写；项目专属新增内容写在 sentinel 之外的 gap 里。
-->
<!-- holo:section end -->

# 需求 —— 压缩索引 <!-- holo:heading -->

<!-- holo:section start -->
项目需求的压缩摘要，供快速跟进。

**权威来源**：`docs/requirements.md`（长篇正文，可能用
项目工作语言撰写）。下面的每一段用几行做摘要，并
指向那里对应的段以查阅全文。

本文件存在的目的是让会话起点无需加载长篇需求文档。
当需求发生变化时，两个文件须同步更新；该配对是
`conventions.md` §Cross-File Alignment 的其中一行。
<!-- holo:section end -->

## 格式 <!-- holo:heading -->

<!-- holo:section start -->
每条 entry 是一个编号块 —— 粗体引出语 + 2–5 行摘要（依 MAINTENANCE
规则 5）+ `→ docs/requirements.md §N` 指针；更长的细节推到指针目标。

**编号 —— 镜像 `docs/requirements.md`：**

- 条目 `N.` ≡ `docs/requirements.md §N`（1:1）。
- 只有当 `docs/requirements.md §N` 本身发生变化时，才新增 / 删除 /
  重写本文件的条目（lockstep）；不要在本文件凭空新增独立条目。
- 该 lockstep 对在 `conventions.md §Cross-File Alignment` 中登记
  （以 "Requirement statement added/changed in `docs/requirements.md`
  §N" 为 key 的那一行）。
<!-- holo:section end -->

## 段 <!-- holo:heading -->

_(none yet — delete this marker once content is added)_
