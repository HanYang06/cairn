# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`Facet`：一个域的整套 UI 定义（声明层）。

- 构造收**注入的领域对象**（不碰总线、不自取）。
- `page(page, route_signal)` 注册页面 + 路由；`navigate` 反查。
- `set` / `add` 作用于默认页（`root`）；`bind` / `conf` 为声明入口。
- 浅分析暂缺（待领域侧统一规范），当前只执行显式声明。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..page import Page
from .bind import Bind, Binding
from .conf import Conf
from .errors import UiError
from .node import Node

if TYPE_CHECKING:
    from ..layout import Layout


class Facet:
    """域 UI 交付单元（分析器 / 组织器 / 包装器三合一的声明半）。"""

    kind = "facet"

    def __init__(self, domain: object, *, name: str = "") -> None:
        self.domain = domain
        self.name = name or type(domain).__name__
        self.conf = Conf()
        self.bind = Bind(self)
        self.root = Page("root")
        self._pages: dict[Page, object] = {}
        self._routes: dict[object, Page] = {}

    def set(self, layout: type[Layout], **opts: Any) -> Layout:
        """设定默认页的根布局形态。"""
        return self.root.set(layout, **opts)

    def add(self, component: object, *, at: object | None = None) -> object:
        """往默认页添加部件。"""
        return self.root.add(component, at=at)

    def page(self, page: Page, route: object) -> Page:
        """注册一个页面及其路由信号（重复注册以最后一次为准）。"""
        self._pages[page] = route
        self._routes[route] = page
        return page

    def pages(self) -> dict[Page, object]:
        """已注册页面：`Page → 路由信号`。"""
        return dict(self._pages)

    def navigate(self, route: object) -> Page:
        """按路由信号反查页面。"""
        page = self._routes.get(route)
        if page is None:
            raise UiError(f"未注册的路由: {route!r}")
        return page

    def compile_bindings(self) -> list[Binding]:
        """编译本域全部绑定（Facet + 默认页 + 各页面），非法即报错。"""
        result = self.bind.compile()
        result.extend(self.root.bind.compile())
        for page in self._pages:
            result.extend(page.bind.compile())
        return result

    def node_paths(self) -> list[tuple[str, Node]]:
        """本域的相对路径 → 节点：`<域>` / `<域>.<page>` / `<域>.<page>.<layout>.<com>…`。"""
        result: list[tuple[str, Node]] = []
        for page in [self.root, *self._pages]:
            prefix = self.name if page is self.root else f"{self.name}.{page.name or page.kind}"
            result.append((prefix, page))
            result.extend(self._walk(page.layout, prefix))
        return result

    def paths(self) -> list[str]:
        """本域的全部相对路径。"""
        return [path for path, _ in self.node_paths()]

    @staticmethod
    def _walk(node: Node, prefix: str) -> list[tuple[str, Node]]:
        base = f"{prefix}.{node.name or node.kind}"
        out: list[tuple[str, Node]] = [(base, node)]
        for placed in node.children():
            if isinstance(placed.component, Node):
                out.extend(Facet._walk(placed.component, base))
        return out

    def __repr__(self) -> str:
        return f"Facet({self.name!r}, pages={len(self._pages)})"


__all__ = ["Facet"]
