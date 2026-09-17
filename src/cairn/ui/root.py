# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`App`：应用组合根。

它是 UI 唯一的依赖入口：拥有库、`Session` / `SessionBridge` 与共享模型；
由装配层显式注入给各部件。部件不直接碰 `Vault`。见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from blake3 import blake3
from PySide6.QtCore import QObject, QTimer, Signal

from ..domains import Group, Note
from .bridge import SessionBridge
from .commands import CommandRegistry
from .default_commands import install
from .models import ListModel, TreeModel
from .rows import TabRow
from .session import Session
from .settings import SettingsStore

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..core import Vault
    from .rows import GroupNode, NoteRow, PropertyRow, RelationRow, VersionRow

SAVE_DEBOUNCE_MS = 800


def _group_key_hash(password: str) -> str:
    """组口令的校验哈希（存哈希不存明文；这不是加密）。"""
    return blake3(password.encode("utf-8")).hexdigest()


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
    """分组树模型的字段 → 取值函数（顺序与导航委托的角色对齐）。"""
    return [
        ("key", lambda node: node.key),
        ("kind", lambda node: node.kind),
        ("title", lambda node: node.title),
        ("preview", lambda node: node.preview),
        ("updated", lambda node: node.updated),
    ]


def _relation_fields() -> list[tuple[str, Callable[[RelationRow], object]]]:
    """关系视图模型的字段 → 取值函数。"""
    return [
        ("oid", lambda row: row.oid),
        ("title", lambda row: row.title),
        ("depth", lambda row: row.depth),
        ("current", lambda row: row.current),
    ]


def _version_fields() -> list[tuple[str, Callable[[VersionRow], object]]]:
    """历史视图模型的字段 → 取值函数。"""
    return [
        ("vid", lambda row: row.vid),
        ("label", lambda row: row.updated + ("（当前）" if row.current else "")),
        ("current", lambda row: row.current),
    ]


