<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 提交规则

- 格式：Conventional Commits，描述用**中文**：`feat(ui): …`、`fix(core): …`。
- **只有用户明确要求才 commit**；不擅自 `push`、`amend`、改 git 配置。
- 提交前顺序固定：`uv run ruff check .` → `uv run mypy src/cairn` → `uv run pytest`。
- 提交前先看 `git status` / `git diff`，只暂存本次该提交的文件，别夹带无关改动。
- 具体消息生成流程见 `git-commit` 技能（来自 `github/awesome-copilot`，MIT）。
