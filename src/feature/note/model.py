# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记的纯数据模型：文本样式等。

画板（``Canvas`` 及其 ``Graphic`` / ``Paint`` / ``Link`` / ``Form`` / ``Line``）已
**升格为全局内容类型**，见 [`domains/canvas.py`](../canvas.py)；外联资源直接引用 ``Asset``
（见 [`domains/asset.py`](../asset.py)）。这里只做转出，方便笔记内部引用。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from ..canvas import Canvas, CanvasBody, Form, Graphic, Line, Link, Paint

if TYPE_CHECKING:
    from collections.abc import Mapping

NOTE_KIND = "cairn.note"
NOTE_MIME = "application/x-cairn-note"
NOTE_SCHEMA = 1

Text = str
Segment = Text | dict[str, Any]


@dataclass(slots=True)
class Style:
    """一段文字的样式；全默认即"无修饰"。

    行内样式由 ``edit`` 的区间叠加表达；全默认即无样式。
    """

    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    font: str = ""
    color: str = ""
    size: float = 0.0

    def to_data(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> Style:
        known = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        return cls(**known)


__all__ = [
    "NOTE_KIND",
    "NOTE_MIME",
    "NOTE_SCHEMA",
    "Canvas",
    "CanvasBody",
    "Form",
    "Graphic",
    "Line",
    "Link",
    "Paint",
    "Segment",
    "Style",
    "Text",
]