class App(QObject):
    """应用组合根：状态镜像、变更桥、共享模型与当前笔记。"""

    current_changed = Signal()
    properties_changed = Signal()
    tabs_changed = Signal()
    profiles_changed = Signal()

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
        self.relations: ListModel[RelationRow] = ListModel(_relation_fields(), display="title")
        self.versions: ListModel[VersionRow] = ListModel(_version_fields(), display="label")
        self.tags: ListModel[str] = ListModel([("name", lambda tag: tag)], display="name")
        self.search_results: ListModel[NoteRow] = ListModel(_note_fields(), display="title")
        self._open_tabs: list[TabRow] = []
        self._active_key = ""
        self._show_trash = False
        self._current_oid = ""
        self._pending_body: tuple[list[dict[str, Any]], dict[str, Any]] | None = None
        self._save = QTimer(self)
        self._save.setSingleShot(True)
        self._save.setInterval(SAVE_DEBOUNCE_MS)
        self._save.timeout.connect(self.flush_body)
        self.bridge.changed.connect(self._on_changed)
        self.reload_notes()
        self.reload_groups()
        self.reload_tags()

    @property
    def current_oid(self) -> str:
        """当前笔记 oid（无则空串）。"""
        return self._current_oid

    def reload_notes(self) -> None:
        """按当前 Session 投影刷新笔记列表模型（按回收站开关过滤）。"""
        rows = self.session.note_rows()
        if self._show_trash:
            rows = [row for row in rows if row.trashed]
        else:
            rows = [row for row in rows if not row.trashed]
        self.notes.set_rows(rows)

    def reload_tags(self) -> None:
        """聚合全部标签。"""
        tags: set[str] = set()
        for row in self.session.note_rows():
            tags.update(row.tags)
        self.tags.set_rows(sorted(tags))

    def search_notes(self, query: str) -> None:
        """按关键词过滤笔记（标题 / 预览），写入搜索模型。"""
        needle = query.strip().lower()
        if not needle:
            self.search_results.set_rows([])
            return
        rows = [
            row
            for row in self.session.note_rows()
            if needle in row.title.lower() or needle in row.preview.lower()
        ]
        self.search_results.set_rows(rows)

    @property
    def show_trash(self) -> bool:
        """是否处于回收站视图。"""
        return self._show_trash

    def toggle_trash(self) -> None:
        """切换回收站视图。"""
        self._show_trash = not self._show_trash
        self.reload_notes()

    def empty_trash(self) -> None:
        """清空回收站（真删）。"""
        for row in self.session.note_rows():
            if row.trashed:
                self.vault.delete(row.oid)
        self.reload_notes()
        self.reload_tags()

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

    def restore_note(self, oid: str) -> None:
        """从回收站恢复。"""
        try:
            note = self.session.note(oid)
        except Exception:  # noqa: BLE001 — 缺失不崩界面
            return
        props = note.props()
        props["trashed"] = False
        note.update(props=props)
        self.reload_notes()

    def _set_flag_many(self, oids: list[str], key: str, value: object) -> None:
        for raw in oids:
            try:
                note = self.session.note(str(raw))
            except Exception:  # noqa: BLE001, S112 — 缺失不崩界面
                continue
            props = note.props()
            props[key] = value
            note.update(props=props)
        self.reload_notes()

    def favorite_many(self, oids: list[str]) -> None:
        """批量收藏。"""
        self._set_flag_many(oids, "favorite", value=True)

    def trash_many(self, oids: list[str]) -> None:
        """批量回收。"""
        self._set_flag_many(oids, "trashed", value=True)

    def toggle_homepage(self, oid: str) -> None:
        """把笔记公开到主页 / 取消公开。"""
        try:
            note = self.session.note(oid)
        except Exception:  # noqa: BLE001 — 缺失不崩界面
            return
        props = note.props()
        shares = list(props.get("share") or [])
        if any(str(entry.get("kind")) == "homepage" for entry in shares):
            shares = [entry for entry in shares if str(entry.get("kind")) != "homepage"]
        else:
            shares.append({"kind": "homepage", "name": ""})
        props["share"] = shares
        note.update(props=props)
        if oid == self._current_oid:
            self.reload_properties()

    def set_group_key(self, gid: str, password: str) -> None:
        """设置 / 清除组口令（存哈希）。"""
        group = self._group(gid)
        if group is None:
            return
        group.key = _group_key_hash(password.strip()) if password.strip() else ""
        group.save()
        self.reload_groups()

    def unlock_group(self, gid: str, password: str) -> bool:
        """校验组口令。"""
        group = self._group(gid)
        if group is None:
            return False
        if not group.key:
            return True
        return _group_key_hash(password) == group.key

    # ---- 档案（本地昵称，存设置文件）----
    def profiles(self) -> list[str]:
        """全部档案名。"""
        raw = self.settings.get("profiles.names", [])
        return [str(name) for name in raw] if isinstance(raw, list) else []

    @property
    def current_profile(self) -> str:
        """当前档案名。"""
        return str(self.settings.get("profiles.active", "") or "本机")

    def create_profile(self, name: str) -> None:
        """新建档案并切到它。"""
        name = name.strip()
        if not name:
            return
        names = self.profiles()
        if name not in names:
            names.append(name)
        self.settings.set("profiles.names", names)
        self.settings.set("profiles.active", name)
        self.profiles_changed.emit()

    def switch_profile(self, name: str) -> None:
        """切换档案。"""
        if name in self.profiles():
            self.settings.set("profiles.active", name)
            self.profiles_changed.emit()

    # ---- 分享（props.share）----
    def share_targets(self) -> list[tuple[str, str, str]]:
        """可分享目标：``(kind, name, label)``。"""
        targets = [("homepage", "", "个人主页")]
        return [*targets, *(("person", name, f"某人 · {name}") for name in self.profiles())]

    def has_share(self, oid: str, kind: str, name: str) -> bool:
        """某笔记是否已分享给目标。"""
        try:
            note = self.session.note(oid)
        except Exception:  # noqa: BLE001 — 缺失不崩界面
            return False
        shares = note.props().get("share") or []
        return any(
            str(entry.get("kind")) == kind and str(entry.get("name") or "") == name
            for entry in shares
        )

    def toggle_share(self, oid: str, kind: str, name: str) -> None:
        """切换某个分享目标。"""
        try:
            note = self.session.note(oid)
        except Exception:  # noqa: BLE001 — 缺失不崩界面
            return
        props = note.props()
        shares = list(props.get("share") or [])

        def same(entry: dict[str, Any]) -> bool:
            return str(entry.get("kind")) == kind and str(entry.get("name") or "") == name

        if any(same(entry) for entry in shares):
            shares = [entry for entry in shares if not same(entry)]
        else:
            shares.append({"kind": kind, "name": name})
        props["share"] = shares
        note.update(props=props)
        if oid == self._current_oid:
            self.reload_properties()

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

    def open_note(self, oid: str) -> None:
        """打开 / 激活某篇笔记（新增或复用标签页）。"""
        if not oid:
            return
        if oid != self._current_oid:
            self.flush_body()
            self._current_oid = oid
            self.reload_properties()
            self.current_changed.emit()
        self._add_tab(oid, self.note_title(oid), "note")
        self._active_key = oid
        self.tabs_changed.emit()

    def open_relations(self) -> None:
        """打开关系视图标签页。"""
        self._add_tab("relations", "关系", "relations")
        self._active_key = "relations"
        self.reload_relations()
        self.tabs_changed.emit()

    def open_history(self, oid: str = "") -> None:
        """打开某篇笔记的历史标签页。"""
        target = oid or self._current_oid
        if not target:
            return
        key = f"history:{target}"
        self._add_tab(key, "历史", "history")
        self._active_key = key
        self.reload_versions(target)
        self.tabs_changed.emit()

    def activate_tab(self, key: str) -> None:
        """按 key 激活标签页。"""
        if not any(tab.key == key for tab in self._open_tabs):
            return
        if key == "relations":
            self._active_key = key
            self.reload_relations()
            self.tabs_changed.emit()
        elif key.startswith("history:"):
            self._active_key = key
            self.reload_versions(key.split(":", 1)[1])
            self.tabs_changed.emit()
        else:
            self.open_note(key)

    def close_tab(self, key: str) -> None:
        """关闭标签页；若关的是当前页则切到最后一个。"""
        self._open_tabs = [tab for tab in self._open_tabs if tab.key != key]
        if key != self._active_key:
            self.tabs_changed.emit()
            return
        if self._open_tabs:
            self.activate_tab(self._open_tabs[-1].key)
        else:
            self._active_key = ""
            self.tabs_changed.emit()

    @property
    def active_key(self) -> str:
        """当前激活标签的 key。"""
        return self._active_key

    def tab_rows(self) -> list[TabRow]:
        """当前打开的标签页。"""
        return list(self._open_tabs)

    def _add_tab(self, key: str, title: str, kind: str) -> None:
        if any(tab.key == key for tab in self._open_tabs):
            return
        self._open_tabs.append(TabRow(key, title or "无标题", kind))

    def reload_relations(self) -> None:
        """按当前笔记刷新关系视图。"""
        rows = self.session.relation_rows(self._current_oid) if self._current_oid else []
        self.relations.set_rows(rows)

    def reload_versions(self, oid: str) -> None:
        """按笔记刷新历史视图。"""
        self.versions.set_rows(self.session.version_rows(oid))

    def restore_version(self, vid: str) -> None:
        """把某篇笔记恢复到指定版本，并刷新视图。"""
        if not self._current_oid:
            return
        self.flush_body()
        try:
            note = self.session.note(self._current_oid)
        except Exception:  # noqa: BLE001 — 缺失不崩界面
            return
        note.restore(vid)
        self.reload_notes()
        self.reload_versions(self._current_oid)
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
        self.reload_tags()
        if self._current_oid:
            self.reload_properties()

    def shutdown(self) -> None:
        """退出前收口：落盘待写正文，断开桥与订阅，关闭库。"""
        self.flush_body()
        self.bridge.dispose()
        self.session.close()
        self.vault.close()


__all__ = ["App"]
