# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""资产领域：继承 ``Block`` 的多媒体对象——图 / 声 / 视频 / 文件。

与其它领域不同，资产**入库第一件事是转码**：无论原始编码是什么，先统一转成
一套最优编码，再交给桶存储。分片不由资产处理——``Block`` / 桶已经自带。
"""

from __future__ import annotations

import mimetypes
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, BinaryIO, ClassVar, Self

from ..core.store import Attr, Block, Body
from .base import normalize_tags

ASSET_KIND = "cairn.asset"
ASSET_SCHEMA = 1

Source = bytes | bytearray | memoryview | str | Path | BinaryIO

# 统一编码（**草案**）：所有多媒体转码到这套编码后再落盘。
# 只留决策位；真正实现要选定编解码库，且必须过许可关（禁止 GPL/AGPL）。
UNIFIED_CODECS: dict[str, str] = {
    "image": "image/png",      # 候选：PNG / WebP（无损）
    "audio": "audio/flac",     # 候选：FLAC
    "video": "video/ffv1",     # 候选：FFV1（无专利，待核实工具许可）
}


def _kind_of(mime: str | None) -> str | None:
    if not mime:
        return None
    return mime.split("/", 1)[0]


def unified_target(mime: str | None) -> str | None:
    """该媒体应转成的统一编码；无匹配则返回 ``None``。"""
    return UNIFIED_CODECS.get(_kind_of(mime) or "")


def transcode(data: bytes, mime: str | None) -> tuple[bytes, str | None]:
    """把原始字节转码为统一编码，返回 ``(字节, mime)``。

    状态：**草案**——默认恒等（不转码）。真正实现落在这里：按 ``unified_target``
    调用选定库重新编码；转码器未就绪时应保持恒等，绝不静默降质。
    """
    return data, mime


def _read_source(source: Source) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, (bytearray, memoryview)):
        return bytes(source)
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes()
    return source.read()


class Asset(Block):
    type = ASSET_KIND
    body = Body()
    mime: ClassVar[str | None] = None

    schema: Attr[int] = ASSET_SCHEMA
    title: Attr[str | None] = None
    tags: Attr = Attr(factory=dict, coerce=normalize_tags)
    name: Attr[str | None] = None
    origin_mime: Attr[str | None] = None    # 转码前的原始编码，留作来源记录

    @classmethod
    def create(
        cls,
        vault: Any,
        source: Source,
        *,
        name: str | None = None,
        mime: str | None = None,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> Self:
        asset = cls()
        asset._vault = vault
        raw = _read_source(source)
        original = mime or (mimetypes.guess_type(name)[0] if name else None)
        encoded, unified = transcode(raw, original)      # ← 入库先转码
        asset.body = encoded
        asset.attrs["name"] = None if name is None else str(name)
        asset.attrs["mime"] = unified
        asset.attrs["origin_mime"] = original
        asset.title = name
        asset.tags = tags or {}
        if props:
            asset.attrs["props"] = dict(props)
        asset.save()
        return asset

    @property
    def content_type(self) -> str | None:
        value = self.attrs.get("mime")
        return None if value is None else str(value)


__all__ = ["ASSET_KIND", "ASSET_SCHEMA", "UNIFIED_CODECS", "Asset", "transcode", "unified_target"]
