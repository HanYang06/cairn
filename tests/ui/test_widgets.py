# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Widgets 部件与外壳的进程内测试（离屏 QApplication）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QApplication, QSplitter

from cairn.core import Vault
from cairn.domains import Note
from cairn.ui.components import Component, InspectorPanel, ListPanel, Panel, Stack
from cairn.ui.root import App
from cairn.ui.theme import LIGHT, current_theme, set_current_theme
from cairn.ui.theme.manager import ThemeManager
from cairn.ui.window import MainWindow, Shell

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.usefixtures("qapp")


def test_component_defaults_object_name() -> None:
    widget = Component()
    assert widget.objectName() == "Component"
    assert widget.theme is current_theme()


def test_panel_title_and_body() -> None:
    panel = Panel("标题")
    panel.set_title("改名")
    assert panel.body.objectName() == "PanelBody"
    assert panel.theme is current_theme()


def test_theme_manager_applies_and_tracks(qapp: QApplication) -> None:
    manager = ThemeManager(qapp)
    manager.apply(LIGHT)
    assert manager.current is LIGHT
    assert current_theme() is LIGHT
    assert LIGHT.accent in qapp.styleSheet()


def test_shell_has_three_panes(tmp_path: Path) -> None:
    root = App(Vault.create(tmp_path / "vault"))
    shell = Shell(root)
    assert isinstance(shell, Component)
    assert isinstance(shell.center, Stack)
    assert isinstance(shell.inspector, InspectorPanel)
    splitter = shell.findChild(QSplitter, "ShellSplit")
    assert splitter is not None
    assert splitter.count() == 3
    root.shutdown()


def test_shell_activity_switches_pages(tmp_path: Path) -> None:
    root = App(Vault.create(tmp_path / "vault"))
    shell = Shell(root)
    assert shell.center.stack.currentIndex() == 0
    shell.activity.activated.emit("projects")
    assert shell.center.stack.currentIndex() == 1
    root.shutdown()


def test_shell_navigator_binds_notes_model(tmp_path: Path) -> None:
    root = App(Vault.create(tmp_path / "vault"))
    shell = Shell(root)
    assert isinstance(shell.navigator, ListPanel)
    assert shell.navigator.view.model() is root.notes
    root.shutdown()


def test_app_notes_model_reflects_vault(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    root = App(vault)
    assert root.notes.rowCount() == 0

    note = Note.create(vault, "正文", title="甲")
    root.bridge.flush()
    assert root.notes.rowCount() == 1
    assert root.note_title(str(note.oid)) == "甲"

    root.shutdown()


def test_app_open_note_populates_properties(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    root = App(vault)
    note = Note.create(vault, "正文", title="甲")
    root.bridge.flush()

    root.open_note(str(note.oid))
    assert root.current_oid == str(note.oid)
    rows = [root.properties.row_at(i) for i in range(root.properties.rowCount())]
    assert any(row is not None and row.pid == "favorite" for row in rows)

    root.open_note("")
    assert root.properties.rowCount() == 0
    root.shutdown()


def test_shell_open_note_updates_app(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    root = App(vault)
    note = Note.create(vault, "正文", title="甲")
    root.bridge.flush()

    shell = Shell(root)
    shell.navigator.activated.emit(str(note.oid))
    assert root.current_oid == str(note.oid)
    root.shutdown()


def test_main_window_central_widget(tmp_path: Path) -> None:
    root = App(Vault.create(tmp_path / "vault"))
    window = MainWindow(root)
    assert isinstance(window.centralWidget(), Shell)
    window.close()
    root.shutdown()


def test_theme_state_roundtrip() -> None:
    original = current_theme()
    try:
        set_current_theme(LIGHT)
        assert current_theme() is LIGHT
    finally:
        set_current_theme(original)
