# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""资产领域：**数据**（``AssetData``）与**域服务**（``Asset``）分离。

- ``AssetData(Block)``：非文本内容（图 / 声 / 视等）纯数据 + 属性。
- ``Asset(Domain)``：域服务——入库/载入，入库第一件事是**转码**（草案：恒等），再交桶存储。

分片不由资产处理——``Block`` / 桶已自带。
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, ClassVar

from core.signal import Domain, action
from core.storage import Attr, Block, BodyField

from .base import normalize_tags

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from core.types import Oid

ASSET_KIND = "cairn.asset"
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
    return source.read()


class AssetData(Block):
    """资产数据块：非文本内容 + 属性（纯数据）。"""

    type = ASSET_KIND
    body = BodyField()
    mime: ClassVar[str | None] = None

    schema: Attr[int] = ASSET_SCHEMA
    title: Attr[str | None] = None
    tags: Attr = Attr(factory=dict, coerce=normalize_tags)
    name: Attr[str | None] = None
    origin_mime: Attr[str | None] = None  # 转码前的原始编码，留作来源记录

    @property
    def content_type(self) -> str | None:
        value = self.attrs.get("mime")
        return None if value is None else str(value)


class Asset(Domain):
    """资产域服务（单例）：入库（转码）/ 载入。"""

    name = "Asset"

    def __init__(self, vault: Any) -> None:
        self.vault = vault

    @action
    def create(
        self,
        source: Source,
        *,
        name: str | None = None,
        mime: str | None = None,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> AssetData:
        """入库一个资产：先转码，再落盘。"""
        data = AssetData()
        data._vault = self.vault  # noqa: SLF001 — 服务为数据绑定库
        raw = _read_source(source)
        original = mime or (mimetypes.guess_type(name)[0] if name else None)
        encoded, unified = transcode(raw, original)  # ← 入库先转码
        data.body = encoded
        data.attrs["name"] = None if name is None else str(name)
        data.attrs["mime"] = unified
        data.attrs["origin_mime"] = original
        data.title = name
        data.tags = tags or {}
        if props:
            data.attrs["props"] = dict(props)
        data.save()
        return data

    @action
    def load(self, oid: Oid | str) -> AssetData:
        """按 oid 载入资产数据。"""
        data: AssetData = AssetData.load(self.vault, oid)
        return data


__all__ = [
    "ASSET_KIND",
    "ASSET_SCHEMA",
    "UNIFIED_CODECS",
    "Asset",
    "AssetData",
    "transcode",
    "unified_target",
]
