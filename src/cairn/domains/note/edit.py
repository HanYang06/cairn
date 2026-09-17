# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记正文的编辑原语：**行身份** + **行内区间样式**。

正文 = 有序行序列，每行有稳定 id：

    body  = [ {"id": lid, "v": "第一行"}, {"id": lid2, "v": {"canvas": 0}} ]

行内样式按「行 id → 区间层」叠加（后者覆盖前者）：

    style = { lid: [ {(0, 3): Style(bold=True)} ] }

约定：
- 行 id 生成即锁死；行增删 / 重排只动序列，样式不受影响（不漂移）。
- 区间可叠加，规范化为**不重叠、有序、去掉默认**。
- 内容签名按行顺序取「行值 + 解析后样式」，**丢掉行 id**——同文同样式即同签名，
  这样"纯复制"能去重，改一个字就不同。
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

from blake3 import blake3

from ...types import Oid
from .model import Style

Line = dict[str, Any]
Marker = dict[str, int]
RangeStyle = dict[tuple[int, int], Style]
StyleMap = dict[str, list[RangeStyle]]

_MARKER_KEYS = ("canvas", "access")


def new_id() -> str:
    """生成一个行身份（ULID）。"""
    return str(Oid.new())


def is_marker(value: Any) -> bool:
    """是否是嵌入占位（画板 / 多媒体）。"""
    return isinstance(value, Mapping) and any(key in value for key in _MARKER_KEYS)


# 超长行阈值：等效中文字数（见 ``text_weight``）。
OVERLONG_WEIGHT = 300.0


def text_weight(text: str) -> float:
    """等效中文字数：全角 / 宽字符记 1，半角记 0.5（用于超长行判定）。"""
    return sum(1.0 if unicodedata.east_asian_width(ch) in ("W", "F") else 0.5 for ch in text)


def _entry(line_id: str, value: Any, para: Any = None) -> Line:
    entry: Line = {"id": line_id, "v": value}
    if para:
        entry["p"] = dict(para)
    return entry


# ---- 正文（行序列）----
def normalize_body(raw: Any) -> list[Line]:
    r"""把任意输入规范成带 id 的行序列；字符串按 ``\n`` 拆行，保留 ``p``（段落属性）。"""
    lines: list[Line] = []
    for item in raw or ():
        if is_marker(item):
            lines.append(_entry(new_id(), dict(item)))
            continue
        if isinstance(item, Mapping) and "v" in item:
            lid = str(item.get("id") or new_id())
            para = item.get("p")
            value = item["v"]
            if isinstance(value, str):
                for offset, part in enumerate(value.split("\n")):
                    lines.append(_entry(lid if offset == 0 else new_id(), part, para))
            else:
                lines.append(_entry(lid, value, para))
            continue
        lines.extend(_entry(new_id(), part) for part in str(item).split("\n"))
    return lines or [_entry(new_id(), "")]


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
            out.append(_entry(line["id"], dict(line["v"]), line.get("p")))
            continue
        if cursor < len(values):
            out.append(_entry(line["id"], values[cursor], line.get("p")))
            cursor += 1
    while cursor < len(values):
        out.append(_entry(new_id(), values[cursor]))
        cursor += 1
    return out or [_entry(new_id(), "")]


# ---- 行内区间样式 ----
def _overlay(
    segments: list[tuple[int, int, Style]], start: int, end: int, style: Style
) -> list[tuple[int, int, Style]]:
    """把 ``[start, end)`` 的样式叠加到已解析的区间上（后者覆盖前者）。"""
    if end <= start:
        return segments
    out: list[tuple[int, int, Style]] = []
    for seg_start, seg_end, seg_style in segments:
        if seg_end <= start or seg_start >= end:
            out.append((seg_start, seg_end, seg_style))
            continue
        if seg_start < start:
            out.append((seg_start, start, seg_style))
        if seg_end > end:
            out.append((end, seg_end, seg_style))
    out.append((start, end, style))
    out.sort(key=lambda item: (item[0], item[1]))
    return out


