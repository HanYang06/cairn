# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0
# -*- mode: python ; coding: utf-8 -*-

"""PyInstaller 打包脚本（Windows onedir）。

    uv run python tools/build.py

- 主题配置（``config/theme``）是数据文件，必须显式随包携带（见 datas）。
- 版本号由构建脚本经环境变量 ``CAIRN_VERSION`` 注入，仅用于展示信息。
"""

from pathlib import Path

root = Path(SPECPATH).resolve().parent
config_dir = root / "config"
icon = root / "assets" / "logo" / "cairn.ico"

datas = [(str(config_dir), "config")]

# 未使用的 Qt 大模块不打包，控制体积；按需增删。
excludes = [
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtMultimedia",
    "PySide6.QtPdf",
    "PySide6.QtQuick3D",
    "PySide6.QtSql",
    "PySide6.QtTest",
]

a = Analysis(  # noqa: F821
    # UI 重建后入口恢复为 `ui.__main__` / `ui.app:main`；当前内核态无桌面入口。
    [str(root / "src" / "ui" / "__main__.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
# Qt 的 QML hook 会连带收集未使用的模块（`excludes` 拦不住）；按路径剔除。
_drop = ("webengine",)
a.binaries = [item for item in a.binaries if not any(s in item[0].lower() for s in _drop)]
a.datas = [item for item in a.datas if not any(s in item[0].lower() for s in _drop)]

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="cairn",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon) if icon.exists() else None,
)
coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="cairn",
)
