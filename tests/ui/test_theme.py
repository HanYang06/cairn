# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ui_tools.component import Button, Surface
from ui_tools.core import UiError
from ui_tools.core.qt import build
from ui_tools.core.theme import Theme, load_theme

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


def test_dangling_token_reference_raises() -> None:
    theme = Theme(styles={"widget.label": {"color": "token.nope"}})

    with pytest.raises(KeyError, match="未知 token"):
        theme.to_qss()


def test_selector_group_compiles_each() -> None:
    theme = Theme(styles={"widget.button, widget.label": {"color": "#fff"}})

    qss = theme.to_qss()

    assert 'QWidget[cairnClass="button"]' in qss
    assert 'QWidget[cairnClass="label"]' in qss


def test_theme_rejects_bool_and_none_values() -> None:
    with pytest.raises(ValueError, match="主题值非法"):
        Theme(tokens={"x": True})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="主题值非法"):
        Theme(tokens={"x": None})  # type: ignore[dict-item]


def test_load_theme_rejects_non_object(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[1, 2]", encoding="utf-8")

    with pytest.raises(TypeError, match="JSON 对象"):
        load_theme(path)


def test_load_theme_rejects_falsy_non_object_section(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"token": [], "style": {}}', encoding="utf-8")

    with pytest.raises(TypeError, match="token"):
        load_theme(path)


def test_shadow_alpha_must_be_int() -> None:
    theme = Theme(tokens={"shadow_alpha": "abc"})

    with pytest.raises(UiError, match="shadow_alpha"):
        build(Surface(elevated=True), theme)
