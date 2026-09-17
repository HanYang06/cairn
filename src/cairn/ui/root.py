# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`App`：应用组合根。

它是 UI 唯一的依赖入口：拥有库、`Session` / `SessionBridge` 与共享模型；
由装配层显式注入给各部件。部件不直接碰 `Vault`。见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject

from .bridge import SessionBridge
from .models import ListModel
from .session import Session

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..core import Vault
    from .rows import NoteRow


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


class App(QObject):
    """应用组合根：状态镜像、变更桥与共享模型。"""

    def __init__(self, vault: Vault, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.vault = vault
        self.session = Session(vault)
        self.bridge = SessionBridge(self.session, self)
        self.notes: ListModel[NoteRow] = ListModel(_note_fields(), display="title")
        self.bridge.changed.connect(self.reload_notes)
        self.reload_notes()

    def reload_notes(self) -> None:
        """按当前 Session 投影刷新笔记列表模型。"""
        self.notes.set_rows(self.session.note_rows())

    def note_title(self, oid: str) -> str:
        """取一篇笔记的标题（供界面展示）。"""
        try:
            note = self.session.note(oid)
        except Exception:  # noqa: BLE001 — 缺失 / 损坏不崩界面
            return "（缺失）"
        return note.title or "未命名"

    def shutdown(self) -> None:
        """退出前收口：断开桥与订阅，关闭库。"""
        self.bridge.dispose()
        self.session.close()
        self.vault.close()


__all__ = ["App"]
