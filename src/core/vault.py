# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Vault：应用级门面，架在新存储（``Bucket`` / ``Block``）之上。

本层**不再有本地加密、空间、清单、分块**——那些都归入桶与块；
这里只把「对象」这个概念翻译成块，并提供检索与领域要用的查询。

- 对象 = 块（``Block``）：正文进 ``body``，标题 / 标签 / props 进 ``attrs``。
- 内容按 checksum 去重；对象身份是稳定 id。
- 版本不属于块：本门面只提供"当前版本"占位，具体版本策略留给领域层。
"""

from __future__ import annotations

import io
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any, BinaryIO

from .signal import (
    Event,
    EventBus,
    Handler,
    ObjectDeleted,
    ObjectPut,
    Signal,
    Subscription,
)
from .storage import Block, Bucket
from .types import (
    ObjectInfo,
    ObjectNotFoundError,
    Oid,
    VerifyReport,
    VersionInfo,
    now_ms,
)

Source = bytes | bytearray | memoryview | str | Path | BinaryIO


class Vault:
    """应用级门面：对象进、对象出。"""

    def __init__(self, root: Path | str, bucket: Bucket) -> None:
        self.root = Path(root)
        self.bucket = bucket
        self._signal = Signal()
        self._search = bucket.table("search", oid="TEXT PRIMARY KEY", body="TEXT")

    # ---- 生命周期 ----
    @classmethod
    def create(cls, path: Path | str, passphrase: str | None = None) -> Vault:
        del passphrase
        root = Path(path)
        bucket = Bucket.create(root)
        bucket.catalog.set_meta("created", str(now_ms()))
        bucket.commit()
        return cls(root, bucket)

    @classmethod
    def load(cls, path: Path | str) -> Vault:
        root = Path(path)
        return cls(root, Bucket.open(root))

    def unlock(self, passphrase: str | None = None) -> None:
        del passphrase

    def lock(self) -> None:
        return None

    @property
    def is_locked(self) -> bool:
        return False

    def close(self) -> None:
        self.bucket.close()

    # ---- 通信主干（存储事件 + 领域信号共用一条总线）----
    @property
    def signal(self) -> Signal:
        """通信主干：域服务在其上注册，存储事件与语义信号共用同一条总线。"""
        return self._signal

    @property
    def events(self) -> EventBus:
        """底层事件总线（块级事实通知）；即主干的投递器。"""
        return self._signal.events

    def subscribe(self, handler: Handler, event_type: type[Event] = Event) -> Subscription:
        return self._signal.events.subscribe(handler, event_type)

    # ---- 写 ----
    def put(  # noqa: PLR0913 — 写接口的显式参数面，均有默认值
        self,
        src: Source,
        *,
        type: str = "blob",
        mime: str | None = None,
        meta: dict[str, Any] | None = None,
        oid: Oid | str | None = None,
        search_text: str | None = None,
    ) -> Oid:
        payload = _read_source(src)
        attrs: dict[str, Any] = dict(meta or {})
        if mime is not None:
            attrs["mime"] = mime
        created = oid is None
        if oid is not None:
            target = str(oid)
            try:
                block = self.bucket.get(Block, target)
            except ObjectNotFoundError:
                block = Block(body=payload, attrs=attrs, type=type)
            else:
                block.body = payload
                block.attrs = attrs
                block.type = type
        else:
            block = Block(body=payload, attrs=attrs, type=type)
        self.bucket.put(block)
        self._set_search(block.id, search_text)
        result = Oid.parse(block.id)
        self._signal.events.emit(
            ObjectPut(
                oid=result,
                type=type,
                seq=1,
                created=created,
                checksum=str(block.checksum or ""),
            )
        )
        return result

    def put_meta(
        self,
        oid: Oid | str,
        *,
        meta: dict[str, Any] | None = None,
        search_text: str | None = None,
    ) -> Oid:
        target = str(oid)
        block = self.bucket.get(Block, target)
        merged = dict(block.attrs)
        if meta:
            merged.update(meta)
        block.attrs = merged
        self.bucket.put(block)
        self._set_search(target, search_text)
        return Oid.parse(target)

    def put_block(self, block: Block, *, search_text: str | None = None) -> Block:
        """存储一个块（含领域块），可选更新其检索文本；写入后发 ``ObjectPut``。"""
        created = not self.bucket.has(block.id)
        self.bucket.put(block)
        self._set_search(block.id, search_text)
        self._signal.events.emit(
            ObjectPut(
                oid=Oid.parse(block.id),
                type=block.type,
                seq=1,
                created=created,
                checksum=str(block.checksum or ""),
            )
        )
        return block

    def delete(self, oid: Oid | str) -> None:
        target = str(oid)
        if self.bucket.delete(target):
            self._search.delete(oid=target)
            self.bucket.commit()
            self._signal.events.emit(ObjectDeleted(oid=Oid.parse(target)))

    # ---- 读 ----
    def open(self, oid: Oid | str) -> io.BytesIO:
        return io.BytesIO(self._read_body(oid))

    def read(self, oid: Oid | str) -> bytes:
        return self._read_body(oid)

    def info(self, oid: Oid | str) -> ObjectInfo:
        return self._info(self.bucket.get(Block, str(oid)))

    def meta(self, oid: Oid | str) -> dict[str, Any]:
        return dict(self.bucket.get(Block, str(oid)).attrs)

    def iter(
        self,
        *,
        type: str | None = None,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
    ) -> Iterator[ObjectInfo]:
        wanted = _wanted_tags(tags)
        for block_id in self._block_ids(type):
            block = self.bucket.get(Block, block_id)
            if type is not None and block.type != type:
                continue
            info = self._info(block)
            if wanted and not _matches_tags(info.tags, wanted):
                continue
            yield info

    def _block_ids(self, type_name: str | None) -> Iterable[str]:
        """按类型取块 id：走 ``block.type`` 整数码索引，不扫全表。"""
        if type_name is None:
            return self.bucket.iter_block_ids()
        code = self.bucket.catalog.find_type_code(type_name)
        if code is None:
            return ()
        rows = self.bucket.query("SELECT oid FROM block WHERE type = ? ORDER BY oid", (code,))
        return [str(row["oid"]) for row in rows]

    def iter_object_ids(self) -> Iterator[Oid]:
        for block_id in self.bucket.iter_block_ids():
            yield Oid.parse(block_id)

    # ---- 版本（占位：块不管版本，具体策略留给领域层）----
    def versions(self, oid: Oid | str) -> list[VersionInfo]:
        block = self.bucket.get(Block, str(oid))
        body = block.body
        size = len(body) if isinstance(body, (bytes, bytearray)) else block.size
        return [
            VersionInfo(
                seq=1,
                updated=block.updated,
                size=size,
                is_current=True,
                author=str(block.attrs.get("author") or ""),
            )
        ]

    def read_version(self, oid: Oid | str, seq: int) -> bytes:
        if seq != 1:
            raise ObjectNotFoundError(f"版本不存在: {oid}@{seq}")
        return self._read_body(oid)

    def restore_version(self, oid: Oid | str, seq: int) -> Oid:
        if seq != 1:
            raise ObjectNotFoundError(f"版本不存在: {oid}@{seq}")
        return Oid.parse(str(oid))

    # ---- 检索 ----
    def search(self, query: str) -> list[Oid]:
        query = query.strip()
        if not query:
            return []
        rows = self.bucket.query("SELECT oid FROM search WHERE body LIKE ?", (f"%{query}%",))
        return [Oid.parse(str(row["oid"])) for row in rows]

    def index_is_empty(self) -> bool:
        return self._search.count() == 0

    def rebuild_index(self, *, text_of: Any = None) -> int:
        rows = self.bucket.query("SELECT oid FROM search")
        for row in rows:
            self._search.delete(oid=str(row["oid"]))
        count = 0
        for block_id in self.bucket.iter_block_ids():
            block = self.bucket.get(Block, block_id)
            info = self._info(block)
            text = text_of(info) if text_of is not None else None
            if text:
                self._search.insert({"oid": block_id, "body": text})
            count += 1
        self.bucket.commit()
        return count

    # ---- 维护 ----
    def gc(self, *, retention_ms: int | None = None) -> int:
        del retention_ms
        return 0

    def verify(self, *, deep: bool = False) -> VerifyReport:
        del deep
        problems: list[str] = []
        ids = list(self.bucket.iter_block_ids())
        for block_id in ids:
            try:
                self.bucket.get(Block, block_id)
            except Exception as exc:  # noqa: BLE001 — 巡检要收集所有问题，不能中断
                problems.append(f"{block_id}: {exc}")
        return VerifyReport(objects=len(ids), problems=tuple(problems))

    # ---- 内部 ----
    def _read_body(self, oid: Oid | str) -> bytes:
        body = self.bucket.get(Block, str(oid)).body
        return bytes(body) if not isinstance(body, bytes) else body

    def _info(self, block: Block) -> ObjectInfo:
        attrs = block.attrs
        body = block.body
        size = len(body) if isinstance(body, (bytes, bytearray)) else block.size
        return ObjectInfo(
            oid=Oid.parse(block.id),
            type=block.type,
            mime=attrs.get("mime"),
            size=size,
            created=block.created,
            updated=block.updated,
            title=attrs.get("title"),
            tags=_tags_of(attrs),
            seq=1,
            author=str(attrs.get("author") or ""),
        )

    def _set_search(self, block_id: str, search_text: str | None) -> None:
        self._search.delete(oid=block_id)
        if search_text:
            self._search.insert({"oid": block_id, "body": search_text})
        self.bucket.commit()


def _tags_of(attrs: Mapping[str, Any]) -> dict[str, Any]:
    raw = attrs.get("tags") or {}
    if isinstance(raw, Mapping):
        return {str(key): value for key, value in raw.items()}
    return {str(tag): None for tag in raw}


def _wanted_tags(tags: Iterable[str] | Mapping[str, Any] | None) -> dict[str, Any]:
    if tags is None:
        return {}
    if isinstance(tags, Mapping):
        return {str(key): value for key, value in tags.items()}
    return {str(tag): None for tag in tags}


def _matches_tags(have: dict[str, Any], wanted: dict[str, Any]) -> bool:
    for key, value in wanted.items():
        if key not in have:
            return False
        if value is not None and have.get(key) != value:
            return False
    return True


def _read_source(src: Source) -> bytes:
    if isinstance(src, bytes):
        return src
    if isinstance(src, (bytearray, memoryview)):
        return bytes(src)
    if isinstance(src, (str, Path)):
        return Path(src).read_bytes()
    return src.read()
