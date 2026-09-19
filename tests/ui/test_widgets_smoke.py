# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Widgets 外壳冒烟：子进程启动离屏窗口（临时库），0.8 秒后自动退出。"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_SCRIPT = "import sys; from cairn.ui.app import main; raise SystemExit(main(['cairn', '--smoke']))"
_DECL_SCRIPT = (
    "import sys; from cairn.ui.app import main; "
    "raise SystemExit(main(['cairn', '--decl', '--smoke']))"
)


def _run(script: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["CAIRN_VAULT"] = str(tmp_path / "vault")
    return subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def test_widgets_smoke(tmp_path: Path) -> None:
    result = _run(_SCRIPT, tmp_path)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"


def test_decl_smoke(tmp_path: Path) -> None:
    result = _run(_DECL_SCRIPT, tmp_path)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
