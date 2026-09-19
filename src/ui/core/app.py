# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 内核 · 组合根（Qt-free 起始）。

`App` 持有 `Session`（后续再挂命令表 / facade）。**不带 Qt 依赖**：带 QObject 的外壳
在重建的后续阶段另加，避免内核期就被 Qt 绑死。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import Session


class App:
    """组合根：UI 的唯一装配入口。"""

    def __init__(self, session: Session) -> None:
        self.session = session


__all__ = ["App"]
