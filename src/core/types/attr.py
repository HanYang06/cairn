# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""字段声明描述符：``Attr`` = 属性，``Data`` = 数据。

机制通用——**任何"属性"都能用 ``Attr`` 声明**，承载"数据"的字段用 ``Data``（同机制、同存储）。
取值落在对象的 ``attrs`` 上；至于这个对象是不是块、内容最终存到哪，由使用方（存储 / 领域）决定。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

_MISSING = object()


class Attr[T = Any]:
    """属性字段的声明：读写落在对象的 ``attrs`` 上。

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
            return self._normalize(self._factory())
        raw = None if self._default is _MISSING else self._default
        return self._normalize(raw)

    def _normalize(self, value: Any) -> Any:
        """写入归一：``coerce`` → ``item`` 编码（list/tuple 逐元素）。

        ``__set__`` 与默认值 / 工厂产物**共用这一条路径**，落盘形态不因写入路径而异
        （``item`` 字段存的是紧凑数据，如 ``Signature`` → dict）。
        """
        if value is None:
            return None
        if self._coerce is not None:
            value = self._coerce(value)
        if self._item is None:
            return value
        if isinstance(value, (list, tuple)):
            return [self._encode(entry) for entry in value]
        return self._encode(value)

    def _decode(self, value: Any) -> Any:
        if isinstance(value, self._item):
            return value
        if hasattr(self._item, "from_data"):
            return self._item.from_data(value)
        if not isinstance(value, Mapping):
            raise TypeError(f"字段 {self.key!r} 期望映射形态数据，得到 {type(value).__name__}")
        return self._item(**value)

    def _encode(self, value: Any) -> Any:
        return value.to_data() if hasattr(value, "to_data") else value

    def __get__(self, obj: Any, _owner: type | None = None) -> Any:
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

    def __set__(self, obj: Any, value: Any) -> None:
        obj.attrs[self.key] = self._normalize(value)


class Data[T = Any](Attr[T]):
    """**数据字段**的声明：与 ``Attr`` 同机制、同存储，但语义是"数据"而非"属性"。

    ``Attr`` 描述的是**属性**（title / tags / 签名等描述性元数据）；
    画板 / 多媒体这类**承载数据**的字段用 ``Data`` 声明，避免"属性"用词错位。
    用法一致：``canvas: Data = Data(factory=list, item=Canvas)``。
    """


__all__ = ["Attr", "Data"]
