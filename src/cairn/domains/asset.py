"""资产领域（存储）：任意二进制对象——图 / 声 / 视频 / 文件。

资产是不可变内容；笔记通过对象引用（OID）嵌入它，而非内联。
"""

from __future__ import annotations

import mimetypes
from typing import Any, BinaryIO, ClassVar, Self

from ..core.types import SpaceId
from .base import DomainObject, get_handler, register

ASSET_KIND = "cairn.asset"
ASSET_SCHEMA = 1

Source = bytes | bytearray | memoryview | str | BinaryIO


class AssetHandler:
    kind: str = ASSET_KIND
    schema_version: int = ASSET_SCHEMA

    def normalize_meta(self, **fields: Any) -> dict[str, Any]:
        props = dict(fields.get("props") or {})
        name = fields.get("name")
        if name is not None:
            props["name"] = str(name)
        return {
            "title": None if name is None else str(name),
            "tags": [str(tag) for tag in (fields.get("tags") or ())],
            "schema": ASSET_SCHEMA,
            "props": props,
        }


register(AssetHandler())


class Asset(DomainObject):
    kind: ClassVar[str] = ASSET_KIND
    schema_version: ClassVar[int] = ASSET_SCHEMA

    @classmethod
    def create(
        cls,
        vault: Any,
        source: Source,
        *,
        name: str | None = None,
        mime: str | None = None,
        tags: list[str] | None = None,
        props: dict[str, Any] | None = None,
        space: str | SpaceId = "default",
    ) -> Self:
        resolved_mime = mime or (mimetypes.guess_type(name)[0] if name else None)
        meta = get_handler(cls.kind).normalize_meta(name=name, tags=tags, props=props)
        oid = vault.put(source, space=space, type=cls.kind, mime=resolved_mime, meta=meta)
        return cls.load(vault, oid)

    @property
    def name(self) -> str | None:
        return self.props().get("name")

    @property
    def content_type(self) -> str | None:
        return self._info.mime

    @property
    def size(self) -> int:
        return self._info.size
