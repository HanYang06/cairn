"""领域通用数据结构（基板片段等）。"""

from __future__ import annotations

from .substrate import (
    decode_substrate,
    embed_fragment,
    encode_substrate,
    plain_text,
    ref_fragment,
    referenced_oids,
    text_fragment,
)

__all__ = [
    "decode_substrate",
    "embed_fragment",
    "encode_substrate",
    "plain_text",
    "ref_fragment",
    "referenced_oids",
    "text_fragment",
]
