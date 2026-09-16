# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""块（Block）：唯一被存进桶的东西，也是所有领域结构的**基类**。

``Block`` 本身不直接实例化（未登记的 ``type`` 会退回它，作为裸块）。领域结构继承它，
用 ``Attr`` / ``Body`` 重新描述字段。它是**面向存储/硬件**的、自利自足的：
只关心「怎么把这块内容存下去、取回来」，不关心上层业务语义。

字段一览（子类可重新描述 body / attrs，不可动 id 与 checksum 口径）：

    id        稳定身份（OID，ULID），创建时分配，**锁死不可改**
    checksum  内容签名（BLAKE3 十六进制），由 ``content()`` 推出；子类可覆写口径
    type      承载类型（str / Enum），如 ``cairn.note``
    body      主体，由子类用 ``Body(...)`` 重新描述（默认是裸 Body）
    attrs     原生属性，用 ``Attr`` 声明；**领域数据都放这里**（含 config 之外的一切）
    config    写入配置：驱动写入行为（如 ``isolated`` 独占载体）
    author    作者（存储写入者）
    size      主体字节数（bytes 取长度，其余取确定性编码长度）
    created   创建时间（unix 毫秒）
    updated   最近写入时间（unix 毫秒）

铁律 / 约定（谁都不许破）：

1. **id 锁死**：创建即分配，之后不可改（改则抛 ``AttributeError``）。
2. **checksum 是 body 哈希**：``body_hash()`` 只算 body（不含 id / attrs / 签名），
   桶据此在**内容池**里按哈希去重——同 body 复用同一份内容。子类可覆写口径
   （如笔记剥离行 id、把行内样式算入）。attrs 随块行单独存，不参与去重。
3. **decode 用子类口径重算**：读回时由「body 字节 + attrs」拼合，再调 ``compute_checksum()``，
   保证与 ``put`` 时一致（否则覆写了口径的领域对象会读回失败）。
4. **块不承载版本**：版本是笔记 / 项目各自的策略（走 ``VersionStore``），块只存当前内容。
5. **去重发生在领域层**：小内容按 checksum 共享物理内容；分片块（PART/INDEX）不去重。
6. **读写不碰事务、不碰目录**：把整个对象交给桶即可；事务由桶统一收口。

用法：

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
from typing import Any, ClassVar, Self, get_origin

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


class Attr[T = Any]:
    """原生属性的声明：读写都落在 ``Block.attrs`` 上。

    注解里写 ``signature: Attr[Signature]``，语义是「这个字段是 Attr，承载 ``Signature`` 类型」。
    两个参数决定取值形态：

    - ``default`` / ``factory``：字段缺失时的默认值（二选一）。
    - ``item``：**类型化列表 / 类型化值**。给列表字段时，存储里是紧凑数据（dict），
      取出来是类型化对象；元素类型需提供 ``to_data()`` / ``from_data()``。
      单个类型化值（非列表）同样走 ``to_data()``。
    """

    def __init__(
        self,
        default: Any = _MISSING,
        *,
        factory: Callable[[], Any] | None = None,
        item: type[T] | None = None,
        coerce: Callable[[Any], Any] | None = None,
    ) -> None:
        self._default = default
        self._factory = factory
        self._item: Any = item
        self._coerce = coerce
        self.key = ""

    def __set_name__(self, _owner: type, name: str) -> None:
        self.key = name

    def _initial(self) -> Any:
        if self._factory is not None:
            return self._factory()
        raw = None if self._default is _MISSING else self._default
        # item 字段的默认值要落成数据形态（如 Signature 对象 → dict）
        if self._item is not None and raw is not None and hasattr(raw, "to_data"):
            return self._encode(raw)
        return raw

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
        if self._item is not None:
            if isinstance(value, (list, tuple)):
                return [self._decode(entry) for entry in value]
            if isinstance(value, Mapping):
                return self._decode(value)
        return value

    def __set__(self, obj: Block, value: Any) -> None:
        if self._coerce is not None and value is not None:
            value = self._coerce(value)
        if self._item is not None:
            if isinstance(value, (list, tuple)):
                value = [self._encode(entry) for entry in value]
            elif value is not None and hasattr(value, "to_data"):
                value = self._encode(value)
        obj.attrs[self.key] = value


class Body[T = Any]:
    """主体字段的声明：子类用它重新描述 body 的形式与默认值。

    默认实现是「惰性初始化」：首次读取时按 ``factory`` / ``default`` 建值，之后存在
    ``obj.__dict__['_body']`` 里。领域若要更复杂的 body（如笔记的行序列 + 稳定行 id），
    写自己的描述符替换即可——``Block`` 只要求 ``body`` 可读可写、可被 ``canonical`` 编码。
    """

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


