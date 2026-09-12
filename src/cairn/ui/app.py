# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Cairn 桌面应用入口（Qt Quick / QML）。

用法：
    uv run cairn            # 正常启动
    uv run cairn --smoke    # 冒烟：0.8 秒后自动退出（用于自检/CI）
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

QML_DIR = Path(__file__).resolve().parent / "qml"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    app = QGuiApplication(args)
    app.setApplicationName("Cairn")
    app.setOrganizationName("Cairn")

    engine = QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        print("QML 加载失败", file=sys.stderr)
        return 1

    if "--smoke" in args:
        QTimer.singleShot(800, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
