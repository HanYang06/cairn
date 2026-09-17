# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`SessionBridge`：把内核变更翻译成 Qt 信号（唯一翻译点）。

内核事件可能一次写入触发多条；这里用事件循环空闲合并成**一次**信号，避免重复刷新。
数据流始终单向：内核 → Session → Bridge → Model/Component。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Signal, Slot

if TYPE_CHECKING:
    from .session import Session
    from .signal import Subscription


class SessionBridge(QObject):
    """`Session` → Qt 信号；合并同一轮事件循环内的变更。"""

    changed = Signal()
    object_changed = Signal(str)

    def __init__(self, session: Session, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._pending = False
        self._subscription: Subscription = session.changed.connect(self._on_change)

    def _on_change(self, _oid: str) -> None:
        if not self._pending:
            self._pending = True
            QTimer.singleShot(0, self.flush)

    @Slot()
    def flush(self) -> None:
        """合并并发出挂起的变更（事件循环空闲时自动调用，测试可手动调）。"""
        self._pending = False
        for oid in self._session.take_changed():
            self.object_changed.emit(oid)
        self.changed.emit()

    def dispose(self) -> None:
        """断开与 Session 的连接。"""
        self._subscription.cancel()


__all__ = ["SessionBridge"]
