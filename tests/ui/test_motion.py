# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""动画封装测试：默认取主题令牌、`reduce_motion` 降为 0、fade 自动建效果。"""

from __future__ import annotations

from dataclasses import replace

import pytest
from PySide6.QtCore import QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel

from cairn.ui.motion import fade, make_animation
from cairn.ui.theme import current_theme, set_current_theme

pytestmark = pytest.mark.usefixtures("qapp")


def test_make_animation_uses_theme_defaults() -> None:
    animation = make_animation(QLabel("x"), "windowOpacity", 0.5, duration=200)
    assert animation.duration() == 200
    assert animation.endValue() == 0.5
    assert animation.easingCurve().type() == QEasingCurve.Type.OutQuad


def test_reduce_motion_forces_zero_duration() -> None:
    original = current_theme()
    try:
        set_current_theme(replace(original, reduce_motion=True))
        animation = make_animation(QLabel("x"), "windowOpacity", 0.0, duration=999)
        assert animation.duration() == 0
    finally:
        set_current_theme(original)


def test_fade_prepares_opacity_effect() -> None:
    label = QLabel("x")
    animation = fade(label, to=0.5)
    assert isinstance(label.graphicsEffect(), QGraphicsOpacityEffect)
    assert animation.endValue() == 0.5
