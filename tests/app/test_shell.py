# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""壳：三带装配、密度切换与真实笔记投影的离屏测试。"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QListView, QMainWindow, QPushButton

from app.win import CairnApp
from app.win.windows.theme import app_theme
from core import Vault
from feature import Note
from ui_tools.core.qt import build_window

pytestmark = pytest.mark.usefixtures("qapp")


def test_shell_window_has_bands(tmp_path) -> None:
    vault = Vault.create(tmp_path / "vault")

    window = build_window(CairnApp(vault))

    assert isinstance(window, QMainWindow)
    assert window.findChild(QListView, "stage") is not None
    assert window.findChild(QPushButton, "density") is not None
    vault.close()


def test_density_toggle_switches_view(tmp_path) -> None:
    vault = Vault.create(tmp_path / "vault")
    window = build_window(CairnApp(vault))

    stage = window.findChild(QListView, "stage")
    button = window.findChild(QPushButton, "density")
    assert stage is not None
    assert button is not None

    assert stage.viewMode() == QListView.ViewMode.IconMode
    button.click()
    assert stage.viewMode() == QListView.ViewMode.ListMode
    vault.close()


def test_stage_shows_real_notes(tmp_path) -> None:
    vault = Vault.create(tmp_path / "vault")
    notes = Note(vault).bind(vault.signal)
    notes.create("hello", title="你好")
    notes.create("world", title="世界")

    window = build_window(CairnApp(vault))

    stage = window.findChild(QListView, "stage")
    assert stage is not None
    assert stage.model() is not None
    assert stage.model().rowCount() == 2
    vault.close()


def test_theme_falls_back_on_broken_file(tmp_path, monkeypatch) -> None:
    (tmp_path / "broken.json").write_text("{ not json", encoding="utf-8")
    monkeypatch.setenv("CAIRN_THEME_DIR", str(tmp_path))

    theme = app_theme("broken")

    assert theme.token("bg")  # 损坏文件退回内置默认，不抛


def test_theme_rejects_path_traversal(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CAIRN_THEME_DIR", str(tmp_path))

    assert app_theme("../../etc/passwd").token("bg")  # 非法名退回内置默认
