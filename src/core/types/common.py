# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""通用小工具。"""

from __future__ import annotations

import time


def now_ms() -> int:
    """当前 Unix 毫秒时间戳。"""
    return int(time.time() * 1000)
