# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Windows 应用入口：一行起。"""

from __future__ import annotations

from .windows import CairnApp


def main() -> int:
    """开库、组装、跑起来（细节都在 `CairnApp` 里）。"""
    return CairnApp.open().run()


if __name__ == "__main__":
    raise SystemExit(main())
