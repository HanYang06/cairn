# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记领域：类型与行为都在 ``types`` / ``model`` / ``edit``，这里只做转出。"""

from __future__ import annotations

from .body import NoteBody
from .data import NoteData, access_ref, canvas_ref
from .edit.body import (
    Line as LineDict,
)
from .edit.body import (
    Marker,
    is_marker,
    new_id,
    normalize_body,
)
from .edit.style import StyleMap, content_signature
from .edit.text import flatten_text
from .model import (
    NOTE_KIND,
    NOTE_MIME,
    NOTE_SCHEMA,
    CanvasBody,
    CanvasData,
    Form,
    Graphic,
    Line,
    Link,
    Paint,
    Segment,
    Style,
    Text,
)
from .model import (
    Line as LineKind,
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
