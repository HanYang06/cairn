# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Qt 桥：把 `Session` 的变更转成 Qt 信号。

内核 Qt-free；只有这里（与本包其它 `qt*` 模块）依赖 PySide6。
`ui.core` 不 eager 导入本模块，故未装 Qt 时内核仍可导入。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from .session import Session


class Bridge(QObject):
    """`Session` 变更 → Qt 信号。"""

    changed = Signal(object)

    def __init__(self, session: Session, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._cancel = session.watch(self._on_event)
        # C++ 对象被销毁时自动退订，避免回调打到已删除的 QObject。
        self.destroyed.connect(self._on_destroyed)

    def _on_event(self, event: object) -> None:
        self.changed.emit(event)

    def _on_destroyed(self, _obj: object = None) -> None:
        self.close()

    def close(self) -> None:
        """断开与 Session 的观察。"""
        self._cancel()


__all__ = ["Bridge"]
