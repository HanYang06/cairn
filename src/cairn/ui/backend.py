# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 后端适配：把内核 Vault 暴露给 QML。

职责边界：这一层只做「内核 ↔ Qt」的翻译（模型、槽、信号），
不放业务规则（业务在 domains），也不放界面（界面在 qml）。
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    Qt,
    QTimer,
    Signal,
    Slot,
)

from ..core import Vault
from ..core.store import CATALOG_NAME as _CATALOG_NAME
from ..domains import Note, Relation, ancestors, decode_substrate, descendants, plain_text
from ..domains.provenance import DERIVED_FROM

DEV_PASSPHRASE = "cairn-dev"
_SPACE_LABELS = {"default": "个人空间"}
RELATIONS_KEY = "relations"


def _default_vault_root() -> Path:
    """源码 checkout 时把开发库放项目下；否则回落到用户目录。"""
    repo = Path(__file__).resolve().parents[3]
    if (repo / "pyproject.toml").is_file():
        return repo / "vault"
    return Path.home() / ".cairn-dev"


DEV_VAULT = _default_vault_root()


def open_vault(root: Path | str, passphrase: str = DEV_PASSPHRASE) -> Vault:
    """打开或创建库（开发期用固定口令；正式解锁流程后续再补）。"""
    root = Path(root)
    if (root / _CATALOG_NAME).exists():
        vault = Vault.load(root)
        vault.unlock(passphrase)
        return vault
    return Vault.create(root, passphrase)


def _fmt_time(ms: int) -> str:
    moment = datetime.datetime.fromtimestamp(ms / 1000)
    now = datetime.datetime.now()
    if moment.date() == now.date():
        return moment.strftime("%H:%M")
    if moment.year == now.year:
        return moment.strftime("%m-%d")
    return moment.strftime("%Y-%m-%d")


def _fmt_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / 1024 / 1024:.1f} MB"


def _title_of(vault: Vault, oid: Any) -> str:
    try:
        return vault.info(oid).title or "未命名"
    except Exception:
        return "（缺失）"


def _short_author(hex_key: str) -> str:
    return hex_key[:8] if hex_key else ""


def _node_meta(vault: Vault, oid: Any) -> dict[str, Any]:
    try:
        info = vault.info(oid)
    except Exception:
        return {"author": "", "updated": "", "ts": 0}
    return {
        "author": _short_author(info.author),
        "updated": _fmt_time(info.updated),
        "ts": info.updated,
    }


class ProfileStore:
    """本地档案：设备身份之上的若干昵称（暂时只是名字）。"""

    def __init__(self, root: Path) -> None:
        self._path = Path(root) / ".cairn" / "profiles.json"
        self._active = ""
        self._names: list[str] = []
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        self._active = str(data.get("active") or "")
        self._names = [str(name) for name in data.get("profiles") or []]

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"active": self._active, "profiles": self._names}
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @property
    def active(self) -> str:
        return self._active

    def names(self) -> list[str]:
        return list(self._names)

    def create(self, name: str) -> None:
        name = name.strip()
        if not name or name in self._names:
            return
        self._names.append(name)
        self._active = name
        self._save()

    def switch(self, name: str) -> None:
        if name in self._names:
            self._active = name
            self._save()


