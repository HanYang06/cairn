# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Windows 后端：领域数据 → 中立卡片（经 `Show` 投影）。

**呈现映射在 App 侧**：`Show` 给中立的归集结果，这里定义"卡片 = 哪些字段 → 哪些槽"。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ui_tools.core import Show


@dataclass(frozen=True)
class NoteCard:
    """一张笔记卡的展示数据（中立，不含 Qt / 存储类型）。"""

    title: str
    preview: str
    meta: str
    badge: str = "notedata"


def _to_ms(value: Any) -> int:
    """宽松把属性值转成毫秒；非法 / 缺失记 0。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def fmt_time(ms: int) -> str:
    """Unix 毫秒 → 简短相对时间。"""
    if ms <= 0:
        return ""
    try:
        moment = datetime.fromtimestamp(ms / 1000, tz=UTC)
    except (OverflowError, OSError, ValueError):
        return ""
    seconds = int((datetime.now(tz=UTC) - moment).total_seconds())
    if seconds < 60:  # 含未来时间（时钟偏差 / 同步数据）
        result = "刚刚"
    elif seconds < 3600:
        result = f"{seconds // 60} 分钟前"
    elif seconds < 86400:
        result = f"{seconds // 3600} 小时前"
    elif seconds < 86400 * 7:
        result = f"{seconds // 86400} 天前"
    else:
        result = moment.strftime("%Y-%m-%d")
    return result


def _preview(show: Show) -> str:
    for body in show.bodies:
        plain = str(getattr(body, "plain", "") or "")
        text = " ".join(plain.split())
        if text:
            return text[:80]
    return ""


def note_card(note: Any) -> NoteCard:
    """一条笔记（数据对象）→ 卡片。"""
    show = Show(note)
    title = str(show.attrs.get("title") or "").strip()
    return NoteCard(
        title=title or "（无标题）",
        preview=_preview(show),
        meta=fmt_time(_to_ms(show.attrs.get("updated"))),
        badge=show.parts[0].type if show.parts else "notedata",
    )


def note_cards(notes: Any) -> list[NoteCard]:
    """把笔记域服务列出的笔记投影成卡片。"""
    return [note_card(data) for data in notes.list_notes()]


__all__ = ["NoteCard", "fmt_time", "note_card", "note_cards"]
