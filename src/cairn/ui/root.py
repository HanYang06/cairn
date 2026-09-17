# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`App`：应用组合根。

它是 UI 唯一的依赖入口：拥有库与 `Session` / `SessionBridge`（后续还有 facade / 命令表），
由装配层显式注入给各部件；部件不直接碰 `Vault`。见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject

from .bridge import SessionBridge
from .session import Session

if TYPE_CHECKING:
    from ..core import Vault


class App(QObject):
    """应用组合根：持有状态镜像与变更桥。"""

    def __init__(self, vault: Vault, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.vault = vault
        self.session = Session(vault)
        self.bridge = SessionBridge(self.session, self)

    def shutdown(self) -> None:
        """退出前收口：断开桥与订阅，关闭库。"""
        self.bridge.dispose()
        self.session.close()
        self.vault.close()


__all__ = ["App"]
