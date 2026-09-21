# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""行编辑原语（按关注点分三块，**不引类**——纯变换就该是函数）。

- `body`：行身份与行结构（id / 嵌入占位 / 规范化 / 超长判定）
- `text`：行级文本操作（拍平 / 整段替换 / 增删 / 拆合）
- `style`：行内区间样式（规范化 / 编解码 / 读写）

> 本 `__init__` 只做**兼容转出**（拆包前是单模块 `edit.py`）；新代码请直接
> `from .edit import body, style, text` 或从子模块具名导入。
"""

from __future__ import annotations

from .body import (
    OVERLONG_WEIGHT,
    Line,
    Marker,
    is_marker,
    new_id,
    normalize_body,
    text_weight,
)
from .style import (
    StyleMap,
    clear_range_style,
    coerce_style,
    content_signature,
    drop_style,
    encode_style,
    line_styles,
    merge_style,
    set_range_style,
    signature_style,
    split_style,
    toggle_range_style,
)
from .text import (
    apply_text,
    flatten_text,
    insert_line,
    merge_line,
    remove_line,
    set_line_text,
    split_line,
)

__all__ = [
    "OVERLONG_WEIGHT",
    "Line",
    "Marker",
    "StyleMap",
    "apply_text",
    "clear_range_style",
    "coerce_style",
    "content_signature",
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
    "text_weight",
    "toggle_range_style",
]
