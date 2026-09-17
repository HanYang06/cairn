# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主窗口与外壳：`MainWindow`（QMainWindow）+ `Shell`（三栏布局）。

导航已接真实笔记列表（`ListModel` → `ListPanel`）；编辑器 / 检查器为占位，P1 / P2 填入。
见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from .components import ListPanel, Page, Panel, Split, VBox
from .theme import current_theme

if TYPE_CHECKING:
    from .root import App


def _fill(widget: QWidget, hint: str) -> None:
    """给占位容器填一个居中的淡色标签。"""
    label = QLabel(hint)
    label.setObjectName("Faint")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout = QVBoxLayout(widget)
    layout.addWidget(label)


class Shell(VBox):
    """窗口内主体：导航 + 编辑区 + 检查器三栏可拖拽。"""

    def __init__(self, app: App, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self._app = app

        self.navigator = ListPanel("笔记", key_of=lambda row: row.oid)
        self.navigator.set_model(app.notes)
        self.navigator.activated.connect(self._open_note)

        self.editor = Page()
        self._editor_hint = QLabel("编辑器（P2）")
        self._editor_hint.setObjectName("Faint")
        self._editor_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        editor_layout = QVBoxLayout(self.editor)
        editor_layout.addWidget(self._editor_hint)

        self.inspector = Panel("属性")
        _fill(self.inspector.body, "属性检查器（P1）")

        self.split = Split(
            self.navigator,
            self.editor,
            self.inspector,
            orientation=Qt.Orientation.Horizontal,
        )
        splitter = self.split.splitter
        splitter.setObjectName("ShellSplit")
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([current_theme().side_bar_w, 900, 288])
        self.add(self.split, stretch=1)

    def _open_note(self, oid: str) -> None:
        self._editor_hint.setText(self._app.note_title(oid))


class MainWindow(QMainWindow):
    """OS 窗口：中央区放 `Shell`，底部状态栏。"""

    def __init__(self, app: App) -> None:
        super().__init__()
        self._app = app
        self.setWindowTitle("Cairn")
        self.resize(1200, 800)
        self.setCentralWidget(Shell(app, self))
        status = self.statusBar()
        if status is not None:
            status.showMessage("就绪")
