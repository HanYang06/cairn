# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ui.component import Button
from ui.core.qt import build
from ui.core.theme import Theme

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

pytestmark = pytest.mark.usefixtures("qapp")


def test_theme_compiles_qss() -> None:
    theme = Theme(
        tokens={"accent": "#123456"},
        styles={
            "widget.button": {"background": "token.accent"},
            "widget.button:hover": {"border_color": "token.accent", "radius": "4px"},
        },
    )

    qss = theme.to_qss()

    assert 'QWidget[cairnClass="button"] {' in qss
    assert "background: #123456;" in qss
    assert 'QWidget[cairnClass="button"]:hover {' in qss
    assert "border-color: #123456;" in qss
    assert "border-radius: 4px;" in qss


def test_theme_apply(qapp: QApplication) -> None:
    theme = Theme(styles={"widget.label": {"color": "#fff"}})

    theme.apply(qapp)

    assert 'cairnClass="label"' in qapp.styleSheet()


def test_widgets_tagged_with_cairn_class() -> None:
    widget = build(Button("x"))

    assert widget.property("cairnClass") == "button"
