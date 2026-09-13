---
name: memory
description: "Cairn 项目记忆（变更 / 决策 / 进度 / TODO）。任务开始前或改动代码前，读相关记忆了解现状；任务收尾时更新记忆，并清理过期、已废弃、与代码不符的条目。"
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Cairn 项目记忆

**这个技能本身就是项目的记忆**（可变、活文件）。内容按类别放在 `references/`：

| 类别 | 文件 |
|---|---|
| 决策（已定方向及理由） | [`references/decisions.md`](references/decisions.md) |
| 变更（重要改动记录） | [`references/changes.md`](references/changes.md) |
| 进度 / TODO | [`references/progress.md`](references/progress.md) |

## 怎么读

- 任务开始时，只读与当前任务**相关**的条目，不必全读。
- 记忆只是现状快照；与代码或 `docs/architecture/*.md` 冲突时，**服从事实**。

## 怎么写（格式）

每条标明**日期 + 状态**：

```
- 2026-09-14 · 已定 · <内容> | <理由>
```

状态取值：`进行中` / `已定` / `已废弃`。

## 清理机制（硬性）

- 每次任务收尾**顺手清理**：过期、已废弃、与代码或文档不符的条目 → 删除或改写。
- 只增不减会烂掉；记忆必须比代码更短、更新更快。
- 已在代码或架构文档中固化的事实，不要再在记忆里重复。
