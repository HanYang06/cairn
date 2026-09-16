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


# ---- 正文（行序列）----
def normalize_body(raw: Any) -> list[Line]:
    """把任意输入规范成带 id 的行序列；字符串按 ``\\n`` 拆行。"""
    lines: list[Line] = []
    for item in raw or ():
        if is_marker(item):
            lines.append({"id": new_id(), "v": dict(item)})
            continue
        if isinstance(item, Mapping) and "v" in item:
            lid = str(item.get("id") or new_id())
            value = item["v"]
            if isinstance(value, str):
                for offset, part in enumerate(value.split("\n")):
                    lines.append({"id": lid if offset == 0 else new_id(), "v": part})
            else:
                lines.append({"id": lid, "v": value})
            continue
        for part in str(item).split("\n"):
            lines.append({"id": new_id(), "v": part})
    return lines or [{"id": new_id(), "v": ""}]


def flatten_text(lines: Sequence[Line]) -> str:
    """把行序列拍平成纯文本（嵌入占位不占字符）。"""
    return "\n".join(str(line["v"]) for line in lines if not is_marker(line["v"]))


def apply_text(lines: Sequence[Line], text: str) -> list[Line]:
    """整段替换文字，尽量保留行身份与嵌入占位。

    文字行按位复用原有行 id；多出的新行另分配；占位行原地保留。
    """
    values = text.split("\n")
    out: list[Line] = []
    cursor = 0
    for line in lines:
        if is_marker(line["v"]):
            out.append({"id": line["id"], "v": dict(line["v"])})
            continue
        if cursor < len(values):
            out.append({"id": line["id"], "v": values[cursor]})
            cursor += 1
    while cursor < len(values):
        out.append({"id": new_id(), "v": values[cursor]})
        cursor += 1
    return out or [{"id": new_id(), "v": ""}]


# ---- 行内区间样式 ----
def _overlay(segments: list[tuple[int, int, Style]], start: int, end: int, style: Style):
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
        (start, end, style)
        for start, end, style in segments
        if end > start and style != Style()
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


def decode_style(raw: Any, lines: Sequence[Line]) -> StyleMap:
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


def line_styles(smap: StyleMap, line: Line) -> list[tuple[int, int, Style]]:
    """某一行解析后的样式区间（已按当前行长度裁剪）。"""
    text = line["v"]
    length = len(text) if isinstance(text, str) else 0
    resolved = _resolve(smap.get(line["id"], []))
    out: list[tuple[int, int, Style]] = []
    for start, end, style in resolved:
        start = max(0, min(start, length))
        end = max(0, min(end, length))
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
    from ...core.store import canonical

    payload = {
        "type": kind,
        "body": [line["v"] for line in lines],
        "style": signature_style(lines, smap),
    }
    return blake3(canonical(payload)).hexdigest()


__all__ = [
    "Line",
    "Marker",
    "RangeStyle",
    "StyleMap",
    "apply_text",
    "canonicalize_style",
    "coerce_style",
    "content_signature",
    "decode_style",
    "encode_style",
    "flatten_text",
    "is_marker",
    "line_styles",
    "new_id",
    "normalize_body",
    "signature_style",
]
