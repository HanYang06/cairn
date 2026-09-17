# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""展示用格式化：时间 / 大小。Qt-free、可单测，UI 各处共用一处口径。"""

from __future__ import annotations

import datetime


def fmt_time(ms: int) -> str:
    """把 unix 毫秒格式化为「今天看时间、今年看月日、更早看年月日」。"""
    moment = datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.UTC).astimezone()
    now = datetime.datetime.now(tz=datetime.UTC).astimezone()
    if moment.date() == now.date():
        return moment.strftime("%H:%M")
    if moment.year == now.year:
        return moment.strftime("%m-%d")
    return moment.strftime("%Y-%m-%d")


def fmt_size(num_bytes: int) -> str:
    """把字节数格式化为 B / KB / MB。"""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / 1024 / 1024:.1f} MB"


__all__ = ["fmt_size", "fmt_time"]
