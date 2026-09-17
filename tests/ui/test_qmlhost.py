# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`QmlView` QML 岛承载器测试。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cairn.ui.qmlhost import QmlView

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.usefixtures("qapp")


def test_qml_view_loads_source(tmp_path: Path) -> None:
    source = tmp_path / "Island.qml"
    source.write_text("import QtQuick\nItem { width: 10; height: 10 }\n", encoding="utf-8")
    view = QmlView(source, context={"answer": 42})
    assert view.view.objectName() == "QmlView"
    assert view.root_object() is not None
