<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# AGENTS.md

Cairn（巨石堆）：本地优先的加密对象池 / 笔记·资产·项目工作台。
Python 3.13 + PySide6 **Qt Quick / QML**；用 `uv` 管理；Apache-2.0。

## 开工前 SOP（每个任务都先做）

1. **先看规则**：判断当前任务命中哪条规则，只读相关的那条；没有命中的规则就跳过。
2. **再看记忆**：读与本次任务相关的项目记忆（变更 / 决策 / 进度 / TODO），摸清现状。
3. **再动手**。

细则都在 `.agents/skills/`；本文件只做**索引与红线**，不要把长规则堆在这里。

## 常用命令

```powershell
uv sync                                   # 安装/同步依赖
uv run cairn                              # 启动桌面应用
uv run cairn --watch                      # 开发：QML 热重载
uv run cairn --smoke                      # 冒烟：0.8s 后自动退出

uv run pytest                             # 全部测试
uv run pytest tests/core/test_vault.py::test_load_unlock   # 单个测试
uv run ruff check .                       # lint（--fix 自动修）
uv run mypy src/cairn                     # 类型检查

# 离屏渲染 QML 为 PNG（设计评审用），默认写 build/ui_preview.png
uv run python tools/preview_qml.py Shell.qml build/x.png 1440 900 navMode=projects
```

提交前顺序：`ruff -> mypy -> pytest`。**只有用户明确要求才 commit。**

## 硬性约定

- 每个源文件/文档顶部必须有 SPDX 头：`SPDX-FileCopyrightText: 2026 HanYang06`
  + `SPDX-License-Identifier: Apache-2.0`（`.py` 用 `#`，`.md` 用 `<!-- -->`）。
- Apache-2.0 项目：**禁止引入 GPL/AGPL 依赖**（传染红线）；第三方主题/画布库先核实许可。
- 文档、注释、commit message 用中文；commit 用 Conventional Commits（`feat(ui): …`、`fix(core): …`）。
- 不写 C++。Rust（PyO3 + maturin）仅在性能热点被证实后启用。
- 未实现的设计标为「预留/草案」，不要假装已存在。

## 架构分层（别越界）

- `src/cairn/core/`（L0 加密对象池）是公共底座：**必须 Qt-free、传输无关**。
- `src/cairn/domains/`（L3 note/asset/project/relation/composition）只依赖 core 公共 API；
  领域之间互不依赖；**不得给 Manifest 加字段**，扩展只走 `meta.props`；
  `type` 命名空间为 `cairn.<domain>.<kind>`。
- `src/cairn/ui/`：`backend.py` 只做「内核 ↔ Qt」翻译，不放业务规则/界面；
  `qml/` 是界面，`theme/` 是令牌 + QSS。
- `src/comm/`、`src/server/` 是 P2P / 服务端**实验顶层包**，不在 hatch wheel 中
  （仅靠 pytest 的 `pythonpath=["src"]` 可导入）。新内核代码放 `src/cairn`。
- `docs/architecture/*.md` 是设计事实来源（`storage.md` 为 L0 唯一事实来源），
  状态均为「草案」，部分未实现。**有冲突以代码为准，改实现后回写文档。**
- 内部时间统一 unix 毫秒 int；ID 用 ULID（Oid）/ keyed BLAKE3 hex（Cid）。

## 测试与 Qt 冒烟

- pytest：`testpaths=["tests"]`、`pythonpath=["src"]`，无需安装即可 `import cairn`。
- UI 冒烟是子进程启动 Qt，离屏需 `QT_QPA_PLATFORM=offscreen` 且
  `QSG_RHI_BACKEND=software`；预览脚本可用 `CAIRN_PREVIEW_OFFSCREEN=1`。
- 测试无外部服务/数据库，全部用临时本地库。
- `src/cairn/ui/backend.py` 有 ruff per-file 豁免（`N802/N815/B008`）：
  该文件遵守 Qt 驼峰命名，勿按 Python 风格「修正」。

## 环境与坑

- **README 过时**：写的是 "Qt Widgets"，实际是 Qt Quick / QML。
- 开发库默认 `<repo>/vault/`（已 gitignore），可用 `CAIRN_VAULT` 覆盖；
  口令 `CAIRN_DEV_PASSPHRASE`（默认 `cairn-dev`）。
- Python 3.13；`uv.lock` + 阿里云 PyPI 镜像（`pyproject.toml` 的 `[[tool.uv.index]]`）。
- 图片走 Git LFS（`.gitattributes`）；未装 LFS 时 clone 到的 png 只是指针。

## 规则 / 记忆 / Skills（`.agents/skills/`）

- 技能统一放 `.agents/skills/<name>/SKILL.md`（跨工具目录：opencode、Codex、
  GitHub Copilot、Zed 等均读；opencode 全局版才用 `~/.config/opencode/skills/`）。
- 用 CLI 管理（skills.sh）：`npx skills add <owner/repo> --skill <name> -a opencode --copy -y`
  / `npx skills find <词>` / `npx skills update`。第三方技能保持上游原样，
  来源记在 `skills-lock.json`。
- 索引分工：
  - `rules` —— **规则总入口**，按场景分发到自己的 `references/`。规则只写这里。
  - `memory` —— **项目记忆本体**（可变、活文件）：变更 / 决策 / 进度 / TODO。
  - `git-commit` —— 提交规范（Conventional Commits）；来自 `github/awesome-copilot`（MIT）。
  - `skill-creator` —— 写 / 改 skill；来自 `anthropics/skills`（Apache-2.0）。
- 现状：`rules`、`memory` 为自建骨架（备注待补）；`git-commit`、`skill-creator` 为第三方安装。
- **改完 skill 必须重启 opencode 才生效。**

### 记忆的清理机制（硬性）

- `memory` 会过期失真：每条记忆标注**日期 + 状态**（进行中 / 已定 / 已废弃）。
- 每次任务收尾顺手清理：**过期、已废弃、与代码或文档不符**的记忆要删除或改写——
  只增不减会烂掉。
- 冲突时以代码与 `docs/architecture/*.md` 为准，记忆服从事实。
