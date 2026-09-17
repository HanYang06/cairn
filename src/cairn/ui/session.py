# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`Session`：内核状态在 UI 侧的**只读镜像**（Qt-free）。

职责：
- 订阅内核事件，把「哪一块变了」记下来，并作废投影缓存；
- 提供类型化的投影（当前是笔记行）；
- 用极简 `Signal` 广播变更，交给桥接层翻译成 Qt 信号。

不缓存可变领域对象（编辑中的实例由编辑器自己持有），避免与写入互相打架。
"""

from __future__ import annotations

from ..core import Event, ObjectDeleted, ObjectPut, Vault
from ..domains import Note
from .rows import NoteRow
from .signal import Cancellable, Signal


class Session:
    """内核状态镜像：投影缓存 + 变更信号。"""

    def __init__(self, vault: Vault) -> None:
        self._vault = vault
        self._rows: list[NoteRow] | None = None
        self._changed: set[str] = set()
        self.changed = Signal()
        self._subscriptions: list[Cancellable] = [
            vault.subscribe(self._on_event, event_type=ObjectPut),
            vault.subscribe(self._on_event, event_type=ObjectDeleted),
        ]

    @property
    def vault(self) -> Vault:
        """底层库（facade / 编辑器需要写时用）。"""
        return self._vault

    # ---- 读投影 ----
    def note_rows(self) -> list[NoteRow]:
        """笔记行投影（按更新时间倒序），带缓存，事件驱动作废。"""
        if self._rows is None:
            self._rows = self._build_rows()
        return list(self._rows)

    def note(self, oid: str) -> Note:
        """按需加载一篇笔记（用于编辑，不进缓存）。"""
        return Note.load(self._vault, oid)

    def _build_rows(self) -> list[NoteRow]:
        infos = sorted(
            self._vault.iter(type=Note.kind),
            key=lambda info: info.updated,
            reverse=True,
        )
        rows: list[NoteRow] = []
        for info in infos:
            try:
                rows.append(NoteRow.from_note(Note.load(self._vault, info.oid)))
            except Exception:  # noqa: BLE001, S112 — 单篇坏数据不拖垮整个列表
                continue
        return rows

    # ---- 变更 ----
    def _on_event(self, event: Event) -> None:
        if not isinstance(event, (ObjectPut, ObjectDeleted)):
            return
        oid = str(event.oid)
        self._rows = None
        self._changed.add(oid)
        self.changed.emit(oid)

    def take_changed(self) -> list[str]:
        """取出并清空自上次以来的变更 oid（供桥接层合并后发信号）。"""
        changed = sorted(self._changed)
        self._changed.clear()
        return changed

    def invalidate(self) -> None:
        """手动作废投影（用于非事件驱动的外部改动）。"""
        self._rows = None
        self.changed.emit("")

    def close(self) -> None:
        """退订内核事件，断开与库的联系。"""
        for subscription in self._subscriptions:
            subscription.cancel()
        self._subscriptions.clear()


__all__ = ["Session"]
