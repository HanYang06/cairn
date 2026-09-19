# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""组件声明基类：原子与组合部件。

组件是可再组合的声明节点（组合可递归）；真正的 Qt 实现在编译阶段（M1）。
专门的画布 / 大图这类走 QML 岛，同样按普通组件接。
"""

from __future__ import annotations

from ..core.node import Node


class Component(Node):
    """部件基类（原子 / 组合）。"""

    kind = "component"


__all__ = ["Component"]
