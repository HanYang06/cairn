# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""动画封装：把「产生一个动画」从「Qt 能做但很绕」变成一行。

- 时长 / 缓动走主题令牌，`reduce_motion` 时自动降为 0（即时）；
- `animate` 起动画并自动回收；`fade` 免去手建 `QGraphicsOpacityEffect`。

只包高频、成熟的几种用法，不做通用动画引擎。见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QPropertyAnimation,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from .theme import current_theme

_EASING: dict[str, QEasingCurve.Type] = {
    "linear": QEasingCurve.Type.Linear,
    "inQuad": QEasingCurve.Type.InQuad,
    "outQuad": QEasingCurve.Type.OutQuad,
    "inOutQuad": QEasingCurve.Type.InOutQuad,
    "outCubic": QEasingCurve.Type.OutCubic,
}


def resolve_duration(duration: int | None) -> int:
    """解析时长：显式值优先，否则用主题基础时长；``reduce_motion`` 时一律 0。"""
    theme = current_theme()
    if theme.reduce_motion:
        return 0
    return theme.dur_base if duration is None else duration


def make_animation(  # noqa: PLR0913 — 动画参数面：目标 / 属性 / 目标值 / 时长 / 起始 / 缓动
    target: QObject,
    prop: str,
    to: Any,
    *,
    duration: int | None = None,
    start: Any = None,
    easing: str | None = None,
) -> QPropertyAnimation:
    """构造（但不启动）一个属性动画；时长 / 缓动默认取主题令牌。"""
    animation = QPropertyAnimation(target, prop.encode())
    animation.setDuration(resolve_duration(duration))
    if start is not None:
        animation.setStartValue(start)
    animation.setEndValue(to)
    curve = easing or current_theme().easing
    animation.setEasingCurve(_EASING.get(curve, QEasingCurve.Type.OutQuad))
    return animation


def animate(  # noqa: PLR0913 — 与 make_animation 同参数面
    target: QObject,
    prop: str,
    to: Any,
    *,
    duration: int | None = None,
    start: Any = None,
    easing: str | None = None,
) -> QPropertyAnimation:
    """构造并启动一个属性动画（结束后自动回收）。"""
    animation = make_animation(target, prop, to, duration=duration, start=start, easing=easing)
    animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation


def fade(
    widget: QWidget,
    *,
    to: float = 1.0,
    duration: int | None = None,
) -> QPropertyAnimation:
    """淡入 / 淡出；自动准备透明度效果。"""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    return animate(effect, "opacity", to, duration=duration)


__all__ = ["animate", "fade", "make_animation", "resolve_duration"]
