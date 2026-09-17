# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主窗口与外壳：`MainWindow`（QMainWindow）+ `Shell`。

外壳 = 标题栏 +（活动栏 + 三栏）+ 状态栏；中央是「标签页 + 页面栈」；命令面板浮层。
见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from .components import (
    ActivityBar,
    Chip,
    CommandPalette,
    FormatToolbar,
    InspectorPanel,
    NavigatorPanel,
    StatusBar,
    TabBar,
    TitleBar,
)
from .components.editor import NoteEditor
from .layout import HBox, Split, Stack, VBox
from .pages import HistoryPage, Page, RelationsPage, SearchPage, TagsPage
from .session import VAULT_LABEL
from .theme import current_theme

if TYPE_CHECKING:
    from PySide6.QtCore import QPoint

    from .root import App

# 活动栏条目：(id, 字形, 提示)
_ACTIVITY_ITEMS = (
    ("notes", "\ue7c3", "笔记"),
    ("projects", "\ue8b7", "项目"),
    ("community", "\ue716", "社区"),
    ("search", "\ue721", "搜索"),
    ("tags", "\ue8ec", "标签"),
)
_PAGE_INDEX = {"notes": 0, "projects": 3, "community": 4, "search": 5, "tags": 6}


def _placeholder(hint: str) -> Page:
    """建一个占位页面。"""
    page = Page()
    label = QLabel(hint)
    label.setObjectName("Faint")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout = QVBoxLayout(page)
    layout.addWidget(label)
    return page


