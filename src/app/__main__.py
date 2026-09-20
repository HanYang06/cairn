# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""应用入口（`python -m app`）：按平台分发。"""

from __future__ import annotations

import sys


def main() -> int:
    """按当前平台分派到对应入口。"""
    if sys.platform.startswith("win"):
        from .win.main import main as run  # noqa: PLC0415 — 按平台延迟导入

        return run()
    raise SystemExit(f"该平台暂无 UI：{sys.platform}")


if __name__ == "__main__":
    raise SystemExit(main())
