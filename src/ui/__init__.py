# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 内核（重建中）。

目录：
    core      与通信主干的接入点（`Session` / `App`，Qt-free）
    layout    布局组织器（纯几何）
    page      页面层（导航目标）
    component 组件层（原子 / 组合）
    qml       QML 岛

设计见 `docs/architecture/ui-kernel.md`。
"""

from __future__ import annotations

__all__: list[str] = []
