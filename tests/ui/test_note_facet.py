# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QMainWindow

from core import Vault
from feature import Note
from ui.core import App, Session
from ui.core.qt import build_window
from ui.note import NoteFacet

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.usefixtures("qapp")


def test_note_facet_builds_window(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    notes = vault.signal.register(Note(vault))
    notes.create("hello world", title="Hi")

    session = Session(vault.signal)
    app = App(session)
    facet = NoteFacet(notes, session)
    app.mount(facet)

    window = build_window(app)

    assert isinstance(window, QMainWindow)
    assert facet.name == "note"
    # 域服务注册在主干的地址树上，Facet 拿到的是同一个对象
    assert vault.signal.feature.Note is notes
    vault.close()
