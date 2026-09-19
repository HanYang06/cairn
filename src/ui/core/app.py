# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 内核 · 组合根与根壳。

`App` 持 `Session`；根壳 `SuperLayout` **固定命名区域**（一个萝卜一个坑）。
领域只能经 `mount` 把页面放进宿主插槽；壳本身不可增（逃生舱 = 往指定插槽 `add`）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .errors import UiError
from .node import Node

if TYPE_CHECKING:
    from ..page import Page
    from .facet import Facet
    from .session import Session


class SuperLayout(Node):
    """App 根壳：固定命名区域。"""

    def __init__(self) -> None:
        super().__init__("app", addable=False)
        self.titlebar = Node("titlebar", capacity=1)
        self.navigator = Node("navigator")
        self.content = Node("content")  # 标签页宿主
        self.inspector = Node("inspector", capacity=1)
        self.statusbar = Node("statusbar", capacity=1)


class App:
    """组合根：UI 的唯一装配入口。"""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.layout = SuperLayout()
        self._facets: list[Facet] = []
        self._routes: dict[object, Page] = {}
        self._active: Page | None = None

    def mount(self, facet: Facet, *, slot: Node | None = None) -> Facet:
        """挂载一个 Facet：默认页 + 显式页面进宿主插槽，路由登记进反查表。"""
        host = slot if slot is not None else self.layout.content
        host.add(facet.root)
        for page, route in facet.pages().items():
            host.add(page)
            self._routes[route] = page
        self._facets.append(facet)
        return facet

    def navigate(self, route: object) -> Page:
        """路由到某页（未挂载即报错）。"""
        page = self._routes.get(route)
        if page is None:
            raise UiError(f"未挂载的路由: {route!r}")
        self._active = page
        return page

    @property
    def active(self) -> Page | None:
        """当前页（未导航过为 `None`）。"""
        return self._active

    def facets(self) -> list[Facet]:
        """已挂载的 Facet。"""
        return list(self._facets)


__all__ = ["App", "SuperLayout"]
