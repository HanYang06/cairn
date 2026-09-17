# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`App`：应用组合根。

它是 UI 唯一的依赖入口：拥有库、`Session` / `SessionBridge` 与共享模型；
由装配层显式注入给各部件。部件不直接碰 `Vault`。见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, QTimer, Signal

from ..domains import Group, Note
from .bridge import SessionBridge
from .commands import CommandRegistry
from .default_commands import install
from .models import ListModel, TreeModel
from .session import Session
from .settings import SettingsStore

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..core import Vault
    from .rows import GroupNode, NoteRow, PropertyRow

SAVE_DEBOUNCE_MS = 800


def _note_fields() -> list[tuple[str, Callable[[NoteRow], object]]]:
    """笔记列表模型的字段 → 取值函数。"""
    return [
        ("oid", lambda row: row.oid),
        ("title", lambda row: row.title),
        ("preview", lambda row: row.preview),
        ("updated", lambda row: row.updated_label),
        ("favorite", lambda row: row.favorite),
        ("archived", lambda row: row.archived),
    ]


def _property_fields() -> list[tuple[str, Callable[[PropertyRow], object]]]:
    """检查器模型的字段 → 取值函数。"""
    return [
        ("pid", lambda row: row.pid),
        ("label", lambda row: f"{row.key}: {row.value}"),
        ("key", lambda row: row.key),
        ("value", lambda row: row.value),
        ("kind", lambda row: row.kind),
        ("editable", lambda row: row.editable),
    ]


def _group_fields() -> list[tuple[str, Callable[[GroupNode], object]]]:
    """分组树模型的字段 → 取值函数。"""
    return [
        ("key", lambda node: node.key),
        ("kind", lambda node: node.kind),
        ("title", lambda node: node.title),
    ]


