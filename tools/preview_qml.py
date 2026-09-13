# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""离屏渲染 QML 界面为 PNG，供设计评审使用。

用法：
    uv run python tools/preview_qml.py [页面.qml] [输出.png] [宽] [高] [键=值 ...]

例：
    uv run python tools/preview_qml.py Shell.qml out.png 1440 900 navMode=projects
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

if os.environ.get("CAIRN_PREVIEW_OFFSCREEN"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QSG_RHI_BACKEND", "software")

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView

from cairn.ui.backend import Backend, open_vault, seed_demo

ROOT = Path(__file__).resolve().parents[1]
QML_ROOT = ROOT / "src" / "cairn" / "ui" / "qml"


def main(argv: list[str]) -> int:
    page = "Shell.qml"
    out = ROOT / "build" / "ui_preview.png"
    width, height = 1440, 900
    numbers: list[int] = []
    props: dict[str, str] = {}
    for arg in argv[1:]:
        if arg.endswith(".qml"):
            page = arg
        elif arg.endswith(".png"):
            out = Path(arg)
        elif arg.isdigit():
            numbers.append(int(arg))
        elif "=" in arg:
            key, value = arg.split("=", 1)
            props[key] = value
    if numbers:
        width = numbers[0]
    if len(numbers) > 1:
        height = numbers[1]
    out.parent.mkdir(parents=True, exist_ok=True)

    app = QGuiApplication(argv[:1])

    preview_root = Path(tempfile.gettempdir()) / "cairn-preview"
    if preview_root.exists():
        shutil.rmtree(preview_root, ignore_errors=True)
    backend = Backend(open_vault(preview_root, "preview-pass"))
    seed_demo(backend)

    view = QQuickView()
    view.engine().rootContext().setContextProperty("backend", backend)
    view.engine().rootContext().setContextProperty("notesModel", backend.notes)
    view.engine().rootContext().setContextProperty("tabsModel", backend.tabs)
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(str(QML_ROOT / page)))
    if view.status() == QQuickView.Error:
        for error in view.errors():
            print(error.toString(), file=sys.stderr)
        return 1

    root = view.rootObject()
    for key, value in props.items():
        if root is not None:
            root.setProperty(key, value)

    view.resize(width, height)
    view.show()

    def shot() -> None:
        image = view.grabWindow()
        ok = image.save(str(out))
        print(f"{'saved' if ok else 'failed'}: {out} ({image.width()}x{image.height()})")
        app.quit()

    QTimer.singleShot(500, shot)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
