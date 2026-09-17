# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""结构件测试：意图信号与递归组合。"""

from __future__ import annotations

import pytest

from cairn.ui.components import ListPanel, Section, Toolbar
from cairn.ui.models import ListModel

pytestmark = pytest.mark.usefixtures("qapp")


def test_toolbar_emits_triggered_action() -> None:
    got: list[str] = []
    bar = Toolbar()
    bar.triggered.connect(got.append)
    button = bar.add_action("new", "\ue710", tip="新建")
    bar.add_action("del", "\ue74d")
    button.control.click()
    assert got == ["new"]


def test_composites_nest_arbitrarily() -> None:
    outer = Section("外")
    inner = Section("内")
    outer.body.add(inner)
    assert inner.parent() is outer.body


def test_list_panel_binds_model_and_emits_key() -> None:
    panel = ListPanel("笔记", key_of=lambda row: row)
    model: ListModel[str] = ListModel([("title", str)], display="title")
    model.set_rows(["a", "b"])
    panel.set_model(model)
    got: list[str] = []
    panel.activated.connect(got.append)

    assert panel.view.model() is model
    panel._on_activated(model.index(1, 0))
    assert got == ["b"]
