# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QMainWindow

from app.win import CairnApp
from app.win.backend import fmt_time
from core import CairnError, Vault
from ui_tools.core.qt import build_window

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.usefixtures("qapp")


def test_app_builds_window(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")

    app = CairnApp(vault)
    window = build_window(app)

    assert isinstance(window, QMainWindow)
    vault.close()


def test_app_open_creates_then_loads(tmp_path: Path) -> None:
    root = tmp_path / "vault"

    CairnApp.open(root).close()  # 不存在 → 创建
    CairnApp.open(root).close()  # 已存在 → 加载


def test_app_open_propagates_newer_catalog(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    vault = Vault.create(root)
    vault.bucket.catalog.set_meta("catalog_version", "999")
    vault.bucket.catalog.commit()
    vault.close()

    with pytest.raises(CairnError, match="目录版本过新"):
        CairnApp.open(root)  # 不得掩盖成「桶已存在」


def test_fmt_time_tolerates_bad_values() -> None:
    assert fmt_time(0) == ""
    assert fmt_time(-5) == ""
    assert fmt_time(10**20) == ""  # 超出 datetime 范围不崩
