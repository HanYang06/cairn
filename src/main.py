# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""桌面入口（组合根）：打开库、注册领域服务、组装 UI。

**只有这里认识领域**（构造 `Note` 并注入给 `Facet`）；`ui/` 内不 import `feature`。
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core import Vault
from feature import Note
from ui.core import App, Session
from ui.core.qt import build_window
from ui.note import NoteFacet


def build(vault: Vault) -> App:
    """由一个库组装 UI 组合根。"""
    notes = vault.signal.register(Note(vault))
    session = Session(vault.signal)
    app = App(session)
    app.mount(NoteFacet(notes, session))
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