class Shell(VBox):
    """窗口内主体：标题栏 +（活动栏 + 导航 + 中央 + 检查器）+ 状态栏。"""

    def __init__(self, app: App, parent: QWidget | None = None) -> None:  # noqa: PLR0915 — 外壳装配集中于此
        super().__init__(parent=parent, spacing=0)
        self._app = app

        self.titlebar = TitleBar(f"Cairn / {VAULT_LABEL}")
        self._profile_chip = Chip("档案", on_click=self._open_profile_menu)
        self.titlebar.add(self._profile_chip)
        self.add(self.titlebar)
        self.statusbar = StatusBar()

        body = HBox(spacing=0)
        self.activity = ActivityBar()
        for item_id, glyph, tip in _ACTIVITY_ITEMS:
            self.activity.add_item(item_id, glyph, tip=tip)
        self.activity.activated.connect(self.switch_page)
        body.add(self.activity)

        self.navigator = NavigatorPanel()
        self.navigator.set_model(app.groups)
        self.navigator.note_activated.connect(self._open_note)
        self.navigator.new_note_requested.connect(self._new_note)
        self.navigator.new_group_requested.connect(self._new_group)
        self.navigator.context_requested.connect(self._show_context)
        self.navigator.node_dropped.connect(self._on_node_dropped)

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

        self.search_page = SearchPage()
        self.search_page.set_model(app.search_results)
        self.search_page.query_changed.connect(app.search_notes)
        self.search_page.note_activated.connect(self._open_note)

        self.tags_page = TagsPage()
        self.tags_page.set_model(app.tags)
        self.tags_page.tag_activated.connect(self._search_tag)

        self._pages = [
            self.notes_page,
            self.relations_page,
            self.history_page,
            self.projects_page,
            self.community_page,
            self.search_page,
            self.tags_page,
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
        body.add(self.split, stretch=1)
        self.add(body, stretch=1)

        self.add(self.statusbar)

        self.command_palette = CommandPalette(self)
        self.command_palette.set_provider(self._palette_items)
        self.command_palette.chosen.connect(self._on_palette_chosen)
        shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.command_palette.open_palette)

    # ---- 路由 ----
    def switch_page(self, item_id: str) -> None:
        """活动栏：切换中央页面。"""
        index = _PAGE_INDEX.get(item_id)
        if index is not None:
            self.center.set_current(index)

    def _sync_tabs(self) -> None:
        """标签变更后：重建标签条、按当前页切栈、刷新状态。"""
        self.tabbar.set_tabs(self._app.tab_rows(), self._app.active_key)
        key = self._app.active_key
        if key == "relations":
            self.center.set_current(1)
        elif key.startswith("history:"):
            self.center.set_current(2)
        elif key:
            self.center.set_current(0)
        self._update_status()

    def _update_status(self) -> None:
        self.statusbar.set_message(f"{self._app.notes.rowCount()} 篇笔记 · 就绪")

    def _search_tag(self, tag: str) -> None:
        self.switch_page("search")
        self.search_page.set_query(tag)

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
        self.titlebar.set_text(f"Cairn / {VAULT_LABEL} · {note.title or '未命名'}")

    def _new_note(self) -> None:
        self._app.create_note(title="新笔记")

    def _new_group(self) -> None:
        node = self.navigator.current_node()
        parent = node.key if node is not None and node.kind == "group" else ""
        self._app.create_group("新组", parent_gid=parent)

    def _run_tool(self, tool_id: str, _source: object) -> None:
        self.editor.apply_tool(tool_id)

    # ---- 命令面板 ----
    def _palette_items(self, query: str) -> list[tuple[str, str, str]]:
        needle = query.strip().lower()
        commands = [
            (command.title, "command", command.id)
            for command in self._app.commands.all()
            if not needle or needle in command.title.lower() or needle in command.id.lower()
        ]
        notes = [
            (row.title, "note", row.oid)
            for row in self._app.session.note_rows()
            if needle and (needle in row.title.lower() or needle in row.preview.lower())
        ]
        return (commands + notes)[:30]

    def _on_palette_chosen(self, kind: str, key: str) -> None:
        if kind == "command":
            self._app.run_command(key)
        elif kind == "note":
            self._open_note(key)

    # ---- 右键菜单 ----
    def _show_context(self, kind: str, key: str, pos: QPoint) -> None:
        menu = QMenu(self)
        selected = [node for node in self.navigator.selection() if node.kind == "note"]
        if len(selected) > 1:
            oids = [node.key for node in selected]
            menu.addAction(f"收藏所选（{len(oids)}）", lambda: self._app.favorite_many(oids))
            menu.addAction(f"回收所选（{len(oids)}）", lambda: self._app.trash_many(oids))
        elif kind == "group" and key:
            menu.addAction("新建子组", lambda: self._app.create_group("新组", parent_gid=key))
            menu.addAction("改名…", lambda: self._rename_group(key))
            menu.addAction("锁定 / 解锁", lambda: self._app.toggle_group_lock(key))
            menu.addAction("设置口令…", lambda: self._prompt_group_key(key))
            menu.addAction("删除组", lambda: self._app.delete_group(key))
        elif kind == "note":
            menu.addAction("关系", self._app.open_relations)
            menu.addAction("历史", lambda: self._app.open_history(key))
            share_menu = menu.addMenu("分享")
            for share_kind, share_name, label in self._app.share_targets():
                action = share_menu.addAction(label)
                action.setCheckable(True)
                action.setChecked(self._app.has_share(key, share_kind, share_name))
                action.triggered.connect(
                    lambda _checked=False, k=share_kind, n=share_name: self._app.toggle_share(
                        key, k, n
                    )
                )
            menu.addAction("公开到主页", lambda: self._app.toggle_homepage(key))
            menu.addAction("移出分组", lambda: self._app.clear_note_groups(key))
            if self._app.show_trash:
                menu.addAction("恢复", lambda: self._app.restore_note(key))
            else:
                menu.addAction("回收", lambda: self._app.trash_note(key))
        if not menu.isEmpty():
            menu.exec(pos)

    def _on_node_dropped(self, key: str, kind: str, target_gid: str) -> None:
        if kind == "group":
            self._app.move_group(key, target_gid)
        elif target_gid:
            self._app.add_note_to_group(key, target_gid)
        else:
            self._app.clear_note_groups(key)

    def _open_profile_menu(self) -> None:
        menu = QMenu(self)
        current = self._app.current_profile
        for name in self._app.profiles():
            action = menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(name == current)
            action.triggered.connect(lambda _checked=False, n=name: self._app.switch_profile(n))
        menu.addSeparator()
        menu.addAction("新建档案…", self._new_profile)
        menu.exec(self._profile_chip.mapToGlobal(self._profile_chip.rect().center()))

    def _new_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "新建档案", "名称")
        if ok:
            self._app.create_profile(name)

    def _rename_group(self, gid: str) -> None:
        title, ok = QInputDialog.getText(self, "改组名", "名称")
        if ok:
            self._app.rename_group(gid, title)

    def _prompt_group_key(self, gid: str) -> None:
        key, ok = QInputDialog.getText(
            self, "设置组口令", "留空并确定即清除", QLineEdit.EchoMode.Password
        )
        if ok:
            self._app.set_group_key(gid, key)


class MainWindow(QMainWindow):
    """OS 窗口：中央区放 `Shell`。"""

    def __init__(self, app: App) -> None:
        super().__init__()
        self._app = app
        self.setWindowTitle("Cairn")
        self.resize(1200, 800)
        self.setCentralWidget(Shell(app, self))
