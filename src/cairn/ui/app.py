# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Cairn 桌面应用入口（Qt Quick / QML）。

用法：
    uv run cairn             # 正常启动
    uv run cairn --watch     # 开发模式：QML 热重载（只重载 Shell，不重建窗口）
    uv run cairn --smoke     # 冒烟：0.8 秒后自动退出（用于自检/CI）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QFileSystemWatcher,
    QObject,
    QTimer,
    QUrl,
    Signal,
)
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .backend import Backend, env_passphrase, env_vault_root, open_vault

QML_DIR = Path(__file__).resolve().parent / "qml"
ENTRY = QML_DIR / "Main.qml"
SHELL = QML_DIR / "Shell.qml"


def apply_round_corners(window: QObject) -> None:
    """Windows 11 原生圆角（最大化时系统会自动保持方正）。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = int(window.winId())  # type: ignore[attr-defined]
        preference = ctypes.c_int(2)  # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
        )
    except Exception:
        pass


class ShellSource(QObject):
    """把 `Loader.source` 暴露成可绑定的属性。

    热重载只改这里的 URL，由 QML 绑定驱动 Loader 重载；不通过 findChild 去
    改 Loader 本身，避免 PySide6 包装器被回收后 ``setProperty`` 抛
    "Internal C++ object already deleted"。
    """

    changed = Signal()

    def __init__(self, url: QUrl) -> None:
        super().__init__()
        self._url = url

    def get_url(self) -> QUrl:
        return self._url

    def set_url(self, url: QUrl) -> None:
        if url != self._url:
            self._url = url
            self.changed.emit()

    shellSource = Property(QUrl, get_url, set_url, notify=changed)


class HotReloader(QObject):
    """监视 QML 目录；改动后用带版本号的 URL 触发 Shell 重载（不重建窗口）。"""

    def __init__(
        self,
        engine: QQmlApplicationEngine,
        source: ShellSource,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._source = source
        self._revision = 0
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._schedule)
        self._watcher.directoryChanged.connect(self._schedule)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._reload)
        self._scan()

    def _scan(self) -> None:
        files = {str(p) for p in QML_DIR.rglob("*.qml")}
        dirs = {str(p.parent) for p in QML_DIR.rglob("*.qml")}
        dirs.add(str(QML_DIR))
        wanted = files | dirs
        watched = set(self._watcher.files()) | set(self._watcher.directories())
        missing = [p for p in wanted if p not in watched and Path(p).exists()]
        if missing:
            self._watcher.addPaths(missing)

    def _schedule(self, *_args: object) -> None:
        self._timer.start()

    def _reload(self) -> None:
        self._revision += 1
        # 版本号让 URL 变化：Loader 会重新实例化，绕过组件缓存。
        url = QUrl.fromLocalFile(str(SHELL))
        url.setQuery(f"v={self._revision}")
        self._source.set_url(url)
        self._scan()
        print(f"[watch] 重新加载 Shell.qml（v{self._revision}）", flush=True)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    if "--watch" in args or "--dev" in args:
        os.environ.setdefault("QML_DISABLE_DISK_CACHE", "1")

    app = QGuiApplication(args)
    app.setApplicationName("Cairn")
    app.setOrganizationName("Cairn")
    _font = QFont()
    _font.setFamilies(
        ["Sarasa Mono SC", "Cascadia Mono", "Consolas", "Noto Sans Mono CJK SC", "monospace"]
    )
    app.setFont(_font)

    try:
        vault = open_vault(env_vault_root(), env_passphrase())
    except Exception as exc:
        print(f"打开库失败：{exc}", file=sys.stderr)
        return 1
    backend = Backend(vault)

    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty("backend", backend)
    context.setContextProperty("notesModel", backend.notes)
    context.setContextProperty("tabsModel", backend.tabs)
    shell_source = ShellSource(QUrl.fromLocalFile(str(SHELL)))
    context.setContextProperty("reloader", shell_source)
    engine.load(QUrl.fromLocalFile(str(ENTRY)))
    if not engine.rootObjects():
        print("QML 加载失败", file=sys.stderr)
        return 1
    for obj in engine.rootObjects():
        apply_round_corners(obj)

    if "--watch" in args or "--dev" in args:
        # 必须留引用（并挂到 engine 上）：否则 QObject 会被 GC，watcher 随之失效。
        _hot_reloader = HotReloader(engine, shell_source, engine)
        print("[watch] 已开启 QML 热重载（改动 qml/ 下文件即生效）")
        print(f"[watch] 监视目录：{QML_DIR}")

    if "--smoke" in args:
        QTimer.singleShot(800, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
