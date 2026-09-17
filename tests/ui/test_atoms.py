# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""原子组件测试：意图信号与基本读写。"""

from __future__ import annotations

import pytest

from cairn.ui.components import (
    Button,
    Chip,
    Divider,
    Field,
    IconButton,
    Label,
    Section,
    ToggleSwitch,
)

pytestmark = pytest.mark.usefixtures("qapp")


def test_button_emits_clicked() -> None:
    seen: list[int] = []
    button = Button("确定", on_click=lambda: seen.append(1))
    button.control.click()
    assert seen == [1]


def test_icon_button_emits_clicked() -> None:
    seen: list[int] = []
    button = IconButton("\ue710", tip="新建", on_click=lambda: seen.append(1))
    button.control.click()
    assert seen == [1]


def test_label_text_roundtrip() -> None:
    label = Label("标题")
    label.text = "改名"
    assert label.text == "改名"
    assert label.control.text() == "改名"


def test_field_submits_value() -> None:
    got: list[str] = []
    field = Field("名字", placeholder="请输入")
    field.submitted.connect(got.append)
    field.value = "石头"
    field.edit.returnPressed.emit()
    assert got == ["石头"]


def test_section_holds_body() -> None:
    section = Section("属性")
    section.body.add(Label("x"))
    section.set_title("改名")
    layout = section.body.layout()
    assert layout is not None
    assert layout.count() == 1


def test_chip_emits_clicked() -> None:
    seen: list[int] = []
    chip = Chip("标签", on_click=lambda: seen.append(1))
    chip.control.click()
    assert seen == [1]


def test_toggle_switch_emits_toggled() -> None:
    got: list[bool] = []
    switch = ToggleSwitch()
    switch.toggled.connect(got.append)
    switch.checked = True
    assert got == [True]
    assert switch.checked is True


def test_divider_orientation() -> None:
    assert Divider().maximumHeight() == 1
    assert Divider(vertical=True).maximumWidth() == 1
