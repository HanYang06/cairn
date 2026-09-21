# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""通信主干：域服务基类与动作 / 多播信号句柄。

- ``Domain``：域服务基类（处理器级单例），注册后挂到 ``Signal`` 的地址树上。
- ``@action``：把方法标成**单播动作**；调用经总线派发，异常原样透传。
- ``Topic``：类字段声明**多播信号**；实例上取到 ``BoundTopic``，``emit`` / ``subscribe``。

地址零字符串：``signal.feature.Note.save(...)`` 全靠属性访问，动作与信号都是**对象句柄**。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, Self, overload

from core.types import ROLE_DOMAIN, CairnError, TypeInfo, register, type_name

if TYPE_CHECKING:
    import builtins
    from enum import Enum

    from core.storage import Block

    from .bus import Signal
    from .events import Subscription

SignalHandler = Callable[[Any], None]
ActionFunc = Callable[..., Any]


def _type_units(declared: Any) -> tuple[str, ...]:
    """把声明（单个数据类，或它们的列表 / 元组）归一化成 `type` 名元组。"""
    if declared is None:
        return ()
    items = declared if isinstance(declared, (list, tuple)) else (declared,)
    names: list[str] = []
    for item in items:
        name = type_name(getattr(item, "type", "") or "")
        if name:
            names.append(name)
    return tuple(names)


class SignalError(CairnError):
    """通信主干错误。"""


class Action:
    """绑定的单播动作句柄：调用即经总线派发，异常原样透传。"""

    __slots__ = ("_func", "_name", "_owner", "_signal")

    def __init__(self, signal: Signal | None, owner: Domain, func: ActionFunc, name: str) -> None:
        self._signal = signal
        self._owner = owner
        self._func = func
        self._name = name

    @property
    def name(self) -> str:
        """动作名。"""
        return self._name

    @property
    def owner(self) -> Domain:
        """所属域服务。"""
        return self._owner

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self._signal is None:
            return self._func(self._owner, *args, **kwargs)
        return self._signal.invoke(self, *args, **kwargs)

    def __repr__(self) -> str:
        return f"Action({type(self._owner).__name__}.{self._name})"


class Domain:
    """域服务基类：单例处理器；对外只暴露 ``@action`` 动作与 ``Topic`` 信号。

    域是**管理型对象**：每 App / Vault 一个，**无 ID**；`type` / `name` / `data`(依赖的
    数据结构) 用类属性声明，基类填默认、子类只写差异。定义时登记进最小类型表。
    """

    name: ClassVar[str] = ""  # 解析键；缺省 = 定义它的模块路径（不是显示名）
    type: ClassVar[str | Enum] = ""
    data: ClassVar[tuple[builtins.type[Block], ...]] = ()  # 本域用到的数据类
    light: ClassVar[list[builtins.type[Block]] | builtins.type[Block] | None] = None

    _signal: Signal | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.__dict__.get("name"):
            cls.name = cls.__module__
        if not cls.__dict__.get("type"):
            cls.type = cls.__name__.lower()
        units = _type_units(cls.__dict__.get("light")) or (type_name(cls.type),)
        register(
            TypeInfo(
                type=type_name(cls.type),
                role=ROLE_DOMAIN,
                cls=cls,
                name=cls.name,
                deps=_type_units(cls.data),
                units=units,
            )
        )

    def bind(self, signal: Signal) -> Self:
        """绑定通信主干（组合根显式调用；非字符串注册）。"""
        self._signal = signal
        return self

    @property
    def bus(self) -> Signal:
        """所属通信主干；未绑定即抛错。"""
        if self._signal is None:
            raise SignalError(f"域未绑定总线：{type(self).__name__}")
        return self._signal


class BoundTopic:
    """绑定到某条总线的多播信号句柄。"""

    __slots__ = ("_signal", "_topic")

    def __init__(self, signal: Signal | None, topic: Topic) -> None:
        self._signal = signal
        self._topic = topic

    @property
    def name(self) -> str:
        """信号名。"""
        return self._topic.name

    def emit(self, data: Any = None) -> None:
        """发出信号；订阅者异常被隔离。未注册时无总线，直接丢弃。"""
        if self._signal is not None:
            self._signal.emit(self, data)

    def subscribe(self, handler: SignalHandler) -> Subscription:
        """订阅本信号，返回取消句柄；未注册即抛错。"""
        if self._signal is None:
            raise SignalError(f"域未注册，无法订阅信号：{self._topic.name}")
        return self._signal.subscribe(self, handler)

    def __repr__(self) -> str:
        return f"BoundTopic({self._topic.name})"


class Topic:
    """多播信号声明（类字段描述符）；实例上取到 ``BoundTopic``。"""

    def __init__(self) -> None:
        self._name = ""

    def __set_name__(self, _owner: type, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        """信号名。"""
        return self._name

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> Topic: ...
    @overload
    def __get__(self, obj: Domain, objtype: type | None = None) -> BoundTopic: ...
    def __get__(self, obj: Domain | None, objtype: type | None = None) -> Topic | BoundTopic:
        if obj is None:
            return self
        key = f"__topic_{self._name}"
        cached = obj.__dict__.get(key)
        if isinstance(cached, BoundTopic):
            return cached
        bound = BoundTopic(obj._signal, self)  # noqa: SLF001 — 域与主干同包强耦合
        obj.__dict__[key] = bound
        return bound

    def __repr__(self) -> str:
        return f"Topic({self._name})"


class _Action:
    """单播动作声明（类字段描述符）。"""

    def __init__(self, func: ActionFunc) -> None:
        self._func = func
        self._name = func.__name__
        self.__wrapped__ = func

    def __set_name__(self, _owner: type, name: str) -> None:
        self._name = name

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> _Action: ...
    @overload
    def __get__(self, obj: Domain, objtype: type | None = None) -> Action: ...
    def __get__(self, obj: Domain | None, objtype: type | None = None) -> _Action | Action:
        if obj is None:
            return self
        return Action(obj._signal, obj, self._func, self._name)  # noqa: SLF001 — 域与主干同包强耦合

    def __repr__(self) -> str:
        return f"action({self._name})"


def action(func: ActionFunc) -> _Action:
    """把方法标记为单播动作（类字段描述符）。"""
    return _Action(func)


__all__ = [
    "Action",
    "BoundTopic",
    "Domain",
    "SignalError",
    "SignalHandler",
    "Topic",
    "action",
]
