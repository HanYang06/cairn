# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""桌面入口：打开库、组装 UI、启动。

领域树的静态声明在应用内核 `kernel.py`（那里才认识领域）；本文件只做 boot。
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core import Vault
from kernel import Kernel
from ui.core import App, Session
from ui.core.qt import build_window
from ui.note import NoteFacet


def build(vault: Vault) -> App:
    """由一个库组装 UI。"""
    kernel = Kernel(vault)
    session = Session(kernel.signal)
    app = App(session)
    app.mount(NoteFacet(kernel.feature.Note, session))
    return app


def main() -> int:
    """桌面入口。"""
    qapp = QApplication.instance() or QApplication([])
    root = Path(os.environ.get("CAIRN_VAULT", str(Path.cwd() / "vault")))
    vault = Vault.load(root) if root.exists() else Vault.create(root)
    build_window(build(vault)).show()
    return qapp.exec()


if __name__ == "__main__":
    raise SystemExit(main())
