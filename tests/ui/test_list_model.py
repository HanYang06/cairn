# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QListView

from tests.conftest import make_kernel
from ui_tools.component import List
from ui_tools.core import App, Facet, Session, Slot
from ui_tools.core.qt import WindowHost
from ui_tools.layout import VBox

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.usefixtures("qapp")


def test_list_refreshes_on_change(tmp_path: Path) -> None:
    core = make_kernel(tmp_path)
    notes = core.role("note")
    notes.create("a", title="A")

    session = Session(core.signal)
    model = session.model(lambda: [str(data.title) for data in notes.list_notes()])

    facet = Facet(object(), name="note")
    facet.set(VBox)
    facet.add(List(model))
    app = App(session)
    app.root.add(Slot("main", expects="page"))
    app.add(facet)

    host = WindowHost(app)
    view = host.window.findChild(QListView)
    assert view is not None
    assert view.model() is not None
    assert view.model().rowCount() == 1

    notes.create("b", title="B")
    assert view.model().rowCount() == 2

    core.close()
