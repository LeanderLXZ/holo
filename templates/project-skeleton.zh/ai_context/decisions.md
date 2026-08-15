<!-- holo:section start -->
<!--
MAINTENANCE — 编辑本文件前请先阅读。
本文件是决策的索引（INDEX），不是决策本身。
1. 每条 entry 1–2 行、且总长 ≤ 200 字符：一行决策陈述 + `→ docs/decisions.md #N`。完整条目（理据 / 边界 / 指针）放在 `docs/decisions.md` 同编号下。
2. 准入判据：只记录当时确有争议的决策 —— 存在像样的备选方案、且未来可能被重新提出。显然的 / 无争议的选择不立条目。
3. 优先就地替换 / 删除而非新增；新增前先检查是否能并入已有条目。
4. 只描述当前设计 —— 不写"legacy / deprecated / formerly / renamed from"。
5. 不出现真实产品 / 客户 / 私有内容名称 —— 使用结构性占位符。
6. 本文件 + `docs/decisions.md` 是一对 lockstep —— 同编号、同主题分节；改其一必须同步改另一个（若项目在 §Cross-File Alignment 维护行，可把这一对登记为一行）。
7. Sentinel 纪律（参见 CLAUDE.md §plugin 管理段）：sentinel `<!-- holo:section start/end -->` 内的内容是 plugin canonical，`/holo:update` 会覆写；项目专属新增内容写在 sentinel 之外的 gap 里。
-->
<!-- holo:section end -->

# 关键决策 —— 索引 <!-- holo:heading -->

<!-- holo:section start -->
持久性工程决策的索引：每条决策 1–2 行 —— 决策陈述本身 + 指向
`docs/decisions.md` 完整条目的指针（同 `#N`）。本文件在每个会话
开始时被读取，因此在结构上保持轻量：陈述放这里，理据放
`docs/decisions.md`，完整讨论历史存放于
`logs/change_logs/<slug>.md`。会话开始时永不加载
`docs/decisions.md` —— 需要某条决策的"为什么"时按需查阅。
<!-- holo:section end -->

## 格式 <!-- holo:heading -->

<!-- holo:section start -->
每条 entry 是一个 1–2 行的编号块，**总长 ≤ 200 字符**（陈述 + 指针，
含空白）：

```
N. <决策陈述，一行>。
   → docs/decisions.md #N
```

只看决策陈述就应能知道"什么已有定论"；为什么放在归档条目里。
当某句理据是承重的（会改变读者的下一步动作）时，可以并入首行 ——
但边界、实测数据、历史沿革永远不放这里。

**起约束作用的是字符上限，不是行数**：一行写任意长也满足"1–2 行"，
索引于是退化回它本要替代的归档。超过 200 字符意味着超出部分属于
`docs/decisions.md` 条目 —— 在这里蒸馏，把细节挪过去。
`/holo:update` 的 `decisions_fat_format` 检查按同一个数字判定。

**准入判据：** 只在"当时存在像样的备选方案、且未来读者可能重新
提出它"时才立条目。试金石：没有这条 entry，一个不知情但有能力的
人会做出不同选择吗？不会 → 不立。

**编号 —— 全局 append-only，与 `docs/decisions.md` 共享：**

- 编号全局、不分节，且两文件完全一致：索引 `#N` ⇔ 归档 `#N`，
  要么都有、要么都没有。
- 追加前扫本文件 `max(N)`；新条 = `max + 1`。同一趟里在这里追加
  索引行、在 `docs/decisions.md` 追加完整条目。
- 永不重号已有 entry —— 下游代码 / docs / log 用 `#N` 引用。
- 永不填洞；append-only 下 gap 是正常的。
- 节内视觉顺序不是数字顺序（节按主题聚，编号按落地时间聚）。

**引用语义：** `decisions.md #N` 指索引（本文件）—— 稳定的公共
引用。`docs/decisions.md #N` 指归档条目 —— 需要专指理据或边界时
使用。

**就地替换**（决策变了，主题还相关）：在**两个文件里**都用新决策
替换 entry 内容。编号不变。前提：(a) 旧信息确认已失效；(b) 下游
引用旧决策的文件已更新。若被替换的方案曾被实际尝试后退回，在归档
条目里保留半行痕迹 —— `（曾试 X，退回，见 log）` —— 防止失败路径
被再次提出；索引行只描述当前决策。

**删除条目**（主题完全不相关了）：从**两个文件里**删掉 entry；gap
保留（永不重号填洞）。前提：(a) 信息确认已失效；(b) `grep -rn
"decisions.md #<N>" . --exclude-dir=logs` 返回 0 live 引用。若信息
已失效但 `logs/` 之外仍有 live 引用 → 询问用户决定。
<!-- holo:section end -->

## 段（按主题组织） <!-- holo:heading -->

<!-- holo:section start -->
随决策日志增长，挑选稳定的主题化标题 —— 例如
"Data Separation"、"Runtime Loading"、"Schema Bounds"。
`docs/decisions.md` 使用**相同的**节标题；一条决策的索引行和归档
条目位于相互对应的节下。同一节内的决策仍按全局（整文件）编号。
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_