def _resolve(layers: Sequence[Mapping[tuple[int, int], Style]]) -> list[tuple[int, int, Style]]:
    segments: list[tuple[int, int, Style]] = []
    for layer in layers:
        for key, style in layer.items():
            start, end = int(key[0]), int(key[1])
            segments = _overlay(segments, start, end, style)
    result = [
        (start, end, style) for start, end, style in segments if end > start and style != Style()
    ]
    merged: list[tuple[int, int, Style]] = []
    for start, end, style in result:
        if merged and merged[-1][1] == start and merged[-1][2] == style:
            merged[-1] = (merged[-1][0], end, style)
        else:
            merged.append((start, end, style))
    return merged


def canonicalize_style(smap: Mapping[str, Any], lines: Sequence[Line]) -> StyleMap:
    """规范化样式表：只留有效行、合并区间、去掉默认与空区间。"""
    valid = {line["id"] for line in lines}
    result: StyleMap = {}
    for lid, layers in smap.items():
        if str(lid) not in valid:
            continue
        resolved = _resolve(list(layers))
        if resolved:
            result[str(lid)] = [{(start, end): style for start, end, style in resolved}]
    return result


def decode_style(raw: Any, lines: Sequence[Line]) -> StyleMap:  # noqa: C901 — 兼容旧格式的分支解析
    """把落盘 / 旧格式的样式解码成类型化样式表。

    兼容两种旧形态：与行等长的 ``list[Style]``（旧平行表）、以及
    ``{lid: [[start, end, style_data], ...]}``。
    """
    if not raw:
        return {}
    if isinstance(raw, (list, tuple)):
        smap: dict[str, list[RangeStyle]] = {}
        for index, line in enumerate(lines):
            if index >= len(raw) or is_marker(line["v"]):
                continue
            style = raw[index]
            style = style if isinstance(style, Style) else Style.from_data(style)
            length = len(line["v"]) if isinstance(line["v"], str) else 0
            if style != Style() and length > 0:
                smap[line["id"]] = [{(0, length): style}]
        return canonicalize_style(smap, lines)
    smap = {}
    for lid, triples in raw.items():
        layers: list[RangeStyle] = []
        layer: RangeStyle = {}
        for item in triples or ():
            if isinstance(item, Mapping):  # 已是 {(s,e): Style}
                for key, style in item.items():
                    resolved = style if isinstance(style, Style) else Style.from_data(style)
                    layer[(int(key[0]), int(key[1]))] = resolved
            elif isinstance(item, (list, tuple)) and len(item) >= 3:
                start, end, style = item[0], item[1], item[2]
                resolved = style if isinstance(style, Style) else Style.from_data(style)
                layer[(int(start), int(end))] = resolved
        if layer:
            layers.append(layer)
        smap[str(lid)] = layers
    return canonicalize_style(smap, lines)


def encode_style(smap: StyleMap) -> dict[str, list[list[Any]]]:
    """把类型化样式表编码成可落盘的紧凑形式。"""
    out: dict[str, list[list[Any]]] = {}
    for lid, layers in smap.items():
        triples: list[list[Any]] = []
        for layer in layers:
            for (start, end), style in layer.items():
                triples.append([int(start), int(end), style.to_data()])
        if triples:
            out[lid] = triples
    return out


def coerce_style(value: Any, lines: Sequence[Line]) -> StyleMap:
    """统一入口：任意样式输入 → 规范化类型化样式表。"""
    if value is None:
        return {}
    return decode_style(value, lines)


_BOOL_KEYS = ("bold", "italic", "underline", "strike")


def _index_of(lines: Sequence[Line], line_id: str) -> int:
    for index, line in enumerate(lines):
        if line["id"] == line_id:
            return index
    return -1


def _copy_lines(lines: Sequence[Line]) -> list[Line]:
    return [_entry(line["id"], line["v"], line.get("p")) for line in lines]


