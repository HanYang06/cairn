# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QMainWindow

from app import build
from core import Vault
from ui_tools.core.qt import build_window

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.usefixtures("qapp")


def test_app_builds_window(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")

    app = build(vault)
    window = build_window(app)

    assert isinstance(window, QMainWindow)
    vault.close()
