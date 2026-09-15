# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记领域：类型与行为都在 ``types``，这里只做转出。"""

from __future__ import annotations

from .shapes import ShapeSet, ShapeSpec, build_vertices, graphic_from, load_shape_set
from .types import (
    NOTE_KIND,
    NOTE_MIME,
    NOTE_SCHEMA,
    Canvas,
    Form,
    Graphic,
    Line,
    Link,
    Note,
    Paint,
    Segment,
    Style,
    bare,
    blank_styles,
    canvas_ref,
    normalize,
)

__all__ = [
    "NOTE_KIND",
    "NOTE_MIME",
    "NOTE_SCHEMA",
    "Canvas",
    "Form",
    "Graphic",
    "Line",
    "Link",
    "Note",
    "Paint",
    "Segment",
    "ShapeSet",
    "ShapeSpec",
    "Style",
    "bare",
    "blank_styles",
    "build_vertices",
    "canvas_ref",
    "graphic_from",
    "load_shape_set",
    "normalize",
]