# ---- 行级编辑原语（返回新序列，不改原值）----
def set_line_text(lines: Sequence[Line], line_id: str, text: str) -> list[Line]:
    r"""改写某一行文字；含换行时按 ``\n`` 就地拆成多行（新行另分配 id，沿用 ``p``）。"""
    parts = str(text).split("\n")
    out: list[Line] = []
    for line in lines:
        if line["id"] != line_id or is_marker(line["v"]):
            out.append(_entry(line["id"], line["v"], line.get("p")))
            continue
        out.append(_entry(line["id"], parts[0], line.get("p")))
        out.extend(_entry(new_id(), part, line.get("p")) for part in parts[1:])
    return out


def insert_line(
    lines: Sequence[Line], after_id: str | None, value: str = ""
) -> tuple[list[Line], str]:
    """在 ``after_id`` 之后插入一行（``None`` 追加到末尾）；返回新行 id。"""
    out = _copy_lines(lines)
    lid = new_id()
    position = len(out) if after_id is None else _index_of(out, after_id) + 1
    out.insert(max(0, position), _entry(lid, str(value)))
    return out, lid


def remove_line(lines: Sequence[Line], line_id: str) -> list[Line]:
    """删除一行；删空时保留一个空行，保证正文至少一行。"""
    out = [_entry(line["id"], line["v"], line.get("p")) for line in lines if line["id"] != line_id]
    return out or [_entry(new_id(), "")]


def split_line(
    lines: Sequence[Line], line_id: str, offset: int
) -> tuple[list[Line], str, str, int]:
    """在 ``offset`` 处把一行拆成两行；返回 ``(新序列, 新行 id, 原行 id, 原行长度)``。"""
    out: list[Line] = []
    new_lid = new_id()
    old_len = 0
    for line in lines:
        if line["id"] != line_id or is_marker(line["v"]):
            out.append(_entry(line["id"], line["v"], line.get("p")))
            continue
        text = str(line["v"])
        old_len = len(text)
        cut = max(0, min(int(offset), old_len))
        out.append(_entry(line["id"], text[:cut], line.get("p")))
        out.append(_entry(new_lid, text[cut:], line.get("p")))
    return out, new_lid, line_id, old_len


def merge_line(lines: Sequence[Line], line_id: str) -> tuple[list[Line], str | None, int]:
    """把 ``line_id`` 并入上一行；返回 ``(新序列, 上一行 id, 上一行长度)``。

    已是首行、或涉及嵌入占位时不合并，返回 ``(原序列, None, 0)``。
    """
    out = _copy_lines(lines)
    index = _index_of(out, line_id)
    if index <= 0:
        return out, None, 0
    previous = out[index - 1]
    current = out[index]
    if is_marker(previous["v"]) or is_marker(current["v"]):
        return _copy_lines(lines), None, 0
    previous_text = str(previous["v"])
    out[index - 1] = _entry(previous["id"], previous_text + str(current["v"]), previous.get("p"))
    del out[index]
    return out, previous["id"], len(previous_text)


def drop_style(smap: StyleMap, line_id: str) -> StyleMap:
    """去掉某一行的全部样式。"""
    return {key: value for key, value in smap.items() if key != line_id}


def split_style(smap: StyleMap, line_id: str, new_line_id: str, offset: int) -> StyleMap:
    """拆行时按 ``offset`` 把该行样式切成两段，右段迁到新行并平移。"""
    layers = smap.get(line_id)
    if not layers:
        return smap
    left: RangeStyle = {}
    right: RangeStyle = {}
    for start, end, style in _resolve(layers):
        if start < offset:
            left[(start, min(end, offset))] = style
        if end > offset:
            right[(max(start, offset) - offset, end - offset)] = style
    out = {key: value for key, value in smap.items() if key != line_id}
    if left:
        out[line_id] = [left]
    if right:
        out[new_line_id] = [right]
    return out


def merge_style(smap: StyleMap, first_id: str, second_id: str, first_len: int) -> StyleMap:
    """合并两行时拼接样式：第二行区间整体右移 ``first_len``。"""
    merged: RangeStyle = {}
    for start, end, style in _resolve(smap.get(first_id, [])):
        merged[(start, end)] = style
    for start, end, style in _resolve(smap.get(second_id, [])):
        merged[(start + first_len, end + first_len)] = style
    out = {key: value for key, value in smap.items() if key not in (first_id, second_id)}
    if merged:
        out[first_id] = [merged]
    return out


