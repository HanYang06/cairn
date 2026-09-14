<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Cairn · 巨石堆

> 本地优先的个人知识 / 资产 / 项目工作台。

一块块往上堆。

## 定位

- **本地优先**：文件是本体，应用只是消费者。数据以普通文件落盘，SQLite 只是可重建的索引。
- **三件套**：笔记、存储、项目管理。
- **桌面优先**：以 Windows 为主要平台，内核与打包保持跨平台能力。
- **加密对象池**：内容寻址 + 加密存储，是与其他笔记软件的根本分野。

## 现状

早期开发阶段，**尚未发布**。加密对象池（L0）与 QML 界面外壳已可运行，领域功能在逐步接入。
详细进度、决策与待办见 `.agents/skills/memory/references/`。

## 快速开始

需要 **Python 3.13** 与 [`uv`](https://docs.astral.sh/uv/)：

```powershell
uv sync                    # 安装/同步依赖
uv run cairn               # 启动桌面应用
uv run cairn --watch       # 开发：QML 热重载
uv run cairn --smoke       # 冒烟：0.8s 后自动退出
```

- 开发库默认放在 `<repo>/vault/`（已 gitignore），可用环境变量 `CAIRN_VAULT` 覆盖。
- 开发口令为环境变量 `CAIRN_DEV_PASSPHRASE`（默认 `cairn-dev`）；**正式解锁流程尚未实现**。

## 技术栈

- **语言**：Python 3.13。
- **界面**：PySide6 **Qt Quick / QML**（不是 Qt Widgets）。
- **环境与构建**：`uv`（`uv.lock`）+ hatchling；PyPI 走阿里云镜像（见 `pyproject.toml`）。
- **原生扩展**：预留 Rust（PyO3 + maturin），仅在性能热点被证实后启用；**不写 C++**。
- **许可**：Apache-2.0，**禁止引入 GPL/AGPL 依赖**。

## 架构

| 目录 | 职责 |
|---|---|
| `src/cairn/core/` | L0 加密对象池，公共底座；**Qt-free、传输无关** |
| `src/cairn/domains/` | 领域对象（note / asset / project / relation / composition） |
| `src/cairn/ui/` | `backend.py` 做「内核 ↔ Qt」翻译；`qml/` 界面与主题令牌 |
| `src/comm/`、`src/server/` | P2P / 服务端**实验顶层包**，不在 wheel 中 |

设计事实来源见 `docs/architecture/*.md`（`storage.md` 为 L0 唯一事实来源）；**有冲突以代码为准**。

## 开发

```powershell
uv run pytest                 # 全部测试（无需外部服务，全部用临时本地库）
uv run ruff check .           # lint（--fix 自动修）
uv run mypy src/cairn         # 类型检查

# 离屏渲染 QML 为 PNG（设计评审用）
uv run python tools/preview_qml.py Shell.qml build/x.png 1440 900
```

提交前顺序：`ruff -> mypy -> pytest`。

### 打包（Windows）

```powershell
uv run python tools/build.py               # 绿色包 -> dist/cairn/
uv run python tools/build.py --clean       # 先清 build/ 与 dist/
uv run python tools/build.py --installer   # 再出安装包（需已装 Inno Setup）
```

- PyInstaller 配置：`packaging/cairn.spec`；安装包脚本：`packaging/windows/cairn.iss`。
- 产物：`dist/cairn/`（免安装 zip）、`dist/installer/Cairn-<ver>-win-x64-setup.exe`。
- CI：`.github/workflows/build-windows.yml`（打 `v*` tag 或手动触发）。

## 平台与分发（规划）

内核跨平台，但打包按需投入，当前优先级：

| 平台 / 形态 | 载体 | 优先级 |
|---|---|---|
| 源码 | sdist + wheel | P0 |
| **Windows** 桌面 | 安装包（Inno Setup）+ 免安装 zip | **P0** |
| Linux 服务端 / CLI | 控制台入口 + Docker | P1（待 `src/server` 成熟） |
| Linux 桌面 | AppImage | P2 |
| macOS 桌面 | `.dmg` + 公证 | 暂缓 |

Windows 打包脚本已就绪（见「开发 · 打包」）：**PyInstaller（`--onedir`）+ Inno Setup**，出免安装 zip 与安装包。
代码签名留待发布前补齐；其余平台为规划。

## 北极星

可选择性联邦进一个 P2P 博客网络（服务器可选、公私自决、可发现可私网）。网络是增强层，不是本体。

## 许可

Copyright 2026 HanYang06。本项目基于 [Apache License 2.0](LICENSE) 授权。
分发时请一并保留 [`LICENSE`](LICENSE) 与 [`NOTICE`](NOTICE)。
