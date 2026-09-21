# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记领域：数据描述在 ``data``、操作在 ``edit`` / ``service``，这里只做转出。"""

from __future__ import annotations

from .data import (
    NOTE_KIND,
    NOTE_MIME,
    NOTE_SCHEMA,
    CanvasBody,
    CanvasData,
    Form,
    Graphic,
    Line,
    Link,
    NoteBody,
    NoteData,
    Paint,
    Segment,
    Text,
    access_ref,
    canvas_ref,
)
from .data import (
    Line as LineKind,
)
from .edit import (
    Line as LineDict,
)
from .edit import (
    Marker,
    Style,
    StyleMap,
    content_signature,
    flatten_text,
    is_marker,
    new_id,
    normalize_body,
)
from .service import Note
from .shapes import ShapeSet, ShapeSpec, build_vertices, graphic_from, load_shape_set
from .versions import NOTE_CODEC

__all__ = [
    "NOTE_CODEC",
    "NOTE_KIND",
    "NOTE_MIME",
    "NOTE_SCHEMA",
    "CanvasBody",
    "CanvasData",
    "Form",
    "Graphic",
    "Line",
    "LineDict",
    "LineKind",
    "Link",
    "Marker",
    "Note",
    "NoteBody",
    "NoteData",
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
