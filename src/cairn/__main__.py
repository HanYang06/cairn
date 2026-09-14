# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""让 `python -m cairn`（以及冻结后的可执行文件）可达应用入口。"""

from __future__ import annotations

from cairn.ui.app import main

if __name__ == "__main__":
    raise SystemExit(main())