def _style_at(smap: StyleMap, line_id: str, position: int) -> Style:
    for start, end, style in _resolve(smap.get(line_id, [])):
        if start <= position < end:
            return style
    return Style()


def style_at(smap: StyleMap, line_id: str, position: int) -> Style:
    """某一行某位置**解析后**的样式（供工具读取当前值）。"""
    return _style_at(smap, line_id, int(position))


def toggle_range_style(smap: StyleMap, line_id: str, start: int, end: int, key: str) -> StyleMap:
    """对 ``[start, end)`` 切换一个布尔样式；以区间起点处的当前样式为基准取反。"""
    if key not in _BOOL_KEYS or end <= start:
        return smap
    current = _style_at(smap, line_id, int(start))
    data = current.to_data()
    data[key] = not bool(getattr(current, key))
    toggled = Style.from_data(data)
    layer: RangeStyle = {(int(start), int(end)): toggled}
    return {**smap, line_id: [*smap.get(line_id, []), layer]}


def set_range_style(
    smap: StyleMap, line_id: str, start: int, end: int, patch: Mapping[str, Any]
) -> StyleMap:
    """对 ``[start, end)`` 设置若干样式字段（未提到的字段保持区间起点处现状）。"""
    if end <= start:
        return smap
    current = _style_at(smap, line_id, int(start))
    data = current.to_data()
    for key, value in patch.items():
        if key in data:
            data[key] = value
    layer: RangeStyle = {(int(start), int(end)): Style.from_data(data)}
    return {**smap, line_id: [*smap.get(line_id, []), layer]}


def clear_range_style(smap: StyleMap, line_id: str, start: int, end: int) -> StyleMap:
    """清掉 ``[start, end)`` 的全部行内样式（叠加一层默认值）。"""
    if end <= start:
        return smap
    layer: RangeStyle = {(int(start), int(end)): Style()}
    return {**smap, line_id: [*smap.get(line_id, []), layer]}


def line_styles(smap: StyleMap, line: Line) -> list[tuple[int, int, Style]]:
    """某一行解析后的样式区间（已按当前行长度裁剪）。"""
    text = line["v"]
    length = len(text) if isinstance(text, str) else 0
    resolved = _resolve(smap.get(line["id"], []))
    out: list[tuple[int, int, Style]] = []
    for seg_start, seg_end, style in resolved:
        start = max(0, min(seg_start, length))
        end = max(0, min(seg_end, length))
        if end > start:
            out.append((start, end, style))
    return out


def signature_style(lines: Sequence[Line], smap: StyleMap) -> list[list[Any]]:
    """内容签名里的样式视图：按行顺序、丢行 id。"""
    view: list[list[Any]] = []
    for line in lines:
        if is_marker(line["v"]):
            view.append([])
            continue
        view.append(
            [[start, end, style.to_data()] for start, end, style in line_styles(smap, line)]
        )
    return view


def content_signature(kind: str, lines: Sequence[Line], smap: StyleMap) -> str:
    """版本用的内容签名（不含行 id）：同文同样式即同签名。"""
    from ...core.store import canonical  # noqa: PLC0415 — 延迟导入，避免加载期潜在环

    payload = {
        "type": kind,
        "body": [line["v"] for line in lines],
        "style": signature_style(lines, smap),
    }
    return blake3(canonical(payload)).hexdigest()


__all__ = [
    "OVERLONG_WEIGHT",
    "Line",
    "Marker",
    "RangeStyle",
    "StyleMap",
    "apply_text",
    "canonicalize_style",
    "clear_range_style",
    "coerce_style",
    "content_signature",
    "decode_style",
    "drop_style",
    "encode_style",
    "flatten_text",
    "insert_line",
    "is_marker",
    "line_styles",
    "merge_line",
    "merge_style",
    "new_id",
    "normalize_body",
    "remove_line",
    "set_line_text",
    "set_range_style",
    "signature_style",
    "split_line",
    "split_style",
    "style_at",
    "text_weight",
    "toggle_range_style",
]
