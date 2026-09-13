# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 后端适配：把内核 Vault 暴露给 QML。

职责边界：这一层只做「内核 ↔ Qt」的翻译（模型、槽、信号），
不放业务规则（业务在 domains），也不放界面（界面在 qml）。
"""

from __future__ import annotations

import datetime
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

from ..conf import TOML_NAME
from ..core import Vault
from ..domains import Note

DEV_PASSPHRASE = "cairn-dev"
DEV_VAULT = Path.home() / ".cairn-dev"
_SPACE_LABELS = {"default": "个人空间"}


def open_vault(root: Path | str, passphrase: str = DEV_PASSPHRASE) -> Vault:
    """打开或创建库（开发期用固定口令；正式解锁流程后续再补）。"""
    root = Path(root)
    if (root / TOML_NAME).exists():
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


def _preview(vault: Vault, oid: Any, limit: int = 90) -> str:
    try:
        text = Note.load(vault, oid).text.strip().replace("\n", " ")
    except Exception:
        return ""
    return text[:limit]


class NotesModel(QAbstractListModel):
    """笔记列表模型（按更新时间倒序）。"""

    OidRole = Qt.ItemDataRole.UserRole + 1
    TitleRole = Qt.ItemDataRole.UserRole + 2
    PreviewRole = Qt.ItemDataRole.UserRole + 3
    UpdatedRole = Qt.ItemDataRole.UserRole + 4

    def __init__(self, vault: Vault, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._vault = vault
        self._rows: list[Any] = []
        self._previews: dict[str, str] = {}
        self.reload()

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.OidRole: b"oid",
            self.TitleRole: b"title",
            self.PreviewRole: b"preview",
            self.UpdatedRole: b"updated",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._rows)

    def data(  # type: ignore[override]
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        info = self._rows[index.row()]
        if role == self.OidRole:
            return str(info.oid)
        if role == self.TitleRole:
            return info.title or "未命名"
        if role == self.PreviewRole:
            return self._previews.get(str(info.oid), "")
        if role == self.UpdatedRole:
            return _fmt_time(info.updated)
        return None

    def reload(self) -> None:
        self.beginResetModel()
        infos = sorted(
            self._vault.iter(type=Note.kind),
            key=lambda info: info.updated,
            reverse=True,
        )
        self._rows = list(infos)
        self._previews = {str(info.oid): _preview(self._vault, info.oid) for info in infos}
        self.endResetModel()


class TabsModel(QAbstractListModel):
    """打开的笔记标签（一个任务一个标签）。"""

    OidRole = Qt.ItemDataRole.UserRole + 1
    TitleRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._items: list[tuple[str, str]] = []

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {self.OidRole: b"oid", self.TitleRole: b"title"}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._items)

    def data(  # type: ignore[override]
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        oid, title = self._items[index.row()]
        if role == self.OidRole:
            return oid
        if role == self.TitleRole:
            return title or "无标题"
        return None

    def index_of(self, oid: str) -> int:
        for position, (item_oid, _) in enumerate(self._items):
            if item_oid == oid:
                return position
        return -1

    def oids(self) -> list[str]:
        return [oid for oid, _ in self._items]

    def add(self, oid: str, title: str) -> int:
        existing = self.index_of(oid)
        if existing >= 0:
            return existing
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append((oid, title))
        self.endInsertRows()
        return row

    def remove(self, oid: str) -> None:
        row = self.index_of(oid)
        if row < 0:
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        self._items.pop(row)
        self.endRemoveRows()

    def set_title(self, oid: str, title: str) -> None:
        row = self.index_of(oid)
        if row < 0:
            return
        self._items[row] = (oid, title)
        changed = self.index(row, 0)
        self.dataChanged.emit(changed, changed, [self.TitleRole])


class Backend(QObject):
    """QML 侧的唯一后端入口。"""

    currentChanged = Signal()
    contentChanged = Signal()
    tagsChanged = Signal()

    def __init__(self, vault: Vault, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._vault = vault
        self.notes = NotesModel(vault, self)
        self.tabs = TabsModel(self)
        self._current: Note | None = None
        self._pending_oid: str | None = None
        self._pending_text: str = ""
        self._save = QTimer(self)
        self._save.setSingleShot(True)
        self._save.setInterval(900)
        self._save.timeout.connect(self.flush)

    # ---- 当前笔记 ----
    @Property(str, notify=currentChanged)
    def currentOid(self) -> str:
        return str(self._current.oid) if self._current is not None else ""

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

    @Property(list, notify=tagsChanged)
    def currentTags(self) -> list[str]:
        return list(self._current.tags) if self._current is not None else []

    def _set_current(self, note: Note | None) -> None:
        self._current = note
        self.currentChanged.emit()
        self.tagsChanged.emit()

    def _activate(self, note: Note) -> None:
        self._set_current(note)
        self.tabs.add(str(note.oid), note.title or "无标题")

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
        return str(note.oid)

    @Slot(str)
    def openNote(self, oid: str) -> None:
        if not oid or oid == self.currentOid:
            return
        self.flush()
        self._activate(Note.load(self._vault, oid))

    @Slot(str)
    def closeTab(self, oid: str) -> None:
        self.flush()
        row = self.tabs.index_of(oid)
        if row < 0:
            return
        self.tabs.remove(oid)
        if oid != self.currentOid:
            return
        remaining = self.tabs.oids()
        if remaining:
            self._activate(Note.load(self._vault, remaining[min(row, len(remaining) - 1)]))
        else:
            self._set_current(None)

    @Slot(str)
    def deleteNote(self, oid: str) -> None:
        self.flush()
        self._vault.delete(oid)
        self.tabs.remove(oid)
        remaining = self.tabs.oids()
        if self.currentOid == oid or self._current is None:
            if remaining:
                self._activate(Note.load(self._vault, remaining[-1]))
            else:
                self._set_current(None)
        self.notes.reload()

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

    # ---- 标签 ----
    @Slot(str)
    def addTag(self, tag: str) -> None:
        tag = tag.strip()
        if not tag or self._current is None:
            return
        tags = list(self._current.tags)
        if tag in tags:
            return
        tags.append(tag)
        self._current.update(tags=tags)
        self.tagsChanged.emit()
        self.notes.reload()

    @Slot(str)
    def removeTag(self, tag: str) -> None:
        if self._current is None:
            return
        tags = [item for item in self._current.tags if item != tag]
        self._current.update(tags=tags)
        self.tagsChanged.emit()
        self.notes.reload()


def seed_demo(backend: Backend) -> None:
    """给开发/预览用的示例笔记（仅在空库时写入）。"""
    if backend.notes.rowCount() > 0:
        return
    samples = [
        ("存储层设计笔记", "内容先落在本地对象池，再进入索引；块级去重让相同内容只存一份。", ["存储", "设计"]),
        ("布局取舍 v1", "把「收」和「编」分开：收集时零摩擦，整理时再建立关系与归属。", ["设计"]),
        ("QML 外壳草案", "领域栏、工具册、标签工作区、上下文右区、谱系面包屑。", ["客户端"]),
    ]
    for title, text, tags in samples:
        Note.create(backend._vault, text, title=title, tags=tags)
    backend.notes.reload()
    rows = range(backend.notes.rowCount())
    oids = [str(backend.notes.data(backend.notes.index(row, 0), NotesModel.OidRole)) for row in reversed(list(rows))]
    for oid in oids:
        backend.openNote(oid)


def env_vault_root() -> Path:
    return Path(os.environ.get("CAIRN_VAULT", str(DEV_VAULT)))


def env_passphrase() -> str:
    return os.environ.get("CAIRN_DEV_PASSPHRASE", DEV_PASSPHRASE)
