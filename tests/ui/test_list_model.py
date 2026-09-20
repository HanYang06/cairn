# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QListView

from core import Vault
from feature import Note
from ui.component import List
from ui.core import App, Facet, Session
from ui.core.qt import WindowHost
from ui.layout import VBox

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.usefixtures("qapp")


def test_list_refreshes_on_change(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    notes = vault.signal.register(Note(vault))
    notes.create("a", title="A")

    session = Session(vault.signal)
    model = session.model(lambda: [str(data.title) for data in notes.list_notes()])

    facet = Facet(object(), name="note")
    facet.set(VBox)
    facet.add(List(model))
    app = App(session)
    app.mount(facet)

    host = WindowHost(app)
    view = host.window.findChild(QListView)
    assert view is not None
    assert view.model() is not None
    assert view.model().rowCount() == 1

    notes.create("b", title="B")
    assert view.model().rowCount() == 2

    vault.close()
