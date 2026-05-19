# TODO 清单 —— 归档

已完成 / 已废弃任务的精简归档。**精简**意为：标题 +
一句话总结 + 链接到对应的 `logs/change_logs/` 条目。完整细节
存于 git 历史与变更日志中，不在此处。

兄弟文件：`docs/todo_list.md`（活动队列 + 格式契约）。
活动队列中的任务完成或被废弃时移入此处 —— 精确移动规则参见
活动文件的 `## File guide → How to update entries`。

## Format

```
### [T-XXX] <title>

- **Completion form**: <commit / squash / merge / log-only>
- **Summary**: <one-line outcome>
- **Log**: <link to logs/change_logs/YYYY-MM-DD_HHMMSS_slug.md>
```

条目在各段底部追加，禁止重排。

---

## Completed

<!-- 已落地的任务。仅精简条目。 -->

## Abandoned

<!-- 完成前被放弃的任务。精简条目；对应的 change-log
     条目必须说明 WHY 该任务被放弃。 -->
