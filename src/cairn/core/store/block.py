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

from collections.abc import Callable, Iterable, Iterator, Mapping
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar, Self, get_origin

import cbor2
from blake3 import blake3

from ...types import CairnError, CorruptObjectError, Oid

if TYPE_CHECKING:
    import builtins

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


class Data[T = Any](Attr[T]):
    """**数据字段**的声明：与 ``Attr`` 同机制、同存储，但语义是"数据"而非"属性"。

    ``Attr`` 描述的是**属性**（title / tags / 签名等描述性元数据）；
    画板 / 多媒体这类**承载数据**的字段用 ``Data`` 声明，避免"属性"用词错位。
    用法一致：``canvas: Data = Data(factory=list, item=Canvas)``。
    """


class Body:
    """body 容器基类：**无 ID**、依存于块；自带状态字段 ``hash``。

    子类声明自己的内容字段，并实现 ``content()``（参与哈希的内容视图）与
    ``to_data()`` / ``from_data()``（落盘）。``hash`` **只覆盖内容字段**，
    排除自身状态（hash 自己、时间戳等）——否则自我指涉、且时间戳会让去重永远失败。

    约定：内容一变更就调 ``refresh()`` 重算一次并存下来，之后直接用，不重复算。
    """

    hash: str = ""

    def content(self) -> Any:
        """参与哈希的内容字段（子类实现）。"""
        raise NotImplementedError

    def refresh(self) -> Body:
        """内容变更后重算一次 ``hash``。"""
        self.hash = _digest(canonical(self.content()))
        return self

    def to_data(self) -> Any:
        raise NotImplementedError

    @classmethod
    def from_data(cls, data: Any) -> Body:
        raise NotImplementedError


class BodyField[T = Any]:
    """``body`` 字段的声明：惰性建值、每实例一份、结构化时校验是 ``Body``。

    - ``BodyField()``：裸 body（bytes / list / 标量），原样存取。
    - ``BodyField(prototype=NoteBody())``：结构化 body；读取按 prototype 类型**每实例新建**
      （用 ``from_data(to_data())``），写入时非 ``Body`` 则 ``from_data`` 转换。
    """

    def __init__(
        self,
        default: Any = _MISSING,
        *,
        factory: Callable[[], Any] | None = None,
        prototype: Body | None = None,
    ) -> None:
        self._default = default
        self._factory = factory
        self._prototype = prototype
        self.key = ""

    def __set_name__(self, _owner: type, name: str) -> None:
        self.key = name

    def _fresh(self) -> Any:
        if self._prototype is not None:
            return type(self._prototype).from_data(self._prototype.to_data())
        if self._factory is not None:
            return self._factory()
        return None if self._default is _MISSING else self._default

    def __get__(self, obj: Block | None, _owner: type | None = None) -> Any:
        if obj is None:
            return self
        if "_body" not in obj.__dict__:
            obj.__dict__["_body"] = self._fresh()
        return obj.__dict__["_body"]

    def __set__(self, obj: Block, value: Any) -> None:
        if self._prototype is not None and not isinstance(value, Body):
            value = type(self._prototype).from_data(value)
        obj.__dict__["_body"] = value


def _is_attr_annotation(annotation: Any) -> bool:
    """注解是否是 ``Attr`` / ``Data`` 及其下标（属性 / 数据字段）。"""
    if isinstance(annotation, str):
        name = annotation.split("[", 1)[0].strip()
        return name in ("Attr", "Data")
    return get_origin(annotation) in (Attr, Data)


def _is_container_annotation(annotation: Any) -> bool:
    """注解是否是裸容器（``list[...]`` / ``dict[...]``）——数据字段可自证类型、免标记。"""
    if isinstance(annotation, str):
        return annotation.startswith(("list[", "dict[", "tuple[", "set["))
    return get_origin(annotation) in (list, dict, tuple, set)


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


