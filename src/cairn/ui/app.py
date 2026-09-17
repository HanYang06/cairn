# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Cairn 桌面应用入口（Qt Quick / QML）。

用法：
    uv run cairn             # 正常启动（当前为 QML 主界面）
    uv run cairn --watch     # 开发模式：QML 热重载（只重载 Shell，不重建窗口）
    uv run cairn --smoke     # 冒烟：0.8 秒后自动退出（用于自检/CI）
    uv run cairn --widgets   # 启动 Widgets 外壳（重建中，见 progress.md「UI 重建」）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property,
    QFileSystemWatcher,
    QObject,
    QTimer,
    QUrl,
    Signal,
)
from PySide6.QtGui import QFont
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from .backend import Backend, env_passphrase, env_vault_root, open_vault

if TYPE_CHECKING:
    from ..core import Vault

QML_DIR = Path(__file__).resolve().parent / "qml"
ENTRY = QML_DIR / "Main.qml"
SHELL = QML_DIR / "Shell.qml"


def apply_round_corners(window: QObject) -> None:
    """Windows 11 原生圆角（最大化时系统会自动保持方正）。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes  # noqa: PLC0415 — 仅 Windows 分支需要，避免非 Windows 平台导入

        hwnd = int(window.winId())  # type: ignore[attr-defined]
        preference = ctypes.c_int(2)  # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
        )
    except Exception:  # noqa: BLE001, S110 — 原生 API 不可用时静默降级，不影响启动
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


def _run_widgets(app: QApplication, vault: Vault, *, smoke: bool) -> int:
    """启动 Widgets 外壳（P0 占位）；返回进程退出码。"""
    from .root import App  # noqa: PLC0415 — 仅 Widgets 模式需要，避免 QML 路径导入
    from .theme import LIGHT  # noqa: PLC0415
    from .theme.manager import ThemeManager  # noqa: PLC0415
    from .window import MainWindow  # noqa: PLC0415

    root = App(vault)
    ThemeManager(app).apply(LIGHT)
    window = MainWindow(root)
    app.aboutToQuit.connect(root.shutdown)
    window.show()
    if smoke:
        QTimer.singleShot(800, app.quit)
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    """启动桌面应用；返回进程退出码。"""
    args = list(sys.argv if argv is None else argv)
    if "--watch" in args or "--dev" in args:
        os.environ.setdefault("QML_DISABLE_DISK_CACHE", "1")

    app = QApplication(args)
    app.setApplicationName("Cairn")
    app.setOrganizationName("Cairn")
    _font = QFont()
    _font.setFamilies(
        ["Sarasa Mono SC", "Cascadia Mono", "Consolas", "Noto Sans Mono CJK SC", "monospace"]
    )
    app.setFont(_font)

    try:
        vault = open_vault(env_vault_root(), env_passphrase())
    except Exception:  # noqa: BLE001 — 顶层入口：启动失败统一以退出码 1 结束
        return 1

    if "--widgets" in args:
        return _run_widgets(app, vault, smoke="--smoke" in args)

    backend = Backend(vault)
    app.aboutToQuit.connect(backend.shutdown)

    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty("backend", backend)
    context.setContextProperty("notesModel", backend.notes)
    context.setContextProperty("tabsModel", backend.tabs)
    shell_source = ShellSource(QUrl.fromLocalFile(str(SHELL)))
    context.setContextProperty("reloader", shell_source)
    engine.load(QUrl.fromLocalFile(str(ENTRY)))
    if not engine.rootObjects():
        return 1
    for obj in engine.rootObjects():
        apply_round_corners(obj)

    if "--watch" in args or "--dev" in args:
        # 必须留引用（并挂到 engine 上）：否则 QObject 会被 GC，watcher 随之失效。
        _hot_reloader = HotReloader(engine, shell_source, engine)

    if "--smoke" in args:
        QTimer.singleShot(800, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