class App(QObject):
    """应用组合根：状态镜像、变更桥、共享模型与当前笔记。"""

    current_changed = Signal()
    properties_changed = Signal()

    def __init__(self, vault: Vault, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.vault = vault
        self.session = Session(vault)
        self.bridge = SessionBridge(self.session, self)
        self.settings = SettingsStore(vault.root)
        self.commands = CommandRegistry()
        install(self.commands)
        shortcuts = self.settings.get("commands.shortcuts", {})
        if isinstance(shortcuts, dict):
            self.commands.set_shortcuts(shortcuts)
        self.notes: ListModel[NoteRow] = ListModel(_note_fields(), display="title")
        self.properties: ListModel[PropertyRow] = ListModel(_property_fields(), display="label")
        self.groups: TreeModel[GroupNode] = TreeModel(
            _group_fields(), lambda node: node.children, display="title"
        )
        self._current_oid = ""
        self._pending_body: tuple[list[dict[str, Any]], dict[str, Any]] | None = None
        self._save = QTimer(self)
        self._save.setSingleShot(True)
        self._save.setInterval(SAVE_DEBOUNCE_MS)
        self._save.timeout.connect(self.flush_body)
        self.bridge.changed.connect(self._on_changed)
        self.reload_notes()
        self.reload_groups()

    @property
    def current_oid(self) -> str:
        """当前笔记 oid（无则空串）。"""
        return self._current_oid

    def reload_notes(self) -> None:
        """按当前 Session 投影刷新笔记列表模型。"""
        self.notes.set_rows(self.session.note_rows())

    def create_note(self, text: str = "", *, title: str | None = None) -> str:
        """新建一篇笔记并打开；返回其 oid。"""
        note = Note.create(self.vault, text, title=title)
        self.reload_notes()
        self.open_note(str(note.oid))
        return str(note.oid)

    def run_command(self, command_id: str) -> bool:
        """执行一条命令（上下文为组合根自身）。"""
        return self.commands.run(command_id, self)

    # ---- 分组 ----
    def reload_groups(self) -> None:
        """按当前 Session 投影刷新分组树模型。"""
        self.groups.set_roots(self.session.group_nodes())

    def _group(self, gid: str) -> Group | None:
        if not gid:
            return None
        return Group.by_gid(self.vault, gid)

    def create_group(self, title: str = "新组", *, parent_gid: str = "") -> str:
        """新建组（可指定父组），返回 gid。"""
        group = Group.create(self.vault, title or "新组", parent=self._group(parent_gid))
        self.reload_groups()
        return group.gid

    def rename_group(self, gid: str, title: str) -> None:
        """改组名（锁定则忽略）。"""
        group = self._group(gid)
        if group is None or group.lock:
            return
        group.title = title.strip() or "未命名组"
        group.save()
        self.reload_groups()

    def delete_group(self, gid: str) -> None:
        """删除组：先从所有父组摘除，再删块（锁定则忽略）。"""
        group = self._group(gid)
        if group is None or group.lock:
            return
        for parent in list(Group.list(self.vault)):
            if gid in parent.group:
                parent.remove(group)
        group.delete()
        self.reload_groups()

    def toggle_group_lock(self, gid: str) -> None:
        """锁定 / 解锁组编辑。"""
        group = self._group(gid)
        if group is None:
            return
        group.lock = not group.lock
        group.save()
        self.reload_groups()

    def add_note_to_group(self, oid: str, gid: str) -> None:
        """把笔记加进组。"""
        group = self._group(gid)
        if group is None or not oid or group.lock:
            return
        try:
            group.add(self.session.note(oid))
        except Exception:  # noqa: BLE001 — 缺失笔记不崩界面
            return
        self.reload_groups()

    def remove_note_from_group(self, oid: str, gid: str) -> None:
        """把笔记从组里移除。"""
        group = self._group(gid)
        if group is None or not oid or group.lock:
            return
        group.remove(oid)
        self.reload_groups()

    def move_group(self, gid: str, parent_gid: str) -> None:
        """把组挂到新父组下（``parent_gid`` 为空＝移回根）。"""
        group = self._group(gid)
        if group is None or gid == parent_gid:
            return
        parent = self._group(parent_gid)
        for item in [entry for entry in Group.list(self.vault) if gid in entry.group]:
            item.remove(group)
        if parent is not None:
            parent.add(group)
        self.reload_groups()

    def clear_note_groups(self, oid: str) -> None:
        """把某笔记从所有（未锁定的）组里移除。"""
        changed = False
        for group in list(Group.list(self.vault)):
            if oid in group.group and not group.lock:
                group.remove(oid)
                changed = True
        if changed:
            self.reload_groups()

    def trash_note(self, oid: str) -> None:
        """把笔记移入回收站（标记 props.trashed）。"""
        try:
            note = self.session.note(oid)
        except Exception:  # noqa: BLE001 — 缺失不崩界面
            return
        props = note.props()
        props["trashed"] = True
        note.update(props=props)
        self.reload_notes()

    def open_note(self, oid: str) -> None:
        """把某篇笔记设为当前，并刷新检查器属性。"""
        if oid == self._current_oid:
            return
        self.flush_body()
        self._current_oid = oid
        self.reload_properties()
        self.current_changed.emit()

    def update_current_body(self, body: list[dict[str, Any]], style: dict[str, Any]) -> None:
        """编辑器改动：记下待写正文，去抖后落盘。"""
        self._pending_body = (body, style)
        self._save.start()

    def flush_body(self) -> None:
        """把待写正文落到当前笔记（若有）。"""
        self._save.stop()
        pending = self._pending_body
        self._pending_body = None
        if pending is None or not self._current_oid:
            return
        body, style = pending
        try:
            note = self.session.note(self._current_oid)
        except Exception:  # noqa: BLE001 — 缺失 / 损坏不崩界面
            return
        note.set_body(body, style=style)
        note.persist()

    def reload_properties(self) -> None:
        """按当前笔记刷新检查器属性模型。"""
        rows = self.session.note_properties(self._current_oid) if self._current_oid else []
        self.properties.set_rows(rows)
        self.properties_changed.emit()

    def note_title(self, oid: str) -> str:
        """取一篇笔记的标题（供界面展示）。"""
        try:
            note = self.session.note(oid)
        except Exception:  # noqa: BLE001 — 缺失 / 损坏不崩界面
            return "（缺失）"
        return note.title or "未命名"

    def _on_changed(self) -> None:
        self.reload_notes()
        self.reload_groups()
        if self._current_oid:
            self.reload_properties()

    def shutdown(self) -> None:
        """退出前收口：落盘待写正文，断开桥与订阅，关闭库。"""
        self.flush_body()
        self.bridge.dispose()
        self.session.close()
        self.vault.close()


__all__ = ["App"]
