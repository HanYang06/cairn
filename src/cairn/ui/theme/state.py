# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""当前主题状态：组件读令牌 / 效果配置的唯一入口（无 Qt 依赖）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .themes import LIGHT

if TYPE_CHECKING:
    from .tokens import Theme


class _ThemeState:
    __slots__ = ("elevations", "theme")

    def __init__(self, theme: Theme) -> None:
        self.theme = theme
        self.elevations: dict[str, int] = {}


_state = _ThemeState(LIGHT)


def current_theme() -> Theme:
    """当前生效的主题令牌（供组件读取，不直接改）。"""
    return _state.theme


def set_current_theme(theme: Theme) -> None:
    """切换当前主题（由 ``ThemeManager`` 在应用 QSS 后调用）。"""
    _state.theme = theme


def set_elevations(mapping: dict[str, int]) -> None:
    """记录各部件类的阴影层级（由主题配置编译而来）。"""
    _state.elevations = dict(mapping)


def current_elevation(class_name: str) -> int:
    """某个部件类当前配置的阴影层级（0 表示无）。"""
    return _state.elevations.get(class_name, 0)


__all__ = [
    "current_elevation",
    "current_theme",
    "set_current_theme",
    "set_elevations",
]