def _data_from_value(value: Any) -> Data[Any]:
    """把容器注解的裸默认值包成 ``Data``（数据字段）。"""
    if isinstance(value, list):
        items = list(value)
        return Data(factory=lambda: list(items))
    mapping = dict(value)
    return Data(factory=lambda: dict(mapping))


def _body_type(cls: builtins.type[Block]) -> builtins.type[Body] | None:
    """类声明的 body 类型（结构化 body）；裸 body 返回 ``None``。"""
    field = cls.__dict__.get("body")
    if isinstance(field, BodyField) and field._prototype is not None:  # noqa: SLF001 — 同模块内省
        return type(field._prototype)  # noqa: SLF001
    return None


def _body_from_data(target: builtins.type[Block], raw: Any) -> Any:
    kind = _body_type(target)
    if kind is not None and not isinstance(raw, Body):
        return kind.from_data(raw)
    return raw


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
    body: Any = BodyField()
    _REGISTRY: ClassVar[dict[str, builtins.type[Block]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        declared = cls.__dict__.get("type")
        if declared is not None:
            Block._REGISTRY[_type_name(declared)] = cls
        if "kind" not in cls.__dict__:
            cls.kind = cls.type
        # 注解即类型、右边即值：把类体裸值自动包成字段描述符。
        for name, annotation in cls.__dict__.get("__annotations__", {}).items():  # noqa: RUF063
            value = cls.__dict__.get(name, _MISSING)
            if value is _MISSING:
                continue
            if isinstance(value, Body):  # 结构化 body：每实例一份 + 校验
                descriptor: Any = BodyField(prototype=value)
            elif isinstance(value, Attr):
                continue
            elif _is_attr_annotation(annotation):
                descriptor = _attr_from_value(value)
            elif _is_container_annotation(annotation) and isinstance(value, (list, dict)):
                descriptor = _data_from_value(value)
            else:
                continue
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

    def __init__(  # noqa: PLR0913 — 块记录的扁平字段构造器，拆包反而更绕
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
        return

    # id 锁死：创建后不可改
    @property
    def id(self) -> str:
        if self._id is None:
            raise CairnError("块 id 未初始化")
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        if self._id is not None and value != self._id:
            raise AttributeError("块 id 不可修改")
        self._id = value

    def body_hash(self) -> str:
        """**去重键**：只算 ``body``（不含 id / attrs / 签名 / 时间戳）。

        - 结构化 body（``Body`` 子类）用它自己的 ``hash``（内容字段口径，变更时已重算）。
        - 裸 body 直接按内容算。子类可覆写口径。
        """
        body = self.body
        if isinstance(body, Body):
            return body.hash or body.refresh().hash
        return _digest(canonical(body))

    def compute_checksum(self) -> str:
        """块签名 = ``body_hash``；桶按它去重，``verify`` 也按它。"""
        return self.body_hash()

    def content_size(self) -> int:
        """主体字节数：bytes 取长度，其余取确定性编码长度。"""
        body = self.body
        if isinstance(body, (bytes, bytearray)):
            return len(body)
        if isinstance(body, Body):
            body = body.to_data()
        return len(canonical(body))

    def encode_body(self) -> bytes:
        """编码 body 为落盘字节（进桶的内容池，按 ``body_hash`` 去重）。"""
        body = self.body
        if isinstance(body, Body):
            body = body.to_data()
        return canonical(body)

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
            raw = cbor2.loads(data) if data else None
            kind = str(type) if type is not None else cls.type
            target = Block._REGISTRY.get(kind, Block)
            body = _body_from_data(target, raw)
            block = target(id=id, body=body, attrs=dict(attrs or {}), type=kind)
            block.checksum = block.compute_checksum()
        except (
            cbor2.CBORDecodeError,
            cbor2.CBOREncodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise CorruptObjectError("块解析失败") from exc
        return block

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
        block: Self = vault.bucket.get(cls, str(oid))
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
