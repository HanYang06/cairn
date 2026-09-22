# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Vault：应用级门面，架在存储（``Bucket`` / ``Block``）之上。

本层**不再有本地加密、空间、清单、分块、版本**——那些都归入桶与块；
这里只把「对象」翻译成块，并提供检索与领域要用的查询。

- 对象 = 块（``Block``）：正文进 ``body``，标题 / 标签 / props 进 ``attrs``。
- 内容按 checksum 去重；对象身份是稳定 id。
- 版本不属于块：领域层用通用 ``VersionStore`` 自行承载。
"""

from __future__ import annotations

import io
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

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
from .types import ObjectInfo, Oid, VerifyReport, now_ms, type_name


class Vault:
    """应用级门面：对象进、对象出。"""

    def __init__(self, root: Path | str, bucket: Bucket) -> None:
        self.root = Path(root)
        self.bucket = bucket
        self._signal = Signal()
        self._search = bucket.table("search", oid="TEXT PRIMARY KEY", body="TEXT")

    # ---- 生命周期 ----
    @classmethod
    def create(cls, path: Path | str) -> Vault:
        root = Path(path)
        bucket = Bucket.create(root)
        bucket.catalog.set_meta("created", str(now_ms()))
        bucket.commit()
        return cls(root, bucket)

    @classmethod
    def load(cls, path: Path | str) -> Vault:
        root = Path(path)
        return cls(root, Bucket.open(root))

    def close(self) -> None:
        self.bucket.close()

    # ---- 通信主干（存储事件 + 领域信号共用一条总线）----
    @property
    def signal(self) -> Signal:
        """通信主干：域服务在其上静态挂载，存储事件与语义信号共用同一条总线。"""
        return self._signal

    @property
    def events(self) -> EventBus:
        """底层事件总线（块级事实通知）；即主干的投递器。"""
        return self._signal.events

    def subscribe(self, handler: Handler, event_type: type[Event] = Event) -> Subscription:
        return self._signal.events.subscribe(handler, event_type)

    # ---- 写 ----
    def put_block(self, block: Block, *, search_text: str | None = None) -> Block:
        """存储一个块（含领域块），可选更新其检索文本；写入后发 ``ObjectPut``。"""
        created = not self.bucket.has(block.id)
        self.bucket.put(block)
        if search_text is not None:
            self._set_search(block.id, search_text)
        self._signal.events.emit(
            ObjectPut(
                oid=Oid.parse(block.id),
                type=type_name(block.type),
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
            if type is not None and block.type != type_name(type):
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

    # ---- 检索 ----
    def search(self, query: str) -> list[Oid]:
        query = query.strip()
        if not query:
            return []
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        rows = self.bucket.query(
            "SELECT oid FROM search WHERE body LIKE ? ESCAPE '\\'", (f"%{escaped}%",)
        )
        return [Oid.parse(str(row["oid"])) for row in rows]

    def index_is_empty(self) -> bool:
        return self._search.count() == 0

    def rebuild_index(self, *, text_of: Any = None) -> int:
        """重建检索索引；``text_of`` 从对象信息提取检索文本，必填（否则会清空索引）。

        返回实际写入的条目数。
        """
        if text_of is None:
            raise ValueError("rebuild_index 需要 text_of 提取检索文本")
        rows = self.bucket.query("SELECT oid FROM search")
        for row in rows:
            self._search.delete(oid=str(row["oid"]))
        written = 0
        for block_id in self.bucket.iter_block_ids():
            block = self.bucket.get(Block, block_id)
            text = text_of(self._info(block))
            if text:
                self._search.insert({"oid": block_id, "body": text})
                written += 1
        self.bucket.commit()
        return written

    # ---- 维护 ----
    def gc(self, *, retention_ms: int | None = None) -> int:
        """回收未引用内容；**尚未实现**（勿静默返回 0 误导调用方）。"""
        del retention_ms
        raise NotImplementedError("pack 压实 / gc 尚未实现")

    def verify(self, *, deep: bool = False) -> VerifyReport:
        if deep:
            raise NotImplementedError("深度校验尚未实现")
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
            type=type_name(block.type),
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
    if isinstance(raw, str):
        return {raw: None} if raw else {}
    return {str(tag): None for tag in raw}


def _wanted_tags(tags: Iterable[str] | Mapping[str, Any] | None) -> dict[str, Any]:
    if tags is None:
        return {}
    if isinstance(tags, str):
        return {tags: None} if tags else {}
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
