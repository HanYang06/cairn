# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 测试共享设置：离屏 QApplication（会话级），避免需要显示器。"""

from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QSG_RHI_BACKEND", "software")


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """整个测试会话共享一个 QApplication（Qt 只允许一个）。"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    assert isinstance(app, QApplication)
    return app
