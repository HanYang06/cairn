# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton

from ui_tools.component import Button, Chip, Divider, Field, Label
from ui_tools.core import vocabulary
from ui_tools.core.qt import build

pytestmark = pytest.mark.usefixtures("qapp")


def test_label_builds_qlabel() -> None:
    widget = build(Label("hi"))

    assert isinstance(widget, QLabel)
    assert widget.text() == "hi"


def test_button_builds_qpushbutton() -> None:
    widget = build(Button("save"))

    assert isinstance(widget, QPushButton)
    assert widget.text() == "save"


def test_field_builds_qlineedit_with_placeholder() -> None:
    widget = build(Field(placeholder="name"))

    assert isinstance(widget, QLineEdit)
    assert widget.placeholderText() == "name"


def test_divider_and_chip() -> None:
    assert isinstance(build(Divider()), QFrame)

    chip = build(Chip("tag"))
    assert isinstance(chip, QLabel)
    assert chip.text() == "tag"


def test_vocabulary_includes_atoms() -> None:
    vocab = vocabulary()

    assert vocab["button"]["states"] == ["checked", "disabled", "hover", "pressed"]
    assert "color" in vocab["label"]["stylable"]
