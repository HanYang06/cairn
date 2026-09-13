<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 许可规则（红线）

- 本项目 Apache-2.0：**禁止引入 GPL/AGPL 依赖**（会传染）；宁可少一个功能也别踩。
- 第三方主题 / 画布 / 编辑器库先核实许可证再采用（候选项与结论见 `docs/architecture/ui-theme.md`）。
- 新增第三方 skill：保持上游原样；来源与 hash 记入 `skills-lock.json`，需要时同步 `NOTICE`。
- 新增运行期依赖后复核 `NOTICE` / `pyproject.toml` 的许可声明。
