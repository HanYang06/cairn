# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""行级文本操作：拍平、整段替换、增删、拆合（返回新序列，不改原值）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .body import Line, copy_lines, entry, index_of, is_marker, new_id

if TYPE_CHECKING:
    from collections.abc import Sequence


def flatten_text(lines: Sequence[Line]) -> str:
    """把行序列拍平成纯文本（嵌入占位不占字符）。"""
    return "\n".join(str(line["v"]) for line in lines if not is_marker(line["v"]))


def apply_text(lines: Sequence[Line], text: str) -> list[Line]:
    """整段替换文字，尽量保留行身份、嵌入占位与段落属性。

    文字行按位复用原有行 id 与 ``p``；多出的新行另分配；占位行原地保留。
    """
    values = text.split("\n")
    out: list[Line] = []
    cursor = 0
    for line in lines:
        if is_marker(line["v"]):
            out.append(entry(line["id"], dict(line["v"]), line.get("p")))
            continue
        if cursor < len(values):
            out.append(entry(line["id"], values[cursor], line.get("p")))
            cursor += 1
    while cursor < len(values):
        out.append(entry(new_id(), values[cursor]))
        cursor += 1
    return out or [entry(new_id(), "")]


def set_line_text(lines: Sequence[Line], line_id: str, text: str) -> list[Line]:
    r"""改写某一行文字；含换行时按 ``\n`` 就地拆成多行（新行另分配 id，沿用 ``p``）。"""
    parts = str(text).split("\n")
    out: list[Line] = []
    for line in lines:
        if line["id"] != line_id or is_marker(line["v"]):
            out.append(entry(line["id"], line["v"], line.get("p")))
            continue
        out.append(entry(line["id"], parts[0], line.get("p")))
        out.extend(entry(new_id(), part, line.get("p")) for part in parts[1:])
    return out


def insert_line(
    lines: Sequence[Line], after_id: str | None, value: str = ""
) -> tuple[list[Line], str]:
    """在 ``after_id`` 之后插入一行（``None`` 追加到末尾）；返回新行 id。"""
    out = copy_lines(lines)
    lid = new_id()
    position = len(out)
    if after_id is not None:
        index = index_of(out, after_id)
        if index >= 0:
            position = index + 1
    out.insert(position, entry(lid, str(value)))
    return out, lid


def remove_line(lines: Sequence[Line], line_id: str) -> list[Line]:
    """删除一行；删空时保留一个空行，保证正文至少一行。"""
    out = [entry(line["id"], line["v"], line.get("p")) for line in lines if line["id"] != line_id]
    return out or [entry(new_id(), "")]


def split_line(
    lines: Sequence[Line], line_id: str, offset: int
) -> tuple[list[Line], str, str, int]:
    """在 ``offset`` 处把一行拆成两行；返回 ``(新序列, 新行 id, 原行 id, 原行长度)``。"""
    out: list[Line] = []
    new_lid = new_id()
    old_len = 0
    for line in lines:
        if line["id"] != line_id or is_marker(line["v"]):
            out.append(entry(line["id"], line["v"], line.get("p")))
            continue
        text = str(line["v"])
        old_len = len(text)
        cut = max(0, min(int(offset), old_len))
        out.append(entry(line["id"], text[:cut], line.get("p")))
        out.append(entry(new_lid, text[cut:], line.get("p")))
    return out, new_lid, line_id, old_len


def merge_line(lines: Sequence[Line], line_id: str) -> tuple[list[Line], str | None, int]:
    """把 ``line_id`` 并入上一行；返回 ``(新序列, 上一行 id, 上一行长度)``。

    已是首行、或涉及嵌入占位时不合并，返回 ``(原序列, None, 0)``。
    """
    out = copy_lines(lines)
    index = index_of(out, line_id)
    if index <= 0:
        return out, None, 0
    previous = out[index - 1]
    current = out[index]
    if is_marker(previous["v"]) or is_marker(current["v"]):
        return out, None, 0
    previous_text = str(previous["v"])
    out[index - 1] = entry(previous["id"], previous_text + str(current["v"]), previous.get("p"))
    del out[index]
    return out, previous["id"], len(previous_text)


__all__ = [
    "apply_text",
    "flatten_text",
    "insert_line",
    "merge_line",
    "remove_line",
    "set_line_text",
    "split_line",
]
