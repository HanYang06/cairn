# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""页面：导航目标 = 根布局 + 部件 + 绑定。

页面是可放置的声明节点；根布局可用 `set` 设形态、`add` 放部件。路由由 `Facet` 声明。
"""

from __future__ import annotations

from typing import Any

from ..core.bind import Bind
from ..core.node import Node
from ..layout import Layout, VBox


class Page(Node):
    """单页。"""

    kind = "page"

    def __init__(self, name: str = "", *, title: str = "") -> None:
        super().__init__(name)
        self.title = title
        self.bind = Bind(self)
        self.layout: Layout = VBox()
        super().add(self.layout)  # 布局作为结构子节点，编译树才连得上

    def set(self, layout: type[Layout], **opts: Any) -> Layout:
        """设定根布局形态（`set` = 设形态）。"""
        self.clear()
        self.layout = layout(**opts)
        super().add(self.layout)
        return self.layout

    def add(self, component: object, *, at: object | None = None) -> object:
        """把部件放进根布局（`add` = 加持有）。"""
        return self.layout.add(component, at=at)


__all__ = ["Page"]
