# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`ListModel` 通用列表模型测试。"""

from __future__ import annotations

from PySide6.QtCore import Qt

from cairn.ui.models import ListModel


def test_roles_and_display() -> None:
    model: ListModel[str] = ListModel(
        [("name", lambda row: row), ("size", len)],
        display="name",
    )
    model.set_rows(["ab", "cdef"])

    assert model.rowCount() == 2
    assert model.row_at(1) == "cdef"
    assert model.row_at(9) is None

    index = model.index(1, 0)
    assert model.data(index, int(Qt.ItemDataRole.DisplayRole)) == "cdef"

    names = model.roleNames()
    assert b"name" in names.values()
    size_role = next(role for role, name in names.items() if name == b"size")
    assert model.data(index, size_role) == 4


def test_display_role_maps_to_named_field() -> None:
    model: ListModel[str] = ListModel([("title", str.upper)], display="title")
    model.set_rows(["hi"])
    index = model.index(0, 0)
    assert model.data(index, int(Qt.ItemDataRole.DisplayRole)) == "HI"
