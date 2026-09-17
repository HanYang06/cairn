# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主窗口与外壳：`MainWindow`（QMainWindow）+ `Shell`（活动栏 + 三栏）。

导航接真实笔记列表；中央 `Stack` 做页面路由；检查器接属性模型；编辑器为占位。
见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from .components import ActivityBar, HBox, InspectorPanel, ListPanel, Page, Split, Stack
from .editor import NoteEditor
from .theme import current_theme

if TYPE_CHECKING:
    from .root import App

# 活动栏条目：(id, 字形, 提示)
_ACTIVITY_ITEMS = (
    ("notes", "\ue8a5", "笔记"),
    ("projects", "\ue8b7", "项目"),
    ("community", "\ue716", "社区"),
)


def _page(hint: str) -> tuple[Page, QLabel]:
    """建一个占位页面，返回页面与其提示标签。"""
    page = Page()
    label = QLabel(hint)
    label.setObjectName("Faint")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout = QVBoxLayout(page)
    layout.addWidget(label)
    return page, label


class Shell(HBox):
    """窗口内主体：活动栏 +（导航 + 中央页面栈 + 检查器）。"""

    def __init__(self, app: App, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, spacing=0)
        self._app = app

        self.activity = ActivityBar()
        for item_id, glyph, tip in _ACTIVITY_ITEMS:
            self.activity.add_item(item_id, glyph, tip=tip)
        self.activity.activated.connect(self.switch_page)
        self.add(self.activity)

        self.navigator = ListPanel("笔记", key_of=lambda row: row.oid)
        self.navigator.set_model(app.notes)
        self.navigator.activated.connect(self._open_note)

        self.notes_page = Page()
        self.editor = NoteEditor()
        self.editor.body_changed.connect(app.update_current_body)
        notes_layout = QVBoxLayout(self.notes_page)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_layout.addWidget(self.editor)
        self.projects_page, _ = _page("项目（远期）")
        self.community_page, _ = _page("社区（远期）")
        self._pages = [self.notes_page, self.projects_page, self.community_page]
        self.center = Stack(*self._pages)

        self.inspector = InspectorPanel()
        self.inspector.set_model(app.properties)

        self.split = Split(
            self.navigator,
            self.center,
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

    def switch_page(self, item_id: str) -> None:
        """按活动栏条目 id 切换中央页面。"""
        items = self.activity.items
        index = items.index(item_id) if item_id in items else -1
        if 0 <= index < len(self._pages):
            self.center.set_current(index)

    def _open_note(self, oid: str) -> None:
        self.switch_page("notes")
        self._app.open_note(oid)
        try:
            note = self._app.session.note(oid)
        except Exception:  # noqa: BLE001 — 缺失 / 损坏不崩界面
            return
        self.editor.load_note(note)


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
