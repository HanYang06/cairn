# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""桌面入口（重建中）：组合根与启动。

组合根负责**创建**领域服务并**注入**给 `Facet`（`Facet` 自身不 import 领域）。
当前先给一个不依赖领域的 demo 入口，验证「声明树 → 窗口」整链；真实 Vault 装配随后接。
"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QMainWindow

from core.signal import Signal

from .component import Button, Field, Label
from .core import App, Facet, Session
from .core.qt import build_window
from .layout import HBox, VBox


def build_demo() -> QMainWindow:
    """构造一个不依赖领域的演示窗口。"""
    session = Session(Signal())
    app = App(session)
    facet = Facet(object(), name="demo")
    facet.set(VBox)
    facet.add(Label("Cairn"))
    row = HBox("row")
    row.add(Button("保存"))
    row.add(Field(placeholder="标题"))
    facet.add(row)
    app.mount(facet)
    return build_window(app)


def main() -> int:
    """桌面入口。"""
    app = QApplication.instance() or QApplication([])
    build_demo().show()
    return app.exec()


__all__ = ["build_demo", "main"]
