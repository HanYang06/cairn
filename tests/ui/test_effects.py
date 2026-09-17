# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""效果补丁测试：阴影层级。"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel

from cairn.ui.components import Panel
from cairn.ui.effects import apply_elevation, clear_elevation
from cairn.ui.theme import LIGHT, set_elevations

pytestmark = pytest.mark.usefixtures("qapp")


def test_apply_elevation_sets_shadow() -> None:
    label = QLabel("x")
    effect = apply_elevation(label, 2, LIGHT)
    assert isinstance(effect, QGraphicsDropShadowEffect)
    assert effect.blurRadius() == LIGHT.shadow_blur * 2
    assert label.graphicsEffect() is effect


def test_clear_elevation() -> None:
    label = QLabel("x")
    apply_elevation(label, 1, LIGHT)
    clear_elevation(label)
    assert label.graphicsEffect() is None


def test_zero_level_clears() -> None:
    label = QLabel("x")
    apply_elevation(label, 1, LIGHT)
    assert apply_elevation(label, 0, LIGHT) is None
    assert label.graphicsEffect() is None


def test_component_applies_declared_elevation() -> None:
    set_elevations({"Panel": 1})
    try:
        panel = Panel()
        panel.show()
        assert panel.graphicsEffect() is not None
    finally:
        set_elevations({})
