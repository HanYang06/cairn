# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主窗口与外壳：`MainWindow`（QMainWindow）+ `Shell`（活动栏 + 三栏）。

导航是分组树；中央是「标签页 + 页面栈」（笔记 / 关系 / 历史 + 项目 / 社区占位）；
检查器接属性模型；编辑器接富文本控件。见 `rules/references/ui-boundary.md`。
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

from .components import ActivityBar, FormatToolbar, InspectorPanel, NavigatorPanel, TabBar
from .components.editor import NoteEditor
from .layout import HBox, Split, Stack, VBox
from .pages import HistoryPage, Page, RelationsPage
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


def _placeholder(hint: str) -> Page:
    """建一个占位页面。"""
    page = Page()
    label = QLabel(hint)
    label.setObjectName("Faint")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout = QVBoxLayout(page)
    layout.addWidget(label)
    return page


class Shell(HBox):
    """窗口内主体：活动栏 +（导航 + 中央标签页/页面栈 + 检查器）。"""

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

        self.tabbar = TabBar()
        self.tabbar.activated.connect(app.activate_tab)
        self.tabbar.close_requested.connect(app.close_tab)

        self.notes_page = Page()
        self.editor = NoteEditor()
        self.editor.body_changed.connect(app.update_current_body)
        app.current_changed.connect(self._load_current)
        self.format_toolbar = FormatToolbar()
        self.format_toolbar.tool_triggered.connect(self._run_tool)
        notes_layout = QVBoxLayout(self.notes_page)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_layout.addWidget(self.format_toolbar)
        notes_layout.addWidget(self.editor, 1)

        self.relations_page = RelationsPage()
        self.relations_page.set_model(app.relations)
        self.relations_page.activated.connect(self._open_note)

        self.history_page = HistoryPage()
        self.history_page.set_model(app.versions)
        self.history_page.restore_requested.connect(app.restore_version)

        self.projects_page = _placeholder("项目（远期）")
        self.community_page = _placeholder("社区（远期）")

        self._pages = [
            self.notes_page,
            self.relations_page,
            self.history_page,
            self.projects_page,
            self.community_page,
        ]
        self.center = Stack(*self._pages)
        app.tabs_changed.connect(self._sync_tabs)
        self._sync_tabs()

        self.inspector = InspectorPanel()
        self.inspector.set_model(app.properties)

        self.split = Split(
            self.navigator,
            VBox(self.tabbar, self.center, spacing=0),
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

    # ---- 路由 ----
    def switch_page(self, item_id: str) -> None:
        """活动栏：切换中央页面。"""
        index = {"notes": 0, "projects": 3, "community": 4}.get(item_id)
        if index is not None:
            self.center.set_current(index)

    def _sync_tabs(self) -> None:
        """标签变更后：重建标签条并按当前页切栈。"""
        self.tabbar.set_tabs(self._app.tab_rows(), self._app.active_key)
        key = self._app.active_key
        if key == "relations":
            self.center.set_current(1)
        elif key.startswith("history:"):
            self.center.set_current(2)
        elif key:
            self.center.set_current(0)

    # ---- 笔记 ----
    def _open_note(self, oid: str) -> None:
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

    def _run_tool(self, tool_id: str, _source: object) -> None:
        self.editor.apply_tool(tool_id)

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
            menu.addAction("关系", self._app.open_relations)
            menu.addAction("历史", lambda: self._app.open_history(key))
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