class NotesModel(QAbstractListModel):
    """笔记列表模型（按更新时间倒序，可关键词/标签过滤）。"""

    OidRole = Qt.ItemDataRole.UserRole + 1
    TitleRole = Qt.ItemDataRole.UserRole + 2
    PreviewRole = Qt.ItemDataRole.UserRole + 3
    UpdatedRole = Qt.ItemDataRole.UserRole + 4
    FavoriteRole = Qt.ItemDataRole.UserRole + 5
    ArchivedRole = Qt.ItemDataRole.UserRole + 6

    def __init__(self, vault: Vault, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._vault = vault
        self._rows: list[Any] = []
        self._texts: dict[str, str] = {}
        self._previews: dict[str, str] = {}
        self._favorites: dict[str, bool] = {}
        self._archived: dict[str, bool] = {}
        self._query = ""
        self._tag: str | None = None
        self._show_archived = False
        self._show_trash = False
        self.reload()

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.OidRole: b"oid",
            self.TitleRole: b"title",
            self.PreviewRole: b"preview",
            self.UpdatedRole: b"updated",
            self.FavoriteRole: b"favorite",
            self.ArchivedRole: b"archived",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._rows)

    def data(  # type: ignore[override]
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        info = self._rows[index.row()]
        oid = str(info.oid)
        if role == self.OidRole:
            return oid
        if role == self.TitleRole:
            return info.title or "未命名"
        if role == self.PreviewRole:
            return self._previews.get(oid, "")
        if role == self.UpdatedRole:
            return _fmt_time(info.updated)
        if role == self.FavoriteRole:
            return self._favorites.get(oid, False)
        if role == self.ArchivedRole:
            return self._archived.get(oid, False)
        return None

    def set_query(self, query: str) -> None:
        self._query = query.strip()
        self.reload()

    def set_tag(self, tag: str | None) -> None:
        self._tag = tag or None
        self.reload()

    def set_show_archived(self, show: bool) -> None:
        self._show_archived = show
        self.reload()

    def set_show_trash(self, show: bool) -> None:
        self._show_trash = show
        self.reload()

    def oids(self) -> list[str]:
        return [str(info.oid) for info in self._rows]

    def _query_matches(self) -> set[str] | None:
        """用索引检索返回命中的 oid；索引为空时返回 None（走内存回落）。"""
        if not self._query:
            return None
        try:
            if self._vault.index_is_empty():
                return None
            return {str(oid) for oid in self._vault.search(self._query)}
        except Exception:
            return None

    def reload(self) -> None:
        self.beginResetModel()
        infos = sorted(
            self._vault.iter(type=Note.kind),
            key=lambda info: info.updated,
            reverse=True,
        )
        matching = self._query_matches()
        needle = self._query.lower()
        rows: list[Any] = []
        texts: dict[str, str] = {}
        previews: dict[str, str] = {}
        favorites: dict[str, bool] = {}
        archived: dict[str, bool] = {}
        for info in infos:
            oid = str(info.oid)
            props: dict[str, Any] = {}
            try:
                note = Note.load(self._vault, info.oid)
                text = note.text
                props = note.props()
            except Exception:
                text = ""
            favorite = bool(props.get("favorite"))
            is_archived = bool(props.get("archived"))
            is_trashed = bool(props.get("trashed"))
            texts[oid] = text
            previews[oid] = text.strip().replace("\n", " ")[:90]
            favorites[oid] = favorite
            archived[oid] = is_archived
            if self._show_trash:
                if not is_trashed:
                    continue
            else:
                if is_trashed:
                    continue
                if is_archived and not self._show_archived:
                    continue
            if self._tag is not None and self._tag not in info.tags:
                continue
            if needle:
                if matching is not None:
                    if oid not in matching:
                        continue
                elif needle not in (info.title or "").lower() and needle not in text.lower():
                    continue
            rows.append(info)
        self._rows = rows
        self._texts = texts
        self._previews = previews
        self._favorites = favorites
        self._archived = archived
        self.endResetModel()


class TabsModel(QAbstractListModel):
    """打开的标签（笔记＝任务；关系/历史＝视图）。"""

    OidRole = Qt.ItemDataRole.UserRole + 1
    TitleRole = Qt.ItemDataRole.UserRole + 2
    KindRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._items: list[tuple[str, str, str]] = []

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {self.OidRole: b"oid", self.TitleRole: b"title", self.KindRole: b"kind"}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._items)

    def data(  # type: ignore[override]
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        key, title, kind = self._items[index.row()]
        if role == self.OidRole:
            return key
        if role == self.TitleRole:
            return title or "无标题"
        if role == self.KindRole:
            return kind
        return None

    def index_of(self, key: str) -> int:
        for position, (item_key, _, _) in enumerate(self._items):
            if item_key == key:
                return position
        return -1

    def tab_keys(self) -> list[str]:
        return [key for key, _, _ in self._items]

    def add(self, key: str, title: str, kind: str = "note") -> int:
        existing = self.index_of(key)
        if existing >= 0:
            return existing
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append((key, title, kind))
        self.endInsertRows()
        return row

    def remove(self, key: str) -> None:
        row = self.index_of(key)
        if row < 0:
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        self._items.pop(row)
        self.endRemoveRows()

    def set_title(self, key: str, title: str) -> None:
        row = self.index_of(key)
        if row < 0:
            return
        _, _, kind = self._items[row]
        self._items[row] = (key, title, kind)
        changed = self.index(row, 0)
        self.dataChanged.emit(changed, changed, [self.TitleRole])


class Backend(QObject):
    """QML 侧的唯一后端入口。"""

    currentChanged = Signal()
    contentChanged = Signal()
    tagsChanged = Signal()
    sharesChanged = Signal()
    viewChanged = Signal()
    versionsChanged = Signal()
    tagsListChanged = Signal()
    profilesChanged = Signal()
    archivedViewChanged = Signal()
    propsChanged = Signal()

    def __init__(self, vault: Vault, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._vault = vault
        self._profiles = ProfileStore(vault.root)
        self.notes = NotesModel(vault, self)
        self.tabs = TabsModel(self)
        self._current: Note | None = None
        self._view = "note"
        self._history_oid = ""
        self._pending_oid: str | None = None
        self._pending_text: str = ""
        self._show_archived = False
        self._show_trash = False
        self._save = QTimer(self)
        self._save.setSingleShot(True)
        self._save.setInterval(900)
        self._save.timeout.connect(self.flush)
        self._ensure_search_index()

    def _ensure_search_index(self) -> None:
        try:
            if self._vault.index_is_empty() and any(self._vault.pool.iter_object_ids()):
                self._vault.rebuild_index(text_of=self._note_text)
        except Exception:
            pass

    def _note_text(self, manifest: Any) -> str:
        try:
            note = Note.load(self._vault, manifest.oid)
            return f"{note.title or ''}\n{note.text}"
        except Exception:
            return ""

    # ---- 当前笔记 ----
    def _oid(self) -> str:
        return str(self._current.oid) if self._current is not None else ""

    @Property(str, notify=currentChanged)
    def currentOid(self) -> str:
        return self._oid()

    @Property(str, notify=currentChanged)
    def currentTitle(self) -> str:
        return (self._current.title or "") if self._current is not None else ""

    @Property(str, notify=currentChanged)
    def currentText(self) -> str:
        return self._current.text if self._current is not None else ""

    @Property(str, notify=currentChanged)
    def currentSpace(self) -> str:
        name = self._vault.space().name
        return _SPACE_LABELS.get(name, name)

    @Property(str, notify=currentChanged)
    def currentCreated(self) -> str:
        return _fmt_time(self._current.info.created) if self._current is not None else ""

    @Property(str, notify=currentChanged)
    def currentUpdated(self) -> str:
        return _fmt_time(self._current.info.updated) if self._current is not None else ""

    @Property(str, notify=profilesChanged)
    def currentAuthor(self) -> str:
        return self._profiles.active or "本机"

    @Property(int, notify=currentChanged)
    def currentWords(self) -> int:
        return len(self._current.text) if self._current is not None else 0

    @Property(str, notify=currentChanged)
    def currentSize(self) -> str:
        return _fmt_size(self._current.info.size) if self._current is not None else ""

    @Property(list, notify=tagsChanged)
    def currentTags(self) -> list[str]:
        return list(self._current.tags) if self._current is not None else []

    @Property(bool, notify=propsChanged)
    def currentFavorite(self) -> bool:
        if self._current is None:
            return False
        return bool(self._current.props().get("favorite"))

    @Property(bool, notify=propsChanged)
    def currentArchived(self) -> bool:
        if self._current is None:
            return False
        return bool(self._current.props().get("archived"))

    @Property(list, notify=propsChanged)
    def currentProperties(self) -> list[dict[str, Any]]:
        """当前笔记的属性（KV 检查器数据源）：每个属性带 id / type / editable。"""
        if self._current is None:
            return []
        props = self._current.props()
        return [
            {"id": "kind", "key": "类型", "value": "笔记", "type": "text", "editable": False},
            {
                "id": "space",
                "key": "空间",
                "value": self.currentSpace,
                "type": "text",
                "editable": False,
            },
            {
                "id": "author",
                "key": "作者",
                "value": self.currentAuthor,
                "type": "text",
                "editable": False,
            },
            {
                "id": "tags",
                "key": "标签",
                "value": list(self._current.tags),
                "type": "tags",
                "editable": True,
            },
            {
                "id": "favorite",
                "key": "收藏",
                "value": bool(props.get("favorite")),
                "type": "bool",
                "editable": True,
            },
            {
                "id": "archived",
                "key": "归档",
                "value": bool(props.get("archived")),
                "type": "bool",
                "editable": True,
            },
            {
                "id": "created",
                "key": "创建",
                "value": self.currentCreated,
                "type": "text",
                "editable": False,
            },
            {
                "id": "updated",
                "key": "修改",
                "value": self.currentUpdated,
                "type": "text",
                "editable": False,
            },
            {
                "id": "words",
                "key": "字数",
                "value": self.currentWords,
                "type": "count",
                "editable": False,
            },
            {
                "id": "size",
                "key": "大小",
                "value": self.currentSize,
                "type": "text",
                "editable": False,
            },
        ]

    @Property(list, notify=sharesChanged)
    def currentShares(self) -> list[dict[str, str]]:
        return self._shares()

    @Property(bool, notify=sharesChanged)
    def isPrivate(self) -> bool:
        return len(self._shares()) == 0

    @Property(list, notify=currentChanged)
    def currentAncestors(self) -> list[dict[str, str]]:
        if self._current is None:
            return []
        return [
            {"oid": str(oid), "title": _title_of(self._vault, oid)}
            for oid in ancestors(self._vault, self._current.oid)
        ]

    @Property(list, notify=currentChanged)
    def currentDescendants(self) -> list[dict[str, str]]:
        if self._current is None:
            return []
        return [
            {"oid": str(oid), "title": _title_of(self._vault, oid)}
            for oid in descendants(self._vault, self._current.oid)
        ]

    @Property(list, notify=currentChanged)
    def currentPath(self) -> list[dict[str, Any]]:
        """来源面包屑：来源（旧的在前）→ 当前。"""
        if self._current is None:
            return []
        path: list[dict[str, Any]] = [
            {"oid": str(oid), "title": _title_of(self._vault, oid), "current": False}
            for oid in reversed(ancestors(self._vault, self._current.oid))
        ]
        path.append(
            {
                "oid": str(self._current.oid),
                "title": self._current.title or "未命名",
                "current": True,
            }
        )
        return path

    # ---- 视图 ----
    @Property(str, notify=viewChanged)
    def currentView(self) -> str:
        return self._view

    @Property(str, notify=viewChanged)
    def historyTitle(self) -> str:
        return _title_of(self._vault, self._history_oid) if self._history_oid else ""

    @Property(str, notify=viewChanged)
    def historyOid(self) -> str:
        return self._history_oid

    @Property(dict, notify=currentChanged)
    def currentGraph(self) -> dict[str, Any]:
        """当前笔记的关系图：节点含 depth（负=来源，正=派生），边为 derived-from。"""
        if self._current is None:
            return {"nodes": [], "edges": []}
        root = str(self._current.oid)
        nodes: dict[str, dict[str, Any]] = {
            root: {
                "oid": root,
                "title": self._current.title or "未命名",
                "depth": 0,
                "current": True,
                **_node_meta(self._vault, self._current.oid),
            }
        }
        edges: dict[tuple[str, str], dict[str, Any]] = {}
        seen = {root}
        queue: list[tuple[str, int]] = [(root, 0)]
        while queue:
            cur, depth = queue.pop(0)
            for edge in Relation.outbound(self._vault, cur, relation=DERIVED_FROM):
                target = str(edge.target)
                edges.setdefault(
                    (cur, target),
                    {"from": cur, "to": target, "at": edge.at, "kind": DERIVED_FROM},
                )
                if target not in nodes:
                    nodes[target] = {
                        "oid": target,
                        "title": _title_of(self._vault, target),
                        "depth": depth - 1,
                        "current": False,
                        **_node_meta(self._vault, target),
                    }
                if target not in seen:
                    seen.add(target)
                    queue.append((target, depth - 1))
            for edge in Relation.backlinks(self._vault, cur, relation=DERIVED_FROM):
                source = str(edge.source)
                edges.setdefault(
                    (source, cur),
                    {"from": source, "to": cur, "at": edge.at, "kind": DERIVED_FROM},
                )
                if source not in nodes:
                    nodes[source] = {
                        "oid": source,
                        "title": _title_of(self._vault, source),
                        "depth": depth + 1,
                        "current": False,
                        **_node_meta(self._vault, source),
                    }
                if source not in seen:
                    seen.add(source)
                    queue.append((source, depth + 1))
        depths = [node["depth"] for node in nodes.values()]
        low = min(depths) if depths else 0
        for node in nodes.values():
            node["depth"] -= low
        return {"nodes": list(nodes.values()), "edges": list(edges.values())}

    @Slot(int, result=str)
    def previewVersion(self, seq: int) -> str:
        oid = self._history_oid or self._oid()
        if not oid:
            return ""
        try:
            return plain_text(decode_substrate(self._vault.read_version(oid, seq)))
        except Exception:
            return ""

    @Property(list, notify=versionsChanged)
    def currentVersions(self) -> list[dict[str, Any]]:
        oid = self._history_oid or self._oid()
        if not oid:
            return []
        try:
            return [
                {
                    "seq": version.seq,
                    "updated": _fmt_time(version.updated),
                    "size": _fmt_size(version.size),
                    "current": version.is_current,
                    "author": _short_author(version.author),
                }
                for version in self._vault.versions(oid)
            ]
        except Exception:
            return []

    # ---- 标签聚合 ----
    @Property(list, notify=tagsListChanged)
    def allTags(self) -> list[str]:
        tags: set[str] = set()
        for info in self._vault.iter(type=Note.kind):
            tags.update(info.tags)
        return sorted(tags)

    # ---- 档案 ----
    @Property(list, notify=profilesChanged)
    def profiles(self) -> list[str]:
        return self._profiles.names()

    @Property(str, notify=profilesChanged)
    def currentProfile(self) -> str:
        return self._profiles.active

    @Slot(str)
    def createProfile(self, name: str) -> None:
        self._profiles.create(name)
        self.profilesChanged.emit()
        self.currentChanged.emit()

    @Slot(str)
    def switchProfile(self, name: str) -> None:
        self._profiles.switch(name)
        self.profilesChanged.emit()
        self.currentChanged.emit()

    def _set_current(self, note: Note | None) -> None:
        self._current = note
        self.currentChanged.emit()
        self.tagsChanged.emit()
        self.sharesChanged.emit()
        self.propsChanged.emit()

    def _activate(self, note: Note) -> None:
        self._set_current(note)
        self._view = "note"
        self.viewChanged.emit()
        self.tabs.add(str(note.oid), note.title or "无标题", "note")

    # ---- 生命周期 ----
    @Slot(result=str)
    def createNote(self) -> str:
        self.flush()
        note = Note.create(self._vault, "", title="新笔记")
        self._activate(note)
        self.notes.reload()
        return str(note.oid)

    @Slot(str, result=str)
    def captureNote(self, text: str) -> str:
        self.flush()
        text = text.strip()
        if not text:
            return ""
        title = text.splitlines()[0][:40]
        note = Note.create(self._vault, text, title=title)
        self._activate(note)
        self.notes.reload()
        self.tagsListChanged.emit()
        return str(note.oid)

    @Slot(str)
    def openNote(self, oid: str) -> None:
        if not oid or (oid == self._oid() and self._view == "note"):
            return
        self.flush()
        self._activate(Note.load(self._vault, oid))

    @Slot()
    def openRelations(self) -> None:
        self.flush()
        self.tabs.add(RELATIONS_KEY, "关系", "relations")
        self._view = "relations"
        self.viewChanged.emit()

    @Slot(str)
    def openHistory(self, oid: str) -> None:
        oid = oid or self._oid()
        if not oid:
            return
        self.flush()
        self._history_oid = oid
        self.tabs.add(f"history:{oid}", "历史", "history")
        self._view = "history"
        self.viewChanged.emit()
        self.versionsChanged.emit()

    @Slot(int)
    def restoreVersion(self, seq: int) -> None:
        oid = self._history_oid or self._oid()
        if not oid:
            return
        self._vault.restore_version(oid, seq)
        if self._current is not None and str(self._current.oid) == oid:
            self._current = Note.load(self._vault, oid)
            self.currentChanged.emit()
        self.notes.reload()
        self.versionsChanged.emit()
        self.contentChanged.emit()

    @Slot(str)
    def activateTab(self, key: str) -> None:
        if key == RELATIONS_KEY:
            self.openRelations()
        elif key.startswith("history:"):
            self.openHistory(key.split(":", 1)[1])
        else:
            self.openNote(key)

    @Slot(str)
    def closeTab(self, key: str) -> None:
        self.flush()
        row = self.tabs.index_of(key)
        if row < 0:
            return
        self.tabs.remove(key)
        active = (
            (self._view == "relations" and key == RELATIONS_KEY)
            or (self._view == "history" and key == f"history:{self._history_oid}")
            or (self._view == "note" and key == self._oid())
        )
        if not active:
            return
        keys = self.tabs.tab_keys()
        if not keys:
            self._view = "note"
            self.viewChanged.emit()
            self._set_current(None)
            return
        self.activateTab(keys[min(row, len(keys) - 1)])

    @Slot(str)
    def deleteNote(self, oid: str) -> None:
        self.flush()
        self._vault.delete(oid)
        self.tabs.remove(oid)
        remaining = [key for key in self.tabs.tab_keys() if not key.startswith("history:")]
        if self._current is not None and str(self._current.oid) == oid:
            if remaining:
                self.openNote(remaining[-1])
            else:
                self._view = "note"
                self.viewChanged.emit()
                self._set_current(None)
        self.notes.reload()
        self.tagsListChanged.emit()

    # ---- 列表项操作（按 oid，不切换当前选中）----
    @Property(bool, notify=archivedViewChanged)
    def showArchived(self) -> bool:
        return self._show_archived

    @Slot()
    def toggleShowArchived(self) -> None:
        self._show_archived = not self._show_archived
        self.notes.set_show_archived(self._show_archived)
        self.archivedViewChanged.emit()

    def _apply_flag(self, oid: str, key: str, value: bool) -> None:
        note = Note.load(self._vault, oid)
        props = note.props()
        props[key] = value
        note.update(props=props)
        if self._current is not None and str(self._current.oid) == oid:
            self._current = Note.load(self._vault, oid)
            self.propsChanged.emit()
        self.notes.reload()

    @Slot(str)
    def toggleFavorite(self, oid: str) -> None:
        if not oid:
            return
        try:
            note = Note.load(self._vault, oid)
        except Exception:
            return
        self._apply_flag(oid, "favorite", not bool(note.props().get("favorite")))

    @Slot(str)
    def toggleArchive(self, oid: str) -> None:
        if not oid:
            return
        try:
            note = Note.load(self._vault, oid)
        except Exception:
            return
        self._apply_flag(oid, "archived", not bool(note.props().get("archived")))

    @Slot(str)
    def toggleHomepageOf(self, oid: str) -> None:
        if not oid:
            return
        try:
            note = Note.load(self._vault, oid)
        except Exception:
            return
        shares = list(note.props().get("share") or [])
        if any(str(entry.get("kind")) == "homepage" for entry in shares):
            shares = [entry for entry in shares if str(entry.get("kind")) != "homepage"]
        else:
            shares.append({"kind": "homepage", "name": ""})
        props = note.props()
        props["share"] = shares
        note.update(props=props)
        if self._current is not None and str(self._current.oid) == oid:
            self._current = Note.load(self._vault, oid)
            self.sharesChanged.emit()
            self.propsChanged.emit()
        self.notes.reload()

    @Slot(str, result=str)
    def deriveFrom(self, oid: str) -> str:
        """以指定笔记为源复刻一份，并建立 derived-from 边。"""
        if not oid:
            return ""
        self.flush()
        try:
            source = Note.load(self._vault, oid)
        except Exception:
            return ""
        title = f"{source.title or '未命名'}（复刻）"
        note = Note.create(self._vault, source.text, title=title)
        Relation.create(
            self._vault,
            note.oid,
            source.oid,
            relation=DERIVED_FROM,
            props={"at": str(source.info.seq)},
        )
        self._activate(note)
        self.notes.reload()
        return str(note.oid)

    @Slot(str, result="QVariantMap")
    def noteInfo(self, oid: str) -> dict[str, Any]:
        try:
            note = Note.load(self._vault, oid)
        except Exception:
            return {}
        props = note.props()
        return {
            "oid": str(note.oid),
            "title": note.title or "未命名",
            "favorite": bool(props.get("favorite")),
            "archived": bool(props.get("archived")),
            "trashed": bool(props.get("trashed")),
            "homepage": any(
                str(entry.get("kind")) == "homepage" for entry in (props.get("share") or [])
            ),
        }

    # ---- 回收站 ----
    @Property(bool, notify=propsChanged)
    def showTrash(self) -> bool:
        return self._show_trash

    @Slot()
    def toggleShowTrash(self) -> None:
        self._show_trash = not self._show_trash
        self.notes.set_show_trash(self._show_trash)
        self.propsChanged.emit()

    @Property(int, notify=propsChanged)
    def trashedCount(self) -> int:
        count = 0
        for info in self._vault.iter(type=Note.kind):
            try:
                if Note.load(self._vault, info.oid).props().get("trashed"):
                    count += 1
            except Exception:
                continue
        return count

    def _flag_trashed(self, oid: str, value: bool) -> None:
        if not oid:
            return
        try:
            note = Note.load(self._vault, oid)
        except Exception:
            return
        props = note.props()
        props["trashed"] = value
        note.update(props=props)
        if self._current is not None and str(self._current.oid) == oid:
            self._current = Note.load(self._vault, oid)
        self.notes.reload()
        self.propsChanged.emit()

    @Slot(str)
    def trashNote(self, oid: str) -> None:
        self._flag_trashed(oid, True)

    @Slot(str)
    def restoreNote(self, oid: str) -> None:
        self._flag_trashed(oid, False)

    @Slot(str)
    def purgeNote(self, oid: str) -> None:
        if not oid:
            return
        self.flush()
        self._vault.delete(oid)
        self.tabs.remove(oid)
        if self._current is not None and str(self._current.oid) == oid:
            self._view = "note"
            self.viewChanged.emit()
            self._set_current(None)
        self.notes.reload()
        self.propsChanged.emit()

    @Slot()
    def emptyTrash(self) -> None:
        self.flush()
        for info in list(self._vault.iter(type=Note.kind)):
            try:
                trashed = bool(Note.load(self._vault, info.oid).props().get("trashed"))
            except Exception:
                continue
            if trashed:
                self._vault.delete(info.oid)
                self.tabs.remove(str(info.oid))
        if self._current is not None and self.tabs.index_of(str(self._current.oid)) < 0:
            self._view = "note"
            self.viewChanged.emit()
            self._set_current(None)
        self.notes.reload()
        self.propsChanged.emit()

    # ---- 编辑 ----
    @Slot()
    def flush(self) -> None:
        if self._pending_oid is None:
            return
        oid, text = self._pending_oid, self._pending_text
        self._pending_oid = None
        note = Note.load(self._vault, oid)
        if note.text != text:
            note.update(text=text)
            if self._current is not None and str(self._current.oid) == oid:
                self._current = note
            self.notes.reload()
            self.contentChanged.emit()

    @Slot(str)
    def queueSave(self, text: str) -> None:
        if self._current is None:
            return
        self._pending_oid = str(self._current.oid)
        self._pending_text = text
        self._save.start()

    @Slot(str)
    def renameNote(self, title: str) -> None:
        if self._current is None:
            return
        self._current.update(title=title)
        self.tabs.set_title(str(self._current.oid), title or "无标题")
        self.notes.reload()
        self.contentChanged.emit()

    @Slot(result=str)
    def deriveNote(self) -> str:
        """以当前笔记为源复刻一份，并建立 derived-from 边（钉住源版本）。"""
        if self._current is None:
            return ""
        self.flush()
        source = self._current
        title = f"{source.title or '未命名'}（复刻）"
        note = Note.create(self._vault, source.text, title=title)
        Relation.create(
            self._vault,
            note.oid,
            source.oid,
            relation=DERIVED_FROM,
            props={"at": str(source.info.seq)},
        )
        self._activate(note)
        self.notes.reload()
        return str(note.oid)

    # ---- 分享 ----
    def _shares(self) -> list[dict[str, str]]:
        if self._current is None:
            return []
        result: list[dict[str, str]] = []
        for entry in self._current.props().get("share") or []:
            kind = str(entry.get("kind") or "")
            name = str(entry.get("name") or "")
            if kind == "homepage":
                label = "个人主页"
            elif kind == "community":
                label = f"社区 · {name}"
            elif kind == "person":
                label = f"某人 · {name}"
            else:
                continue
            result.append({"kind": kind, "name": name, "label": label})
        return result

    def _write_shares(self, shares: list[dict[str, str]]) -> None:
        if self._current is None:
            return
        self._current.update(props={"share": shares})
        self.sharesChanged.emit()
        self.propsChanged.emit()
        self.contentChanged.emit()

    @Slot(str, str)
    def addShare(self, kind: str, name: str) -> None:
        """分享给：homepage（公开到主页）/ community / person。"""
        if self._current is None or kind not in ("homepage", "community", "person"):
            return
        name = name.strip()
        if kind != "homepage" and not name:
            return
        shares = list(self._current.props().get("share") or [])
        entry = {"kind": kind, "name": name}
        if entry in shares:
            return
        shares.append(entry)
        self._write_shares(shares)

    @Slot(str, str)
    def removeShare(self, kind: str, name: str) -> None:
        if self._current is None:
            return
        shares = [
            entry
            for entry in (self._current.props().get("share") or [])
            if not (str(entry.get("kind")) == kind and str(entry.get("name") or "") == name)
        ]
        self._write_shares(shares)

    @Slot()
    def toggleHomepage(self) -> None:
        if self._current is None:
            return
        shares = list(self._current.props().get("share") or [])
        if any(str(entry.get("kind")) == "homepage" for entry in shares):
            shares = [entry for entry in shares if str(entry.get("kind")) != "homepage"]
        else:
            shares.append({"kind": "homepage", "name": ""})
        self._write_shares(shares)

    @Property(list, notify=profilesChanged)
    def shareTargets(self) -> list[dict[str, str]]:
        """可分享对象：社区 + 本机成员（不再让用户手输）。"""
        targets = [
            {"kind": "community", "name": name}
            for name in ("Cairn 中文", "本地优先软件", "开源设计")
        ]
        targets += [{"kind": "person", "name": name} for name in self._profiles.names()]
        return targets

    @Slot(str, str)
    def toggleShareTo(self, kind: str, name: str) -> None:
        if self._current is None or kind not in ("community", "person"):
            return

        def same(entry: dict[str, Any]) -> bool:
            return str(entry.get("kind")) == kind and str(entry.get("name") or "") == name

        shares = list(self._current.props().get("share") or [])
        if any(same(entry) for entry in shares):
            shares = [entry for entry in shares if not same(entry)]
        else:
            shares.append({"kind": kind, "name": name})
        self._write_shares(shares)

    # ---- 批量 ----
    @Slot(list)
    def trashMany(self, oids: list) -> None:
        self._set_many(oids, lambda props: props.update({"trashed": True}))

    @Slot(list)
    def restoreMany(self, oids: list) -> None:
        self._set_many(oids, lambda props: props.update({"trashed": False}))

    @Slot(list)
    def favoriteMany(self, oids: list) -> None:
        self._set_many(oids, lambda props: props.update({"favorite": True}))

    @Slot(list, str)
    def addTagToMany(self, oids: list, tag: str) -> None:
        tag = tag.strip()
        if not tag:
            return
        for raw in oids:
            oid = str(raw)
            try:
                note = Note.load(self._vault, oid)
            except Exception:
                continue
            tags = dict(note.tags)
            key = tag.partition(":")[0].strip()
            if key in tags:
                continue
            tags[key] = tag.partition(":")[2].strip() or None
            note.update(tags=tags)
            if self._current is not None and str(self._current.oid) == oid:
                self._current = Note.load(self._vault, oid)
        self.notes.reload()
        self.tagsChanged.emit()
        self.tagsListChanged.emit()
        self.propsChanged.emit()

    def _set_many(self, oids: list, mutate: Any) -> None:
        self.flush()
        for raw in oids:
            oid = str(raw)
            try:
                note = Note.load(self._vault, oid)
            except Exception:
                continue
            props = note.props()
            mutate(props)
            note.update(props=props)
            if self._current is not None and str(self._current.oid) == oid:
                self._current = Note.load(self._vault, oid)
        self.notes.reload()
        self.propsChanged.emit()

    @Slot(result=list)
    def visibleNoteOids(self) -> list[str]:
        return self.notes.oids()

    # ---- 过滤 ----
    @Slot(str)
    def filterNotes(self, query: str) -> None:
        self.notes.set_query(query)

    @Slot(str)
    def filterByTag(self, tag: str) -> None:
        self.notes.set_tag(tag)

    # ---- 标签 ----
    @Slot(str)
    def addTag(self, tag: str) -> None:
        tag = tag.strip()
        if not tag or self._current is None:
            return
        key, _, value = tag.partition(":")
        tags = dict(self._current.tags)
        tags[key.strip()] = value.strip() or None
        self._current.update(tags=tags)
        self.tagsChanged.emit()
        self.tagsListChanged.emit()
        self.propsChanged.emit()
        self.notes.reload()

    @Slot(str)
    def removeTag(self, tag: str) -> None:
        if self._current is None:
            return
        key = str(tag).partition(":")[0].strip()
        tags = dict(self._current.tags)
        tags.pop(key, None)
        self._current.update(tags=tags)
        self.tagsChanged.emit()
        self.tagsListChanged.emit()
        self.propsChanged.emit()
        self.notes.reload()

    @Property(list, notify=propsChanged)
    def tagPairs(self) -> list[dict[str, str]]:
        """标签按 KV 呈现：键值各自列出，无值则 value 为空。"""
        tags = self._current.tags if self._current is not None else {}
        return [
            {"key": key, "value": value or "", "raw": f"{key}:{value}" if value else key}
            for key, value in tags.items()
        ]

    @Slot(str, str, str)
    def replaceTag(self, old: str, key: str, value: str) -> None:
        """把某个标签改写为 ``key:value``；key 为空则删除。"""
        if self._current is None:
            return
        key = key.strip()
        value = value.strip()
        tags = dict(self._current.tags)
        old_key = str(old).partition(":")[0].strip()
        tags.pop(old_key, None)
        if key:
            tags[key] = value or None
        self._current.update(tags=tags)
        self.tagsChanged.emit()
        self.tagsListChanged.emit()
        self.propsChanged.emit()
        self.notes.reload()


def seed_demo(backend: Backend) -> None:
    """给开发/预览用的示例笔记（仅在空库时写入）。"""
    if backend.notes.rowCount() > 0:
        return
    samples = [
        (
            "存储层设计笔记",
            "内容先落在本地对象池，再进入索引；块级去重让相同内容只存一份。",
            ["存储", "设计"],
        ),
        (
            "布局取舍 v1",
            "把「收」和「编」分开：收集时零摩擦，整理时再建立关系与归属。",
            ["设计"],
        ),
        (
            "QML 外壳草案",
            "领域栏、工具册、标签工作区、上下文右区、来源面包屑。",
            ["客户端"],
        ),
    ]
    created: list[Note] = []
    for title, text, tags in samples:
        created.append(Note.create(backend._vault, text, title=title, tags=tags))
    qml_note = next((n for n in created if n.title == "QML 外壳草案"), None)
    layout_note = next((n for n in created if n.title == "布局取舍 v1"), None)
    if qml_note is not None and layout_note is not None:
        Relation.create(
            backend._vault,
            qml_note.oid,
            layout_note.oid,
            relation=DERIVED_FROM,
            props={"at": str(layout_note.info.seq)},
        )
    backend.notes.reload()
    total = backend.notes.rowCount()
    keys = [
        str(backend.notes.data(backend.notes.index(row, 0), NotesModel.OidRole))
        for row in reversed(range(total))
    ]
    for key in keys:
        backend.openNote(key)


def env_vault_root() -> Path:
    return Path(os.environ.get("CAIRN_VAULT", str(DEV_VAULT)))


def env_passphrase() -> str:
    return os.environ.get("CAIRN_DEV_PASSPHRASE", DEV_PASSPHRASE)
