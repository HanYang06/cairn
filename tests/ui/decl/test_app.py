# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""组合根测试：根布局编译、窗口、示例应用。"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QMainWindow, QWidget

from cairn.ui.decl import App, Page, VBox, build_demo
from cairn.ui.theme import DARK

pytestmark = pytest.mark.usefixtures("qapp")


def _page() -> Page:
    page = Page(route="p", title="P")
    page.add(VBox())
    return page


def test_app_builds_root_layout() -> None:
    app = App()
    app.mount(_page())
    assert isinstance(app.build(), QWidget)


def test_app_window_wraps_root() -> None:
    app = App(theme=DARK, title="T")
    window = app.window()
    assert isinstance(window, QMainWindow)
    assert window.windowTitle() == "T"
    assert window.centralWidget() is not None


def test_build_demo() -> None:
    app = build_demo(theme=DARK)
    assert app.window().centralWidget() is not None
