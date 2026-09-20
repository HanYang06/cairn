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


class _Feature:
    Note: object

    def __init__(self, note: object) -> None:
        self.Note = note


def test_note_facet_builds_window(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    notes = Note(vault).bind(vault.signal)
    vault.signal.feature = _Feature(notes)
    notes.create("hello world", title="Hi")

    session = Session(vault.signal)
    app = App(session)
    facet = NoteFacet(notes, session)
    app.mount(facet)

    window = build_window(app)

    assert isinstance(window, QMainWindow)
    assert facet.name == "note"
    # 域服务静态挂在主干容器上，Facet 拿到的是同一个对象
    assert vault.signal.feature.Note is notes
    vault.close()
