# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QMainWindow

from ui_tools.app import build_demo

pytestmark = pytest.mark.usefixtures("qapp")


def test_build_demo_window() -> None:
    window = build_demo()

    assert isinstance(window, QMainWindow)
    assert window.centralWidget() is not None
