# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""效果补丁：QSS 表达不了的视觉（阴影等）在代码侧实现，参数来自主题令牌。

主题文件里的 ``widget.<类型>.elevation`` 是**声明**，编译成「类名 → 层级」；
真正的阴影由这里用 `QGraphicsDropShadowEffect` 施加（`Component.showEvent` 自动接）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

if TYPE_CHECKING:
    from .theme import Theme


def apply_elevation(
    widget: QWidget,
    level: int,
    theme: Theme,
) -> QGraphicsDropShadowEffect | None:
    """按主题令牌给部件装阴影；``level <= 0`` 表示清除。"""
    if level <= 0:
        widget.setGraphicsEffect(None)  # type: ignore[arg-type]
        return None
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(float(theme.shadow_blur * level))
    effect.setOffset(0.0, float(theme.shadow_offset * level))
    effect.setColor(QColor(theme.shadow_color))
    widget.setGraphicsEffect(effect)
    return effect


def clear_elevation(widget: QWidget) -> None:
    """清除部件的阴影效果。"""
    widget.setGraphicsEffect(None)  # type: ignore[arg-type]


__all__ = ["apply_elevation", "clear_elevation"]
