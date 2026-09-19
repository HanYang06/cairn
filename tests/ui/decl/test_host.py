# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""页面宿主测试：注册表 / 懒加载 / 切换 / 生命周期 / 错误路径（离屏）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QStackedWidget, QTabBar

from cairn.ui.decl import (
    Compiler,
    Label,
    Page,
    PageHost,
    PageHostWidget,
    PageRegistry,
    RegistryError,
    RouteError,
    Scope,
    VBox,
)
from cairn.ui.decl.host import _build_page_host
from cairn.ui.theme import LIGHT

if TYPE_CHECKING:
    from collections.abc import Callable

pytestmark = pytest.mark.usefixtures("qapp")


def _page(route: str) -> Page:
    page = Page(route=route, title=route.upper())
    page.add(VBox())
    return page


def _factory(route: str) -> Callable[[], Page]:
    return lambda: _page(route)


def _registry(*routes: str) -> PageRegistry:
    registry = PageRegistry()
    for route in routes:
        registry.register(route, _factory(route))
    return registry


def _host(registry: PageRegistry, active: str = "") -> PageHostWidget:
    widget = Compiler(Scope(LIGHT)).build(PageHost(registry=registry, active=active))
    assert isinstance(widget, PageHostWidget)
    return widget


def test_registry_basic() -> None:
    registry = _registry("a")
    assert registry.routes() == ["a"]
    assert "a" in registry
    assert "b" not in registry
    assert registry.factory("a")().route == "a"


def test_registry_rejects_empty_route() -> None:
    with pytest.raises(RouteError):
        PageRegistry().register("", _factory("x"))


def test_registry_rejects_duplicate_route() -> None:
    registry = _registry("a")
    with pytest.raises(RouteError):
        registry.register("a", _factory("a"))


def test_registry_unknown_route_errors() -> None:
    with pytest.raises(RouteError):
        PageRegistry().factory("nope")


def test_host_builds_tabs_and_stack() -> None:
    widget = _host(_registry("a", "b"), active="a")
    assert widget.findChild(QTabBar) is not None
    assert widget.findChild(QStackedWidget) is not None
    assert widget.routes() == ["a", "b"]
    assert widget.current_route() == "a"


def test_host_defaults_to_first_route() -> None:
    assert _host(_registry("a", "b")).current_route() == "a"


def test_host_lazy_builds_only_active() -> None:
    widget = _host(_registry("a", "b"), active="a")
    stack = widget.findChild(QStackedWidget)
    assert stack is not None
    assert stack.count() == 1
    widget.show_route("b")
    assert stack.count() == 2


def test_host_reuses_built_page() -> None:
    widget = _host(_registry("a", "b"), active="a")
    widget.show_route("b")
    widget.show_route("a")
    stack = widget.findChild(QStackedWidget)
    assert stack is not None
    assert stack.count() == 2
    assert widget.current_route() == "a"


def test_host_switch_updates_current() -> None:
    widget = _host(_registry("a", "b"), active="a")
    widget.show_route("b")
    assert widget.current_route() == "b"
    stack = widget.findChild(QStackedWidget)
    assert stack is not None
    assert stack.currentIndex() == 1


def test_host_lifecycle_order() -> None:
    log: list[str] = []

    def first() -> Page:
        return (
            _page("a")
            .on_enter(lambda: log.append("enter-a"))
            .on_leave(lambda: log.append("leave-a"))
        )

    def second() -> Page:
        return (
            _page("b")
            .on_enter(lambda: log.append("enter-b"))
            .on_leave(lambda: log.append("leave-b"))
        )

    registry = PageRegistry()
    registry.register("a", first)
    registry.register("b", second)
    widget = _host(registry, active="a")
    assert log == ["enter-a"]
    widget.show_route("b")
    assert log == ["enter-a", "leave-a", "enter-b"]
    widget.show_route("b")
    assert log == ["enter-a", "leave-a", "enter-b"]


def test_host_unknown_route_errors() -> None:
    widget = _host(_registry("a"), active="a")
    with pytest.raises(RouteError):
        widget.show_route("zzz")


def test_host_tab_click_switches() -> None:
    widget = _host(_registry("a", "b"), active="a")
    bar = widget.findChild(QTabBar)
    assert bar is not None
    bar.setCurrentIndex(1)
    assert widget.current_route() == "b"


def test_host_ignores_out_of_range_tab() -> None:
    widget = _host(_registry("a"), active="a")
    widget._on_tab_changed(99)
    assert widget.current_route() == "a"


def test_single_route_hides_tab_bar() -> None:
    widget = _host(_registry("a"), active="a")
    bar = widget.findChild(QTabBar)
    assert bar is not None
    assert bar.isHidden() is True


def test_multi_route_shows_tab_bar() -> None:
    widget = _host(_registry("a", "b"), active="a")
    bar = widget.findChild(QTabBar)
    assert bar is not None
    assert bar.isHidden() is False


def test_empty_registry_builds_empty_host() -> None:
    widget = _host(PageRegistry())
    assert widget.current_route() == ""
    assert widget.routes() == []


def test_host_builder_rejects_wrong_type() -> None:
    with pytest.raises(RegistryError):
        _build_page_host(Label("x"), Compiler(Scope(LIGHT)))
