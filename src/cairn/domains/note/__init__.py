# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记领域：类型与行为都在 ``types`` / ``model`` / ``edit``，这里只做转出。"""

from __future__ import annotations

from .edit import (
    Line,
    Marker,
    StyleMap,
    content_signature,
    flatten_text,
    is_marker,
    new_id,
    normalize_body,
)
from .model import (
    NOTE_KIND,
    NOTE_MIME,
    NOTE_SCHEMA,
    Access,
    Canvas,
    Form,
    Graphic,
    Link,
    Paint,
    Segment,
    Style,
    Text,
)
from .model import (
    Line as LineKind,
)
from .shapes import ShapeSet, ShapeSpec, build_vertices, graphic_from, load_shape_set
from .types import Note, access_ref, canvas_ref
from .versions import NOTE_CODEC

__all__ = [
    "NOTE_CODEC",
    "NOTE_KIND",
    "NOTE_MIME",
    "NOTE_SCHEMA",
    "Access",
    "Canvas",
    "Form",
    "Graphic",
    "Line",
    "LineKind",
    "Link",
    "Marker",
    "Note",
    "Paint",
    "Segment",
    "ShapeSet",
    "ShapeSpec",
    "Style",
    "StyleMap",
    "Text",
    "access_ref",
    "build_vertices",
    "canvas_ref",
    "content_signature",
    "flatten_text",
    "graphic_from",
    "is_marker",
    "load_shape_set",
    "new_id",
    "normalize_body",
]
