# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主窗口与外壳：`MainWindow`（QMainWindow）+ `Shell`（活动栏 + 三栏）。

导航是分组树；中央 `Stack` 做页面路由；检查器接属性模型；编辑器接富文本控件。
见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from .components import ActivityBar, InspectorPanel, NavigatorPanel
from .components.editor import NoteEditor
from .layout import HBox, Split, Stack
from .pages import Page
from .theme import current_theme

if TYPE_CHECKING:
    from PySide6.QtCore import QPoint

    from .root import App

# 活动栏条目：(id, 字形, 提示)
_ACTIVITY_ITEMS = (
    ("notes", "\ue7c3", "笔记"),
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

        self.navigator = NavigatorPanel()
        self.navigator.set_model(app.groups)
        self.navigator.note_activated.connect(self._open_note)
        self.navigator.new_note_requested.connect(self._new_note)
        self.navigator.new_group_requested.connect(self._new_group)
        self.navigator.context_requested.connect(self._show_context)

        self.notes_page = Page()
        self.editor = NoteEditor()
        self.editor.body_changed.connect(app.update_current_body)
        app.current_changed.connect(self._load_current)
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

    # ---- 笔记 ----
    def _open_note(self, oid: str) -> None:
        self.switch_page("notes")
        self._app.open_note(oid)

    def _load_current(self) -> None:
        oid = self._app.current_oid
        if not oid:
            return
        try:
            note = self._app.session.note(oid)
        except Exception:  # noqa: BLE001 — 缺失 / 损坏不崩界面
            return
        self.editor.load_note(note)

    def _new_note(self) -> None:
        self._app.create_note(title="新笔记")

    def _new_group(self) -> None:
        node = self.navigator.current_node()
        parent = node.key if node is not None and node.kind == "group" else ""
        self._app.create_group("新组", parent_gid=parent)

    # ---- 右键菜单 ----
    def _show_context(self, kind: str, key: str, pos: QPoint) -> None:
        menu = QMenu(self)
        if kind == "group" and key:
            menu.addAction("新建子组", lambda: self._app.create_group("新组", parent_gid=key))
            menu.addAction("改名…", lambda: self._rename_group(key))
            menu.addAction("锁定 / 解锁", lambda: self._app.toggle_group_lock(key))
            menu.addAction("删除组", lambda: self._app.delete_group(key))
        elif kind == "note":
            menu.addAction("移出分组", lambda: self._app.clear_note_groups(key))
            menu.addAction("回收", lambda: self._app.trash_note(key))
        if not menu.isEmpty():
            menu.exec(pos)

    def _rename_group(self, gid: str) -> None:
        title, ok = QInputDialog.getText(self, "改组名", "名称")
        if ok:
            self._app.rename_group(gid, title)


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
