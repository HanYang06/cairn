<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# SPDX 头规则

- 每个源文件 / 文档顶部必须有：
  - `SPDX-FileCopyrightText: 2026 HanYang06`
  - `SPDX-License-Identifier: Apache-2.0`
- 写法：`.py` 用 `#`，`.md` 用 `<!-- -->`。
- `SKILL.md` 例外：YAML frontmatter 必须在最顶部，故 SPDX 注释紧随 frontmatter 之后，
  并同时在 frontmatter 写 `license: Apache-2.0`。
- 第三方 vendored 文件（如 `.agents/skills/skill-creator/`）保持上游原样，不强行加 SPDX。
