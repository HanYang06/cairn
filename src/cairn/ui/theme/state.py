# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""当前主题状态：组件读令牌的唯一入口（无 Qt 依赖）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .themes import LIGHT

if TYPE_CHECKING:
    from .tokens import Theme


class _ThemeState:
    __slots__ = ("theme",)

    def __init__(self, theme: Theme) -> None:
        self.theme = theme


_state = _ThemeState(LIGHT)


def current_theme() -> Theme:
    """当前生效的主题令牌（供组件读取，不直接改）。"""
    return _state.theme


def set_current_theme(theme: Theme) -> None:
    """切换当前主题（由 ``ThemeManager`` 在应用 QSS 后调用）。"""
    _state.theme = theme


__all__ = ["current_theme", "set_current_theme"]
