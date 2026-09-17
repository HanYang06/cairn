# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 后端适配：把内核 Vault 暴露给 QML。

职责边界：这一层只做「内核 ↔ Qt」的翻译（模型、槽、信号），
不放业务规则（业务在 domains），也不放界面（界面在 qml）。
"""

from __future__ import annotations

import copy
import datetime
import json
import os
from pathlib import Path
from typing import Any, TypeGuard

from blake3 import blake3
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
from ..domains import Group, Note, Relation, ancestors, descendants
from ..domains.group import GroupError, list_groups
from ..domains.note.tools import PRESET_LAYOUT, ToolContext, run_tool, tool_info
from ..domains.provenance import DERIVED_FROM

DEV_PASSPHRASE = "cairn-dev"  # noqa: S105 — 开发期固定口令，非生产密钥
VAULT_LABEL = "个人空间"
RELATIONS_KEY = "relations"
# 连续编辑多久没动静才认为是"非连续编辑"，从而记一个版本检查点（毫秒）。
# 自动保存（900ms 去抖）只落盘、不记版本；版本由检查点统一产生。
CHECKPOINT_IDLE_MS = 5 * 60 * 1000


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
    moment = datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.UTC).astimezone()
    now = datetime.datetime.now(tz=datetime.UTC).astimezone()
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


def _short_signature(signature: Any) -> str:
    value = str(getattr(signature, "value", "") or "")
    if not value:
        return "—"
    alg = str(getattr(signature, "alg", "") or "")
    head = value[:10] + "…"
    return f"{alg} · {head}" if alg else head


def _group_key_hash(password: str) -> str:
    """组口令的校验哈希（存哈希不存明文；这不是加密）。"""
    return blake3(password.encode("utf-8")).hexdigest()


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

    def data(  # type: ignore[override]  # noqa: PLR0911 — 角色分派：多分支返回是本职
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

    def set_show_archived(self, *, show: bool) -> None:
        self._show_archived = show
        self.reload()

    def set_show_trash(self, *, show: bool) -> None:
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

    def reload(self) -> None:  # noqa: C901 — Qt 模型重载：排序/过滤/检索编排集中于此
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
    groupsChanged = Signal()

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
        self._pending_note: bool = False
        self._unlocked: set[str] = set()
        self._group_filter: str = ""
        self._show_archived = False
        self._show_trash = False
        self._save = QTimer(self)
        self._save.setSingleShot(True)
        self._save.setInterval(900)
        self._save.timeout.connect(self.flush)
        self._checkpoint = QTimer(self)
        self._checkpoint.setSingleShot(True)
        self._checkpoint.setInterval(CHECKPOINT_IDLE_MS)
        self._checkpoint.timeout.connect(self._checkpoint_now)
        self._ensure_search_index()

    def _ensure_search_index(self) -> None:
        try:
            if self._vault.index_is_empty() and any(self._vault.iter_object_ids()):
                self._vault.rebuild_index(text_of=self._note_text)
        except Exception:
            pass

    def _note_text(self, manifest: Any) -> str:
        try:
            note = Note.load(self._vault, manifest.oid)
        except Exception:
            return ""
        return f"{note.title or ''}\n{note.text}"

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

    @Property(list, notify=contentChanged)
    def currentBlocks(self) -> list[dict[str, Any]]:
        """当前笔记的块视图：行 + 行内样式段 + 占位（编辑器本体接口）。"""
        if self._current is None:
            return []
        return self._current.blocks()

    @Property(str, notify=currentChanged)
    def currentVaultLabel(self) -> str:
        return VAULT_LABEL

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
                "id": "vault",
                "key": "库",
                "value": self.currentVaultLabel,
                "type": "text",
                "editable": False,
            },
            {
                "id": "author",
                "key": "作者",
                "value": self._current.author or "—",
                "type": "text",
                "editable": False,
            },
            {
                "id": "authors",
                "key": "署名",
                "value": "、".join(str(name) for name in self._current.authors) or "—",
                "type": "text",
                "editable": False,
            },
            {
                "id": "signature",
                "key": "签名",
                "value": _short_signature(self._current.signature),
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
                "id": "visibility",
                "key": "可见性",
                "value": "私密" if not self._shares() else f"已分享 {len(self._shares())} 处",
                "type": "text",
                "editable": False,
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
            note = Note.load(self._vault, oid)
            history = note.history()
            index = len(history) - seq
            if not 0 <= index < len(history):
                return ""
            body = note.body_at(history[index]["id"])
            return "\n".join(str(line["v"]) for line in body if isinstance(line["v"], str))
        except Exception:
            return ""

    @Property(list, notify=versionsChanged)
    def currentVersions(self) -> list[dict[str, Any]]:
        oid = self._history_oid or self._oid()
        if not oid:
            return []
        try:
            note = Note.load(self._vault, oid)
            history = note.history()
            total = len(history)
            return [
                {
                    "seq": total - index,
                    "id": entry["id"],
                    "updated": _fmt_time(entry["at"]),
                    "size": "",
                    "current": index == 0,
                    "author": "",
                }
                for index, entry in enumerate(history)
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
        self.contentChanged.emit()
        self.tagsChanged.emit()
        self.sharesChanged.emit()
        self.propsChanged.emit()

    def _activate(self, note: Note) -> None:
        # 切走当前笔记 = 一次非连续编辑的边界：先给旧笔记记检查点。
        self._checkpoint_now()
        self._set_current(note)
        self._view = "note"
        self.viewChanged.emit()
        self.tabs.add(str(note.oid), note.title or "无标题", "note")

    # ---- 生命周期 ----
    @Slot(result=str)
    def createNote(self) -> str:
        note = Note.create(self._vault, "", title="新笔记")
        self._activate(note)
        self.notes.reload()
        return str(note.oid)

    @Slot(str, result=str)
    def captureNote(self, text: str) -> str:
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
        note = Note.load(self._vault, oid)
        history = note.history()
        index = len(history) - seq
        if not 0 <= index < len(history):
            return
        note.restore(history[index]["id"])
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
            self._checkpoint_now()
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
        self.notes.set_show_archived(show=self._show_archived)
        self.archivedViewChanged.emit()

    def _apply_flag(self, oid: str, key: str, *, value: bool) -> None:
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
        self._apply_flag(oid, "favorite", value=not bool(note.props().get("favorite")))

    @Slot(str)
    def toggleArchive(self, oid: str) -> None:
        if not oid:
            return
        try:
            note = Note.load(self._vault, oid)
        except Exception:
            return
        self._apply_flag(oid, "archived", value=not bool(note.props().get("archived")))

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

    def _clone_note(self, source: Note, title: str) -> Note:
        """逐字节克隆正文/样式/嵌入（保留行 id），只换标题。"""
        note = Note()
        note._vault = self._vault
        note.body.text = [copy.deepcopy(line) for line in source.body.text]
        note.body.style = copy.deepcopy(source.body.style)
        note.body.refresh()
        note.canvas = copy.deepcopy(source.canvas)
        note.access = copy.deepcopy(source.access)
        note.tags = dict(source.tags)
        note.attrs["props"] = copy.deepcopy(source.props())
        note.title = title
        note.save()
        return note

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
        note = self._clone_note(source, f"{source.title or '未命名'}（复刻）")
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
        self.notes.set_show_trash(show=self._show_trash)
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

    def _flag_trashed(self, oid: str, *, value: bool) -> None:
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
        self._flag_trashed(oid, value=True)

    @Slot(str)
    def restoreNote(self, oid: str) -> None:
        self._flag_trashed(oid, value=False)

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
    def _touch(self) -> None:
        """标记当前笔记有未落盘的行级改动：自动保存 + 重置检查点空闲计时。"""
        if self._current is None:
            return
        self._pending_note = True
        self._save.start()
        self._checkpoint.start()

    def _checkpoint_now(self) -> None:
        """记一个版本检查点：先落盘，再让笔记相对上次检查点追加版本。"""
        self.flush()
        self._checkpoint.stop()
        note = self._current
        if note is None:
            return
        note.save()
        self.notes.reload()
        self.versionsChanged.emit()

    @Slot()
    def flush(self) -> None:
        """只落盘当前内容，不记版本（连续编辑中的自动保存）。"""
        if self._pending_note:
            self._pending_note = False
            note = self._current
            if note is not None:
                note.persist()
                self.notes.reload()
                self.contentChanged.emit()
            return
        if self._pending_oid is None:
            return
        oid, text = self._pending_oid, self._pending_text
        self._pending_oid = None
        note = Note.load(self._vault, oid)
        if note.text != text:
            note.set_text(text)
            note.persist()
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
        self._checkpoint.start()

    @Slot()
    def saveNow(self) -> None:
        """显式保存（Ctrl+S）：落盘并立即记一个版本检查点。"""
        self._checkpoint_now()

    @Slot()
    def shutdown(self) -> None:
        """退出前收口：落盘 + 记检查点 + 关库。"""
        self._checkpoint_now()
        self._vault.close()

    # ---- 行级编辑（逐行编辑器后端接口）----
    @Slot(str, str)
    def setLineText(self, line_id: str, text: str) -> None:
        if self._current is None:
            return
        self._current.set_line(line_id, text)
        self._touch()

    @Slot(str, str, result=str)
    def insertLineAfter(self, line_id: str, text: str = "") -> str:
        if self._current is None:
            return ""
        new_id = self._current.insert_line_after(line_id or None, text)
        self._touch()
        return new_id

    @Slot(str)
    def removeLine(self, line_id: str) -> None:
        if self._current is None:
            return
        self._current.remove_line(line_id)
        self._touch()

    @Slot(str, int, result=str)
    def splitLine(self, line_id: str, offset: int) -> str:
        if self._current is None:
            return ""
        new_id = self._current.split_line(line_id, int(offset))
        self._touch()
        return new_id

    @Slot(str, result=str)
    def mergeLine(self, line_id: str) -> str:
        if self._current is None:
            return ""
        merged = self._current.merge_line(line_id)
        self._touch()
        return merged or ""

    @Slot(str, int, int, str)
    def toggleLineStyle(self, line_id: str, start: int, end: int, key: str) -> None:
        if self._current is None or end <= start:
            return
        self._current.toggle_style(line_id, int(start), int(end), key)
        self._touch()

    @Slot(str, "QVariantMap")
    def setParagraph(self, line_id: str, patch: dict[str, Any]) -> None:
        """行级（段落）属性：align / heading / list / level / block…，空值删键。"""
        if self._current is None or not line_id:
            return
        self._current.set_paragraph(line_id, patch)
        self._touch()

    @Slot(str)
    def clearParagraph(self, line_id: str) -> None:
        if self._current is None or not line_id:
            return
        self._current.clear_paragraph(line_id)
        self._touch()

    # ---- 工具（字级 / 段级）----
    @Property(list, notify=currentChanged)
    def tools(self) -> list[dict[str, str]]:
        """全部工具的元数据（供工具栏渲染）。"""
        return tool_info()

    @Property(list, notify=currentChanged)
    def toolLayout(self) -> list[list[list[str]]]:
        """预设布局：行 → 组 → 工具 id。"""
        return PRESET_LAYOUT

    @Slot(str, str, int, int)
    def runTool(self, tool_id: str, line_id: str, start: int, end: int) -> None:
        if self._current is None or not line_id:
            return
        line = next((item for item in self._current.body.text if item["id"] == line_id), None)
        if line is None:
            return
        value = line["v"]
        ctx = ToolContext(
            line_id=line_id,
            start=int(start),
            end=int(end),
            length=len(value) if isinstance(value, str) else 0,
            paragraph=dict(line.get("p") or {}),
        )
        if run_tool(tool_id, self._current, ctx):
            self._touch()

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
        note = self._clone_note(source, f"{source.title or '未命名'}（复刻）")
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
    def trashMany(self, oids: list[Any]) -> None:
        self._set_many(oids, lambda props: props.update({"trashed": True}))

    @Slot(list)
    def restoreMany(self, oids: list[Any]) -> None:
        self._set_many(oids, lambda props: props.update({"trashed": False}))

    @Slot(list)
    def favoriteMany(self, oids: list[Any]) -> None:
        self._set_many(oids, lambda props: props.update({"favorite": True}))

    @Slot(list, str)
    def addTagToMany(self, oids: list[Any], tag: str) -> None:
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

    def _set_many(self, oids: list[Any], mutate: Any) -> None:
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

    @Slot(str, result=list)
    def searchNotes(self, query: str) -> list[dict[str, Any]]:
        """工具册搜索：过滤笔记并返回前若干条（标题 + 摘要）供命令面板展示。"""
        self.notes.set_query(query)
        if not query.strip():
            return []
        results: list[dict[str, Any]] = []
        for row in range(self.notes.rowCount()):
            index = self.notes.index(row, 0)
            results.append(
                {
                    "oid": str(self.notes.data(index, NotesModel.OidRole) or ""),
                    "title": str(self.notes.data(index, NotesModel.TitleRole) or ""),
                    "preview": str(self.notes.data(index, NotesModel.PreviewRole) or ""),
                }
            )
            if len(results) >= 8:
                break
        return results

    @Slot(str)
    def filterByTag(self, tag: str) -> None:
        self.notes.set_tag(tag)

    # ---- 组 ----
    def _group_by_gid(self, gid: str) -> Group | None:
        if not gid:
            return None
        return Group.by_gid(self._vault, gid)

    def _note_node(self, oid: str) -> dict[str, Any] | None:
        try:
            note = Note.load(self._vault, oid)
        except Exception:
            return None
        props = note.props()
        if props.get("trashed"):
            return None
        return {
            "kind": "note",
            "oid": oid,
            "title": note.title or "未命名",
            "updated": _fmt_time(note.info.updated),
            "favorite": bool(props.get("favorite")),
            "archived": bool(props.get("archived")),
            "preview": note.text.strip().replace("\n", " ")[:90],
        }

    def _group_unlocked(self, group: Group) -> bool:
        return not group.key or group.gid in self._unlocked

    def _can_edit_group(self, group: Group | None) -> TypeGuard[Group]:
        return group is not None and not group.lock and self._group_unlocked(group)

    def _descendant_gids(self, group: Group) -> set[str]:
        out: set[str] = set()
        stack = [group]
        while stack:
            for child in stack.pop().subgroups(self._vault):
                if child.gid not in out:
                    out.add(child.gid)
                    stack.append(child)
        return out

    def _root_order(self) -> list[str]:
        raw = self._vault.bucket.catalog.get_meta("group_root_order") or ""
        return [item for item in raw.split(",") if item]

    def _set_root_order(self, order: list[str]) -> None:
        self._vault.bucket.catalog.set_meta("group_root_order", ",".join(order))
        self._vault.bucket.commit()

    def _group_node(self, group: Group, seen: set[str]) -> dict[str, Any]:
        unlocked = self._group_unlocked(group)
        node: dict[str, Any] = {
            "kind": "group",
            "gid": group.gid,
            "oid": str(group.oid),
            "title": group.title or "未命名组",
            "lock": bool(group.lock),
            "has_key": bool(group.key),
            "unlocked": unlocked,
            "children": [],
            "count": 0,
        }
        if group.gid in seen or not unlocked:
            return node
        seen = {*seen, group.gid}
        children: list[dict[str, Any]] = []
        for ref in group.group:
            child = self._group_by_gid(ref)
            if child is not None:
                children.append(self._group_node(child, seen))
            else:
                item = self._note_node(ref)
                if item is not None:
                    children.append(item)
        node["children"] = children
        node["count"] = len(children)
        return node

    @Property(list, notify=groupsChanged)
    def groupTree(self) -> list[dict[str, Any]]:
        """导航树：根组（递归子节点）+ 末尾「未分组」；有筛选时只返回该组子树。"""
        groups = list(list_groups(self._vault))
        if self._group_filter:
            root = self._group_by_gid(self._group_filter)
            if root is None:
                self._group_filter = ""
            else:
                return [self._group_node(root, set())]

        known = {group.gid for group in groups}
        contained: set[str] = set()
        referenced: set[str] = set()
        for group in groups:
            contained.update(group.group)
            referenced.update(ref for ref in group.group if ref not in known)

        roots = [group for group in groups if group.gid not in contained]
        rank = {gid: index for index, gid in enumerate(self._root_order())}
        roots.sort(key=lambda group: rank.get(group.gid, len(rank)))
        tree = [self._group_node(group, set()) for group in roots]

        ungrouped = [
            item
            for info in self._vault.iter(type=Note.kind)
            if str(info.oid) not in referenced
            if (item := self._note_node(str(info.oid))) is not None
        ]
        if ungrouped:
            tree.append(
                {
                    "kind": "group",
                    "gid": "",
                    "oid": "",
                    "title": "未分组",
                    "lock": False,
                    "has_key": False,
                    "unlocked": True,
                    "count": len(ungrouped),
                    "children": ungrouped,
                }
            )
        return tree

    def _notify_groups(self) -> None:
        self.groupsChanged.emit()
        self.notes.reload()

    @Property(str, notify=groupsChanged)
    def groupFilter(self) -> str:
        return self._group_filter

    @Slot(str)
    def filterByGroup(self, gid: str) -> None:
        self._group_filter = gid
        self.groupsChanged.emit()

    @Slot()
    def clearGroupFilter(self) -> None:
        self._group_filter = ""
        self.groupsChanged.emit()

    @Slot(str, str, result=str)
    def createGroup(self, title: str, parent_gid: str = "") -> str:
        title = title.strip() or "新组"
        parent = self._group_by_gid(parent_gid)
        if parent is not None and not self._can_edit_group(parent):
            return ""
        group = Group.create(self._vault, title, parent=parent)
        self._notify_groups()
        return group.gid

    @Slot(str, str)
    def renameGroup(self, gid: str, title: str) -> None:
        group = self._group_by_gid(gid)
        if not self._can_edit_group(group):
            return
        group.title = title.strip() or "未命名组"
        group.save()
        self._notify_groups()

    @Slot(str)
    def toggleGroupLock(self, gid: str) -> None:
        group = self._group_by_gid(gid)
        if group is None or not self._group_unlocked(group):
            return
        group.lock = not group.lock
        group.save()
        self._notify_groups()

    @Slot(str, str)
    def setGroupKey(self, gid: str, key: str) -> None:
        group = self._group_by_gid(gid)
        if not self._can_edit_group(group):
            return
        key = key.strip()
        group.key = _group_key_hash(key) if key else ""
        group.save()
        self._unlocked.discard(gid)
        self._notify_groups()

    @Slot(str, str, result=bool)
    def unlockGroup(self, gid: str, password: str) -> bool:
        group = self._group_by_gid(gid)
        if group is None:
            return False
        if not group.key:
            self._unlocked.add(gid)
            self._notify_groups()
            return True
        if _group_key_hash(password) != group.key:
            return False
        self._unlocked.add(gid)
        self._notify_groups()
        return True

    @Slot(str)
    def deleteGroup(self, gid: str) -> None:
        group = self._group_by_gid(gid)
        if not self._can_edit_group(group):
            return
        for parent in list(list_groups(self._vault)):
            if gid in parent.group and self._can_edit_group(parent):
                parent.remove(group)
        group.delete()
        self._unlocked.discard(gid)
        self._notify_groups()

    @Slot(str, str)
    def addNoteToGroup(self, oid: str, gid: str) -> None:
        group = self._group_by_gid(gid)
        if group is None or not oid or not self._can_edit_group(group):
            return
        try:
            group.add(Note.load(self._vault, oid))
        except GroupError:
            return
        self._notify_groups()

    @Slot(str, str)
    def removeNoteFromGroup(self, oid: str, gid: str) -> None:
        group = self._group_by_gid(gid)
        if group is None or not oid or not self._can_edit_group(group):
            return
        try:
            group.remove(oid)
        except GroupError:
            return
        self._notify_groups()

    @Slot(str)
    def clearNoteGroups(self, oid: str) -> None:
        """把某笔记从所有组里移除（拖到「未分组」）。"""
        if not oid:
            return
        changed = False
        for group in list_groups(self._vault):
            if oid in group.group and self._can_edit_group(group):
                group.remove(oid)
                changed = True
        if changed:
            self._notify_groups()

    @Slot(str, str)
    def moveGroup(self, gid: str, parent_gid: str) -> None:
        """把组挂到新父组下（``parent_gid`` 为空＝移回根）。"""
        group = self._group_by_gid(gid)
        if not self._can_edit_group(group) or gid == parent_gid:
            return
        parent = self._group_by_gid(parent_gid)
        if parent is not None:
            if not self._can_edit_group(parent):
                return
            if parent.gid == group.gid or parent.gid in self._descendant_gids(group):
                return
        parents = [item for item in list_groups(self._vault) if gid in item.group]
        if any(not self._can_edit_group(item) for item in parents):
            return
        for item in parents:
            item.remove(group)
        if parent is not None:
            parent.add(group)
        self._notify_groups()

    @Slot(str, int)
    def reorderGroup(self, gid: str, offset: int) -> None:
        """组在其父组内上移/下移（``offset`` = -1 / +1）；根组则改根序。"""
        group = self._group_by_gid(gid)
        if not self._can_edit_group(group):
            return
        for parent in list_groups(self._vault):
            if gid not in parent.group:
                continue
            if not self._can_edit_group(parent):
                return
            order = list(range(len(parent.group)))
            index = parent.group.index(gid)
            target = index + offset
            if 0 <= target < len(order):
                order[index], order[target] = order[target], order[index]
                parent.move(order)
            self._notify_groups()
            return
        ids = [item.gid for item in list_groups(self._vault)]
        roots_now = [item for item in self._root_order() if item in ids]
        roots_now.extend(item for item in ids if item not in roots_now)
        index = roots_now.index(gid)
        target = index + offset
        if 0 <= target < len(roots_now):
            roots_now[index], roots_now[target] = roots_now[target], roots_now[index]
            self._set_root_order(roots_now)
            self._notify_groups()

    @Slot(str, str, int)
    def reorderInGroup(self, gid: str, child_id: str, offset: int) -> None:
        group = self._group_by_gid(gid)
        if not self._can_edit_group(group) or child_id not in group.group:
            return
        order = list(range(len(group.group)))
        index = group.group.index(child_id)
        target = index + offset
        if 0 <= target < len(order):
            order[index], order[target] = order[target], order[index]
            group.move(order)
            self._notify_groups()

    @Property(list, notify=groupsChanged)
    def groupChoices(self) -> list[dict[str, str]]:
        """扁平组列表，供「移动到组」菜单使用。"""
        return [
            {"gid": group.gid, "title": group.title or "未命名组"}
            for group in list_groups(self._vault)
        ]

    @Slot(str, result=dict)
    def groupInfo(self, gid: str) -> dict[str, Any]:
        """单个组的操作视图（供组菜单 / 口令框使用）。"""
        group = self._group_by_gid(gid)
        if group is None:
            return {}
        parent = next(
            (item.gid for item in list_groups(self._vault) if gid in item.group),
            "",
        )
        return {
            "gid": gid,
            "title": group.title or "未命名组",
            "lock": bool(group.lock),
            "has_key": bool(group.key),
            "unlocked": self._group_unlocked(group),
            "in_group": parent != "",
        }

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
    storage_note = next((n for n in created if n.title == "存储层设计笔记"), None)
    work = Group.create(backend._vault, "工作")
    design = Group.create(backend._vault, "设计", parent=work)
    if storage_note is not None:
        work.add(storage_note)
    if layout_note is not None:
        design.add(layout_note)
    client = Group.create(backend._vault, "客户端")
    if qml_note is not None:
        client.add(qml_note)
    backend.notes.reload()
    total = backend.notes.rowCount()
    keys = [
        str(backend.notes.data(backend.notes.index(row, 0), NotesModel.OidRole))
        for row in reversed(range(total))
    ]
    for key in keys:
        backend.openNote(key)


def env_vault_root() -> Path:
    """开发库根目录：``CAIRN_VAULT`` 覆盖，否则用项目内 ``vault/``。"""
    return Path(os.environ.get("CAIRN_VAULT", str(DEV_VAULT)))


def env_passphrase() -> str:
    """开发口令：``CAIRN_DEV_PASSPHRASE`` 覆盖，否则用内置默认值。"""
    return os.environ.get("CAIRN_DEV_PASSPHRASE", DEV_PASSPHRASE)
