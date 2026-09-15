# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记正文的文本编辑：改文字，但**保住嵌件占位**。

正文是「文字段 + 占位符」的列表；整段替换文字时，占位符按其在文本中的位置保留，
只有落在被改写区间里的占位符才会消失（那本来就是编辑者删掉的内容）。
"""

from __future__ import annotations

from typing import Any


def _split(body: list[Any]) -> tuple[str, list[tuple[int, dict[str, Any]]]]:
    """把正文拆成「纯文本」+「占位符(在文本中的偏移)」。"""
    parts: list[str] = []
    markers: list[tuple[int, dict[str, Any]]] = []
    offset = 0
    for segment in body:
        if isinstance(segment, str):
            parts.append(segment)
            offset += len(segment)
        else:
            markers.append((offset, segment))
    return "".join(parts), markers


def _common_prefix(old: str, new: str) -> int:
    size = 0
    while size < len(old) and size < len(new) and old[size] == new[size]:
        size += 1
    return size


def _common_suffix(old: str, new: str, prefix: int) -> int:
    size = 0
    while (
        size < len(old) - prefix
        and size < len(new) - prefix
        and old[len(old) - 1 - size] == new[len(new) - 1 - size]
    ):
        size += 1
    return size


def apply_text_edit(body: list[Any], new_text: str) -> list[Any]:
    """把正文的**文字**改成 ``new_text``，保留未受影响的占位符。"""
    old_text, markers = _split(body)
    if old_text == new_text and not markers:
        return list(body)
    prefix = _common_prefix(old_text, new_text)
    suffix = _common_suffix(old_text, new_text, prefix)
    start = prefix
    stop = len(old_text) - suffix
    inserted = new_text[prefix : len(new_text) - suffix]
    delta = len(inserted) - (stop - start)

    kept: list[tuple[int, dict[str, Any]]] = []
    for offset, marker in markers:
        if offset <= start:
            kept.append((offset, marker))
        elif offset >= stop:
            kept.append((offset + delta, marker))
        # 落在 [start, stop) 的占位随被删文字一起消失

    segments: list[Any] = []
    cursor = 0
    for offset, marker in kept:
        if offset > cursor:
            segments.append(new_text[cursor:offset])
        segments.append(marker)
        cursor = offset
    if cursor < len(new_text):
        segments.append(new_text[cursor:])
    trimmed = [segment for segment in segments if segment != ""]
    return trimmed or [""]


__all__ = ["apply_text_edit"]
