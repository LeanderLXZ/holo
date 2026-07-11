# 决策 —— 完整条目 <!-- holo:heading -->

<!-- holo:section start -->
长文、权威的决策日志。这里是每条决策理据的单一事实来源；
`ai_context/decisions.md` 是它的 1–2 行索引。

两层分离：

- **本文件**（`docs/decisions.md`）—— 完整条目：决策陈述、理据、
  范围边界、指向权威来源（代码路径、文档段、change log）的指针。
  只按需读取 —— 永不进入会话开始的阅读清单。
- **`ai_context/decisions.md`** —— 每条决策 1–2 行的索引，用
  `→ docs/decisions.md #N` 指回这里。

这一对保持 lockstep —— 同全局编号、同主题分节；改其一必须在同一
趟内同步改另一个（追加 / 就地替换 / 删除永远落到两个文件）。若
项目在 `ai_context/conventions.md` §Cross-File Alignment 维护行，
可把这一对登记为一行。

条目格式 —— 编号块，通常 ≤ 5 行（永不为精简牺牲准确性；原始讨论
推到 `logs/change_logs/`）：

```
N. <决策陈述>。
   <理据 —— 为什么选它而不是备选>。
   <范围边界 / 实测事实，当其承重时>。
   → <指向权威来源的指针>
```

就地替换 / 删除遵循 `ai_context/decisions.md` §格式 —— 编号永不
移动；曾实际尝试后退回的被替换方案，条目里保留半行
`（曾试 X，退回，见 log）` 痕迹。
<!-- holo:section end -->

## 段（按主题组织） <!-- holo:heading -->

<!-- holo:section start -->
与 `ai_context/decisions.md` 的节标题完全一致；一条决策的归档条目
与其索引行位于相同的节下。
<!-- holo:section end -->

_(none yet — delete this marker once content is added)_
