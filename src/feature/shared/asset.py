# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""资产：**存储数据结构**（``AssetData(Block)``），不是域。

- ``AssetData``：非文本内容（图 / 声 / 视等）纯数据 + 属性；构造入口 ``create`` 先转码再落盘。
- 它只是数据形态，由需要的域（Note / Project…）在用到时使用。

分片不由资产处理——``Block`` / 桶已自带。
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

from core.storage import Attr, Block, BodyField

from .base import normalize_tags
from .kinds import Kind

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

ASSET_KIND = Kind.Data.Asset
ASSET_SCHEMA = 1

Source = bytes | bytearray | memoryview | str | Path | BinaryIO

# 统一编码（**草案**）：所有多媒体转码到这套编码后再落盘。
# 只留决策位；真正实现要选定编解码库，且必须过许可关（禁止 GPL/AGPL）。
UNIFIED_CODECS: dict[str, str] = {
    "image": "image/png",  # 候选：PNG / WebP（无损）
    "audio": "audio/flac",  # 候选：FLAC
    "video": "video/ffv1",  # 候选：FFV1（无专利，待核实工具许可）
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
    payload = source.read()
    if not isinstance(payload, (bytes, bytearray, memoryview)):
        raise TypeError("资产源必须返回 bytes（不要用文本模式打开）")
    return bytes(payload)


class AssetData(Block):
    """资产数据块：非文本内容 + 属性（纯数据）。"""

    type = ASSET_KIND
    body = BodyField()

    schema: Attr[int] = ASSET_SCHEMA
    title: Attr[str | None] = None
    tags: Attr = Attr(factory=dict, coerce=normalize_tags)
    name: Attr[str | None] = None
    mime: Attr[str | None] = None  # 转码后的统一编码（逐实例，落在 attrs）
    origin_mime: Attr[str | None] = None  # 转码前的原始编码，留作来源记录

    @property
    def content_type(self) -> str | None:
        """统一后的媒体类型（``mime`` 字段的读法别名）。"""
        return self.mime

    @classmethod
    def create(  # noqa: PLR0913 — 构造入口参数面，均有默认值
        cls,
        vault: Any,
        source: Source,
        *,
        name: str | None = None,
        mime: str | None = None,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> AssetData:
        """入库一个资产：先转码，再落盘（数据结构的构造入口）。"""
        data = cls()
        data._vault = vault
        raw = _read_source(source)
        original = mime or (mimetypes.guess_type(name)[0] if name else None)
        encoded, unified = transcode(raw, original)  # ← 入库先转码
        data.body = encoded
        data.name = None if name is None else str(name)
        data.mime = unified
        data.origin_mime = original
        data.title = name
        data.tags = tags or {}
        if props:
            data.attrs["props"] = dict(props)
        data.save()
        return data


__all__ = [
    "ASSET_KIND",
    "ASSET_SCHEMA",
    "UNIFIED_CODECS",
    "AssetData",
    "transcode",
    "unified_target",
]
