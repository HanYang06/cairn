# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""行内区间样式：值类型 + 规范化 / 编解码 / 读写（后层压前层；规范化为不重叠、有序、去默认）。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from blake3 import blake3

from .body import Line, is_marker


@dataclass(slots=True)
class Style:
    """一段文字的样式；全默认即"无修饰"。"""

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
        if not isinstance(data, Mapping):
            return cls()
        known = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        return cls(**known)


RangeStyle = dict[tuple[int, int], Style]
StyleMap = dict[str, list[RangeStyle]]

_BOOL_KEYS = ("bold", "italic", "underline", "strike")


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
    """统一入口：任意样式输入 → 规范化类型化样式表；异形输入退化为空表。"""
    if value is None:
        return {}
    if not isinstance(value, (Mapping, list, tuple)):
        return {}
    return decode_style(value, lines)


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


def bool_state(smap: StyleMap, line_id: str, start: int, end: int, key: str) -> bool | None:
    """区间内某布尔样式的**三态**：全真 ``True`` / 全假 ``False`` / 混合 ``None``。

    无选区（``end <= start``）时取该位置单点；供工具栏高亮「生效 / 未生效 / 半选」。
    """
    start, end = int(start), int(end)
    if end <= start:
        return bool(getattr(_style_at(smap, line_id, start), key))
    result: bool | None = None
    cursor = start
    for seg_start, seg_end, style in _resolve(smap.get(line_id, [])):
        if seg_end <= start or seg_start >= end:
            continue
        if seg_start > cursor:
            if result is True:
                return None
            result = False
        value = bool(getattr(style, key))
        if result is not None and result != value:
            return None
        result = value
        cursor = max(cursor, min(seg_end, end))
    if cursor < end:
        if result is True:
            return None
        result = False
    return bool(result) if result is not None else False


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
        if value is None or key not in data:
            continue
        if key in _BOOL_KEYS:
            data[key] = bool(value)
        elif key == "size":
            data[key] = float(value)
        elif key in ("font", "color"):
            data[key] = str(value)
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
    from core.storage import canonical  # noqa: PLC0415 — 延迟导入，避免加载期潜在环

    payload = {
        "type": kind,
        "body": [line["v"] for line in lines],
        "style": signature_style(lines, smap),
    }
    return blake3(canonical(payload)).hexdigest()


__all__ = [
    "RangeStyle",
    "Style",
    "StyleMap",
    "bool_state",
    "canonicalize_style",
    "clear_range_style",
    "coerce_style",
    "content_signature",
    "decode_style",
    "drop_style",
    "encode_style",
    "line_styles",
    "merge_style",
    "set_range_style",
    "signature_style",
    "split_style",
    "style_at",
    "toggle_range_style",
]
