# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Cairn 桌面应用入口（QtWidgets）。

用法：
    uv run cairn             # 启动
    uv run cairn --smoke     # 冒烟：0.8 秒后自动退出（自检 / CI）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from ..core import Vault
from ..core.store import CATALOG_NAME
from .root import App
from .theme.manager import ThemeManager
from .window import MainWindow

DEV_PASSPHRASE = "cairn-dev"  # noqa: S105 — 开发期固定口令，非生产密钥


def _default_vault_root() -> Path:
    """源码 checkout 时把开发库放项目下；否则回落到用户目录。"""
    repo = Path(__file__).resolve().parents[3]
    if (repo / "pyproject.toml").is_file():
        return repo / "vault"
    return Path.home() / ".cairn-dev"


DEV_VAULT = _default_vault_root()


def env_vault_root() -> Path:
    """开发库根目录：``CAIRN_VAULT`` 覆盖，否则用项目内 ``vault/``。"""
    return Path(os.environ.get("CAIRN_VAULT", str(DEV_VAULT)))


def env_passphrase() -> str:
    """开发口令：``CAIRN_DEV_PASSPHRASE`` 覆盖，否则用内置默认值。"""
    return os.environ.get("CAIRN_DEV_PASSPHRASE", DEV_PASSPHRASE)


def open_vault(root: Path | str, passphrase: str = DEV_PASSPHRASE) -> Vault:
    """打开或创建库（开发期用固定口令；正式解锁流程后续再补）。"""
    root = Path(root)
    if (root / CATALOG_NAME).exists():
        vault = Vault.load(root)
        vault.unlock(passphrase)
        return vault
    return Vault.create(root, passphrase)


def _apply_font(app: QApplication) -> None:
    font = QFont()
    font.setFamilies(
        [
            "Sarasa Mono SC",
            "Noto Sans Mono CJK SC",
            "Cascadia Mono",
            "Consolas",
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "SimSun",
            "monospace",
        ]
    )
    app.setFont(font)


def main(argv: list[str] | None = None) -> int:
    """启动桌面应用；返回进程退出码。"""
    args = list(sys.argv if argv is None else argv)
    app = QApplication(args)
    app.setApplicationName("Cairn")
    app.setOrganizationName("Cairn")
    _apply_font(app)

    try:
        vault = open_vault(env_vault_root(), env_passphrase())
    except Exception:  # noqa: BLE001 — 顶层入口：启动失败统一以退出码 1 结束
        return 1

    root = App(vault)
    ThemeManager(app).apply_default()
    window = MainWindow(root)
    app.aboutToQuit.connect(root.shutdown)
    window.show()

    if "--smoke" in args:
        QTimer.singleShot(800, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
