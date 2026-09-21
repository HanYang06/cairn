# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记正文容器 ``NoteBody``：行序列 + 行内样式，自带内容哈希。

- 行为像 list（迭代 / 下标 / 长度代理到 ``text`` 的行），方便 ``note.body[0]["v"]``。
- ``hash`` = 对 ``content()``（行值 + 行内样式，**剥离行 id**）求摘要；
  不含 attrs / 签名 / 时间戳。内容一变就 ``refresh()`` 重算并存起来。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.storage import Body

from .edit import (
    Line as LineDict,
)
from .edit import (
    StyleMap,
    coerce_style,
    encode_style,
    flatten_text,
    normalize_body,
    signature_style,
)


class NoteBody(Body):
    """正文容器：``text``（行序列）+ ``style``（行内样式）；自带状态 ``hash``。"""

    def __init__(self, text: Any = None, style: Any = None, hash: str = "") -> None:
        self.text: list[LineDict] = normalize_body(text)
        self.style: StyleMap = coerce_style(style, self.text)
        self.hash = str(hash or "")
        if not self.hash:
            self.refresh()

    def content(self) -> dict[str, Any]:
        return {
            "text": [line["v"] for line in self.text],
            "para": [line.get("p") or {} for line in self.text],
            "style": signature_style(self.text, self.style),
        }

    def to_data(self) -> dict[str, Any]:
        return {"text": self.text, "style": encode_style(self.style), "hash": self.hash}

    @classmethod
    def from_data(cls, data: Any) -> NoteBody:
        if not data:
            return cls()
        if isinstance(data, Mapping) and "text" in data:
            return cls(
                text=data.get("text"),
                style=data.get("style"),
                hash=str(data.get("hash") or ""),
            )
        return cls(text=data)  # 兼容：旧 body 就是裸行序列

    @property
    def plain(self) -> str:
        return flatten_text(self.text)

    def refresh(self) -> NoteBody:
        super().refresh()
        return self

    def __iter__(self) -> Any:
        return iter(self.text)

    def __getitem__(self, index: Any) -> Any:
        return self.text[index]

    def __len__(self) -> int:
        return len(self.text)


__all__ = ["NoteBody"]
