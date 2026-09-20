# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""布局组织器：纯几何组合原语。

布局只是声明节点，`kind` 标明形态；真正的排布在编译阶段（M1）交给 Qt 布局。
增长只在原子与页面——布局原语固定这几个，靠**嵌套**拼复杂结构，不再新增。
"""

from __future__ import annotations

from ..core.node import Node


class Layout(Node):
    """布局基类。"""

    kind = "layout"


class VBox(Layout):
    """纵向排列。"""

    kind = "vbox"


class HBox(Layout):
    """横向排列。"""

    kind = "hbox"


class Grid(Layout):
    """网格排列（子件带 `at` 行列）。"""

    kind = "grid"


class Split(Layout):
    """可拖分栏。"""

    kind = "split"


class Stack(Layout):
    """同位置堆叠（页面 / 视图切换）。"""

    kind = "stack"


__all__ = ["Grid", "HBox", "Layout", "Split", "Stack", "VBox"]