def _is_attr_annotation(annotation: Any) -> bool:
    """注解是否是 ``Attr`` / ``Attr[T]``（用于把类体裸值包成字段）。"""
    if isinstance(annotation, str):
        return annotation == "Attr" or annotation.startswith("Attr[")
    return get_origin(annotation) is Attr


def _attr_from_value(value: Any) -> Attr[Any]:
    """把类体里的裸默认值包成 ``Attr``：注解即类型，右边即值。"""
    if isinstance(value, (list, tuple)):
        items = list(value)
        return Attr(factory=lambda: list(items))
    if isinstance(value, Mapping):
        mapping = dict(value)
        return Attr(factory=lambda: dict(mapping))
    if hasattr(value, "to_data"):
        return Attr(item=type(value), default=value)
    return Attr(default=value)


class Block:
    """所有内容类型的基类（也是未登记 ``type`` 的兜底裸块）。

    子类通过**重新描述字段**来定义领域结构，而不是加新顶层字段。字段两种写法等价：

        class Note(Block):
            type = "cairn.note"
            title: Attr[str] = ""            # 注解即类型，右边即值（自动包成字段）
            tags = Attr(factory=dict)        # 也可显式写描述符

            @classmethod
            def tables(cls):                 # 领域自描述的业务表（含关联表）
                return {"notes": {...}}

    注册：定义 ``type`` 的子类会自动进 ``_REGISTRY``（``__init_subclass__``），
    ``decode`` 据此还原成正确的子类。
    """

    type: str = "cairn.block"
    kind: str = "cairn.block"
    body: Body[Any] = Body()
    _REGISTRY: ClassVar[dict[str, builtins.type[Block]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        declared = cls.__dict__.get("type")
        if declared is not None:
            Block._REGISTRY[_type_name(declared)] = cls
        if "kind" not in cls.__dict__:
            cls.kind = cls.type
        # 注解即类型、右边即值：把 ``name: Attr[T] = 默认值`` 自动包成字段描述符。
        for name, annotation in cls.__dict__.get("__annotations__", {}).items():  # noqa: RUF063
            value = cls.__dict__.get(name, _MISSING)
            if value is _MISSING or isinstance(value, Attr):
                continue
            if not _is_attr_annotation(annotation):
                continue
            descriptor = _attr_from_value(value)
            descriptor.__set_name__(cls, name)
            setattr(cls, name, descriptor)

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

    def body_hash(self) -> str:
        """**去重键**：只算 ``body``（不含 id / attrs / 签名 / 时间戳）。

        这是桶里内容池的键——同 body 即复用同一份内容。子类可覆写口径
        （如笔记剥离行 id、把行内样式一并算入）。
        """
        return _digest(canonical(self.body))

    def compute_checksum(self) -> str:
        """块签名 = ``body_hash``；桶按它去重，``verify`` 也按它。"""
        return self.body_hash()

    def content_size(self) -> int:
        """主体字节数：bytes 取长度，其余取确定性编码长度。"""
        if isinstance(self.body, (bytes, bytearray)):
            return len(self.body)
        return len(canonical(self.body))

    def encode_body(self) -> bytes:
        """编码 body 为落盘字节（进桶的内容池，按 ``body_hash`` 去重）。"""
        return canonical(self.body)

    @classmethod
    def decode(
        cls,
        data: bytes,
        *,
        id: str | None = None,
        attrs: Any = None,
        type: str | None = None,
    ) -> Block:
        """由「body 字节 + attrs + type」还原为对应子类；未知类型退回基类。

        body 与 attrs 分开存（body 进内容池、attrs 随块行），这里拼合后按子类口径重算
        ``checksum``，保证读回与写入一致。
        """
        try:
            body = cbor2.loads(data) if data else None
            kind = str(type) if type is not None else cls.type
            target = Block._REGISTRY.get(kind, Block)
            block = target(id=id, body=body, attrs=dict(attrs or {}), type=kind)
            block.checksum = block.compute_checksum()
            return block
        except (
            cbor2.CBORDecodeError,
            cbor2.CBOREncodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
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

    # title / tags / authors 等业务字段**不属于块**：由各领域用 ``Attr`` 自行声明
    # （见 ``domains/base.py`` 的 ``normalize_tags`` 与各领域类）。

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
