# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Windows 应用入口：实际 UI 载体（从内核取数据、用 `ui_tools` 组装窗口）。"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core import Vault
from ui_tools.core.qt import build_window

from .. import build


def main() -> int:
    """启动 Windows 桌面应用。"""
    qapp = QApplication.instance() or QApplication([])
    root = Path(os.environ.get("CAIRN_VAULT", str(Path.cwd() / "vault")))
    vault = Vault.load(root) if root.exists() else Vault.create(root)
    build_window(build(vault)).show()
    return qapp.exec()


if __name__ == "__main__":
    raise SystemExit(main())
