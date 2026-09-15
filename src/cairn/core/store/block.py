# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""块：只用于被继承的基类，也是存储的最小单位。

``Block`` 本身不用于直接实例化——它是**模式**。领域结构继承它，并重新描述：

    class Note(Block):
        type = "cairn.note"          # 承载类型（可 str / Enum）
        body = Body(factory=list)    # 重新描述 body 的形式与默认值
        title = Attr()               # 原生属性（config 也是属性）
        tags = Attr(factory=list)

        @classmethod
        def tables(cls):             # 领域自描述的业务表（含关联表）
            return {"notes": {...}, "note_relations": {...}}

字段：
    id        稳定身份（OID），创建时分配，**锁死**不可改
    checksum  内容校验哈希，由 type+body+attrs 推出
    type      承载类型（str / Enum）
    body      主体，由子类用 ``Body(...)`` 重新描述
    attrs     原生属性，用 ``Attr`` 声明（config 也是属性）
    config    写入配置：保留键驱动写入行为（如 ``isolated`` 独占载体）
    size      内容字节数
    created   创建时间（unix ms）
    updated   最近写入时间（unix ms）

版本（rev / prev / 历史）**不属于块**：块是纯粹的存储单元，版本是项目 / 笔记
各自的事，而项目走 git 式、笔记走另一套，策略本就不同。

读写不碰事务，也看不到 catalog / pack：把**整个对象**交给桶即可——

    note = bucket.new(Note)      # 拿到一个可编辑对象（id 已分配）
    note.title = "第一则"
    note.body.append("正文")
    bucket.put(note)             # 一次调用即落盘；不碰任何事务

    same = bucket.get(Note, note.id)   # 按稳定 id 取回，仍是可编辑对象
