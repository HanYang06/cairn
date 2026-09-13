# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""端到端冒烟：子进程启动 QML 应用（离屏、临时库），0.8 秒后自动退出。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_SCRIPT = "import sys; from cairn.ui.app import main; raise SystemExit(main(['cairn', '--smoke']))"


def test_app_smoke(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QSG_RHI_BACKEND"] = "software"
    env["CAIRN_VAULT"] = str(tmp_path / "vault")
    result = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
