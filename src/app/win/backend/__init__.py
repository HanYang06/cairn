# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Windows 后端：把领域数据投影成界面可用的中立卡片。

不 import Qt；输出普通 DTO，供 `Facet` 声明卡片舞台时取用。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class NoteCard:
    """一张笔记卡的展示数据（中立，不含 Qt / 存储类型）。"""

    title: str
    preview: str
    meta: str
    badge: str = "note"


def fmt_time(ms: int) -> str:
    """Unix 毫秒 → 简短相对时间。"""
    if ms <= 0:
        return ""
    moment = datetime.fromtimestamp(ms / 1000, tz=UTC)
    seconds = int((datetime.now(tz=UTC) - moment).total_seconds())
    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{seconds // 60} 分钟前"
    if seconds < 86400:
        return f"{seconds // 3600} 小时前"
    if seconds < 86400 * 7:
        return f"{seconds // 86400} 天前"
    return moment.strftime("%Y-%m-%d")


def _preview(data: Any) -> str:
    plain = getattr(getattr(data, "body", None), "plain", "") or ""
    return " ".join(str(plain).split())[:80]


def note_cards(notes: Any) -> list[NoteCard]:
    """把笔记域服务列出的笔记投影成卡片。"""
    return [
        NoteCard(
            title=str(getattr(data, "title", "") or "（无标题）"),
            preview=_preview(data),
            meta=fmt_time(int(getattr(data, "updated", 0) or 0)),
            badge="note",
        )
        for data in notes.list_notes()
    ]


__all__ = ["NoteCard", "fmt_time", "note_cards"]
