# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""把主题应用到 QApplication。

Qt 相关逻辑隔离在此，``cairn.ui.theme`` 本体保持无 Qt 依赖。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .loader import ThemeFile, list_themes, load_theme
from .qss import build_elevations, build_qss, compile_theme
from .state import set_current_theme, set_elevations
from .themes import LIGHT

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

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
        """应用令牌主题（内置 / 直接构造的 `Theme`）。"""
        self._app.setStyleSheet(build_qss(theme))
        set_current_theme(theme)
        set_elevations({})
        self._current = theme

    def apply_theme(self, theme_file: ThemeFile) -> None:
        """应用一个主题包（令牌 + 部件规则 + 阴影效果）。"""
        self._app.setStyleSheet(compile_theme(theme_file))
        set_current_theme(theme_file.theme)
        set_elevations(build_elevations(theme_file.rules))
        self._current = theme_file.theme

    def apply_default(self) -> None:
        """优先用 `config/theme` 里的 GitHub 主题；找不到回落到内置亮色。"""
        themes = list_themes()
        for name in ("github-light", "github-dark"):
            path = themes.get(name)
            if path is not None:
                self.apply_theme(load_theme(path))
                return
        self.apply(LIGHT)


__all__ = ["ThemeManager"]
