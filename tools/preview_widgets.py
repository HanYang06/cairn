# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""离屏渲染 Widgets 外壳为 PNG，供设计评审使用。

用法：
    uv run python tools/preview_widgets.py [输出.png] [宽] [高]

例：
    uv run python tools/preview_widgets.py build/widgets.png 1200 800
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

if os.environ.get("CAIRN_PREVIEW_OFFSCREEN"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QSG_RHI_BACKEND", "software")

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from cairn.core import Vault
from cairn.domains import Group, Note
from cairn.ui.root import App
from cairn.ui.theme.manager import ThemeManager
from cairn.ui.window import MainWindow, Shell

ROOT = Path(__file__).resolve().parents[1]

_SAMPLES = (
    ("存储层设计笔记", "内容先落在本地对象池，再进入索引；块级去重让相同内容只存一份。"),
    ("布局取舍 v1", "把「收」和「编」分开：收集时零摩擦，整理时再建立关系与归属。"),
    ("QML 外壳草案", "领域栏、工具册、标签工作区、上下文右区、来源面包屑。"),
)


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else ROOT / "build" / "widgets.png"
    width = int(argv[2]) if len(argv) > 2 else 1200
    height = int(argv[3]) if len(argv) > 3 else 800

    app = QApplication([])
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
    with tempfile.TemporaryDirectory() as tmp:
        vault = Vault.create(Path(tmp) / "vault")
        created = [Note.create(vault, text, title=title) for title, text in _SAMPLES]
        work = Group.create(vault, "工作")
        design = Group.create(vault, "设计", parent=work)
        work.add(created[0])
        design.add(created[1])
        root = App(vault)
        ThemeManager(app).apply_default()
        root.reload_notes()

        window = MainWindow(root)
        shell = window.centralWidget()
        if isinstance(shell, Shell) and root.notes.rowCount() > 0:
            first = root.notes.row_at(0)
            if first is not None:
                shell.navigator.note_activated.emit(first.oid)
        window.resize(width, height)
        window.show()
        app.processEvents()

        out.parent.mkdir(parents=True, exist_ok=True)
        window.grab().save(str(out))
        root.shutdown()
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
