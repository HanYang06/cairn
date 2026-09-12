# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""把主题应用到 QApplication。

Qt 相关逻辑隔离在此，``cairn.ui.theme`` 本体保持无 Qt 依赖。
"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from .qss import build_qss
from .tokens import Theme


class ThemeManager:
    """持有当前主题，负责把令牌渲染成 QSS 并挂到应用上。"""

    def __init__(self, app: QApplication) -> None:
        self._app = app
        self._current: Theme | None = None

    @property
    def current(self) -> Theme | None:
        return self._current

    def apply(self, theme: Theme) -> None:
        self._app.setStyleSheet(build_qss(theme))
        self._current = theme