"""

from __future__ import annotations

import builtins
from collections.abc import Callable, Iterable, Iterator, Mapping
from enum import Enum
from typing import Any, ClassVar, Self

import cbor2
from blake3 import blake3

from ...types import CairnError, CorruptObjectError, Oid

BLOCK_VERSION = 1

INDEX_TYPE = "cairn.index"
PART_TYPE = "cairn.part"

_MISSING = object()


def canonical(obj: Any) -> bytes:
    """确定性 CBOR 编码：同一结构字节唯一，服务 checksum / 去重。"""
    return cbor2.dumps(obj, canonical=True)


def decode_canonical(data: bytes) -> Any:
    """解码 ``canonical`` 的输出。"""
    return cbor2.loads(data)


def _digest(payload: bytes) -> str:
    return blake3(payload).hexdigest()


def _type_name(value: str | Enum) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


class Attr:
    """原生属性的声明：读写都落在 ``Block.attrs`` 上。

    ``item=`` 用于列表字段：存储里是紧凑数据（dict），取出来是类型化对象。
    元素类型需提供 ``to_data()`` / ``from_data()``。
    """

    def __init__(
        self,
        default: Any = _MISSING,
        *,
        factory: Callable[[], Any] | None = None,
        item: Any = None,
    ) -> None:
        self._default = default
        self._factory = factory
        self._item = item
        self.key = ""

    def __set_name__(self, _owner: type, name: str) -> None:
        self.key = name

    def _initial(self) -> Any:
        if self._factory is not None:
            return self._factory()
        return None if self._default is _MISSING else self._default

    def _decode(self, value: Any) -> Any:
        if isinstance(value, self._item):
            return value
        if hasattr(self._item, "from_data"):
            return self._item.from_data(value)
        return self._item(**value)

    def _encode(self, value: Any) -> Any:
        return value.to_data() if hasattr(value, "to_data") else value

    def __get__(self, obj: Block | None, _owner: type | None = None) -> Any:
        if obj is None:
            return self
        if self.key not in obj.attrs:
            if self._factory is not None or self._default is not _MISSING:
                obj.attrs[self.key] = self._initial()
            else:
                return None
        value = obj.attrs[self.key]
        if self._item is not None and isinstance(value, (list, tuple)):
            return [self._decode(entry) for entry in value]
        return value

    def __set__(self, obj: Block, value: Any) -> None:
        if self._item is not None and isinstance(value, (list, tuple)):
            value = [self._encode(entry) for entry in value]
        obj.attrs[self.key] = value


class Body:
    """主体字段的声明：子类用它重新描述 body 的形式与默认值。"""

    def __init__(
        self,
        default: Any = _MISSING,
        *,
        factory: Callable[[], Any] | None = None,
    ) -> None:
        self._default = default
        self._factory = factory

    def _initial(self) -> Any:
        if self._factory is not None:
            return self._factory()
        return None if self._default is _MISSING else self._default

    def __get__(self, obj: Block | None, _owner: type | None = None) -> Any:
        if obj is None:
            return self
        if "_body" not in obj.__dict__:
            obj.__dict__["_body"] = self._initial()
        return obj.__dict__["_body"]

    def __set__(self, obj: Block, value: Any) -> None:
        obj.__dict__["_body"] = value


class Block:
    """所有内容类型的基类。字段架构由子类重新描述。"""

    type: str = "cairn.block"
    kind: str = "cairn.block"
    body = Body()
    _REGISTRY: ClassVar[dict[str, builtins.type[Block]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        declared = cls.__dict__.get("type")
        if declared is not None:
            Block._REGISTRY[_type_name(declared)] = cls
        if "kind" not in cls.__dict__:
            cls.kind = cls.type

    # ---- 领域自描述与绑定（由桶在挂载 / 写入时调用）----
    @classmethod
    def tables(cls) -> dict[str, dict[str, str]]:
        """领域自描述的业务表：``{表名: {列名: 类型/约束}}``，可含关联表。"""
        return {}

    @classmethod
    def bind(cls, bucket: Any) -> None:
        """领域绑定：默认把 ``tables()`` 声明建出来；子类可重写加关联动作。"""
        for name, columns in cls.tables().items():
            bucket.table(name, **columns)

    def __init__(
        self,
        *,
        id: str | None = None,
        body: Any = _MISSING,
        attrs: dict[str, Any] | None = None,
        type: str | Enum | None = None,
        checksum: str | None = None,
        config: dict[str, Any] | None = None,
        author: str = "",
        created: int = 0,
        updated: int = 0,
        size: int = 0,
    ) -> None:
        self._id: str | None = None
        self.id = id if id is not None else str(Oid.new())
        self.type = _type_name(type if type is not None else self.__class__.type)
        if body is not _MISSING:
            self.body = body
        self.attrs: dict[str, Any] = dict(attrs or {})
        self.checksum = checksum
        self.config: dict[str, Any] = dict(config or {})
        self.author = author
        self.created = created
        self.updated = updated
        self.size = size
        self._vault: Any = None
        self._info: Any = None

    def validate(self) -> None:
        """写入前的校验；子类重写，非法即抛异常。默认放行。"""
        return None

    # id 锁死：创建后不可改
    @property
    def id(self) -> str:
        assert self._id is not None
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        if self._id is not None and value != self._id:
            raise AttributeError("块 id 不可修改")
        self._id = value

    def content(self) -> dict[str, Any]:
        """参与 checksum 的内容（不含 id / checksum）。"""
        return {"type": self.type, "body": self.body, "attrs": self.attrs}

    def compute_checksum(self) -> str:
        return _digest(canonical(self.content()))

    def content_size(self) -> int:
        """主体字节数：bytes 取长度，其余取确定性编码长度。"""
        if isinstance(self.body, (bytes, bytearray)):
            return len(self.body)
        return len(canonical(self.body))

    def encode(self) -> bytes:
        """编码为落盘内容（不含 id：内容按 checksum 去重）。"""
        return canonical(
            {
                "v": BLOCK_VERSION,
                "type": self.type,
                "body": self.body,
                "attrs": self.attrs,
            }
        )

    @classmethod
    def decode(cls, data: bytes, *, id: str | None = None) -> Block:
        """解码内容为对应 ``type`` 的子类；未知类型退回基类。"""
        try:
            raw = cbor2.loads(data)
            content = {
                "type": str(raw["type"]),
                "body": raw.get("body"),
                "attrs": raw.get("attrs") or {},
            }
            target = Block._REGISTRY.get(content["type"], Block)
            return target(
                id=id,
                body=content["body"],
                attrs=content["attrs"],
                type=content["type"],
                checksum=_digest(canonical(content)),
            )
        except (cbor2.CBORDecodeError, KeyError, TypeError, ValueError) as exc:
            raise CorruptObjectError("块解析失败") from exc

    def verify(self) -> bool:
        """重算 checksum，校验内容未被篡改。"""
        return self.checksum == self.compute_checksum()

    @classmethod
    def new(cls) -> Block:
        """新建一个空对象，id 已分配。"""
        return cls()

    # ---- 绑定库之后的通用读写（save / load / list）----
    # 领域结构直接继承本类，不再有中间层；这些方法对任何块都通用。
    @property
    def oid(self) -> Oid:
        return Oid.parse(self.id)

    @property
    def info(self) -> Any:
        if self._info is None:
            raise CairnError("块未绑定库：请用 create / load")
        return self._info

    @property
    def space_id(self) -> Any:
        if self._vault is None:
            raise CairnError("块未绑定库")
        return self._vault.space().space_id

    @property
    def title(self) -> str | None:
        value = self.attrs.get("title")
        return None if value is None else str(value)

    @title.setter
    def title(self, value: str | None) -> None:
        self.attrs["title"] = None if value is None else str(value)

    @property
    def tags(self) -> dict[str, str | None]:
        """标签：``{键: 值}``；纯标签的值为 ``None``（也兼容旧的纯列表写法）。"""
        raw = self.attrs.get("tags") or {}
        if isinstance(raw, Mapping):
            return {str(key): (None if value is None else str(value)) for key, value in raw.items()}
        return {str(tag): None for tag in raw}

    @tags.setter
    def tags(self, value: Iterable[str] | Mapping[str, Any]) -> None:
        if isinstance(value, Mapping):
            self.attrs["tags"] = {
                str(key): (None if item is None else str(item)) for key, item in value.items()
            }
        else:
            self.attrs["tags"] = {str(tag): None for tag in value}

    @property
    def authors(self) -> list[Any]:
        """署名作者（有序：一作、二作…）；``author`` 是原作者。"""
        return list(self.attrs.get("authors") or ())

    @authors.setter
    def authors(self, value: Iterable[Any]) -> None:
        self.attrs["authors"] = list(value)

    def meta(self) -> dict[str, Any]:
        return dict(self.attrs)

    def props(self) -> dict[str, Any]:
        return dict(self.attrs.get("props") or {})

    def read(self) -> bytes:
        body = self.body
        return bytes(body) if not isinstance(body, bytes) else body

    def delete(self) -> None:
        self._require_vault().delete(self.id)

    def save(self, *, search_text: str | None = None) -> Self:
        vault = self._require_vault()
        vault.put_block(self, search_text=search_text)
        self._refresh()
        return self

    def _refresh(self) -> None:
        self._info = self._require_vault().info(self.id)

    def _require_vault(self) -> Any:
        if self._vault is None:
            raise CairnError("块未绑定库：请用 create / load")
        return self._vault

    @classmethod
    def load(cls, vault: Any, oid: Oid | str) -> Self:
        block: Any = vault.bucket.get(cls, str(oid))
        block._vault = vault
        block._info = vault.info(block.id)
        return block

    @classmethod
    def list(
        cls,
        vault: Any,
        *,
        tags: Iterable[str] | None = None,
    ) -> Iterator[Self]:
        for info in vault.iter(type=cls.type, tags=tags):
            yield cls.load(vault, info.oid)


__all__ = [
    "BLOCK_VERSION",
    "INDEX_TYPE",
    "PART_TYPE",
    "Attr",
    "Block",
    "Body",
    "canonical",
    "decode_canonical",
]
