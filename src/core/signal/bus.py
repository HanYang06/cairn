# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""通信主干（统一调用总线 / 对象寻址空间）：``Signal`` + 命名空间。

- **单播**：``signal.feature.Note.save(...)`` 经 ``invoke`` 派发，异常原样透传。
- **多播**：``topic.emit(data)`` / ``topic.subscribe(handler)``，订阅者异常隔离。
- **作用域**：每个 App / Vault 一个 ``Signal`` 实例，非全局单例。

地址树形如 ``signal.<命名空间>.<域>.<动作|信号>``；命名空间与域节点是对象、
动作与信号是句柄，全程零字符串。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .events import Event, EventBus, Subscription
from .service import Action, BoundTopic, Domain, SignalError, SignalHandler


@dataclass(frozen=True, slots=True)
class _TopicEvent(Event):
    """多播信号在底层事件总线上的载体。"""

    topic: object
    data: Any = None


class Namespace:
    """地址树上的命名空间节点（``core`` / ``feature``）。"""

    def __init__(self) -> None:
        self._domains: dict[str, Domain] = {}

    def _add(self, name: str, domain: Domain) -> None:
        self._domains[name] = domain
        setattr(self, name, domain)

    def domains(self) -> dict[str, Domain]:
        """本命名空间下已注册的域（名字 → 服务）。"""
        return dict(self._domains)

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(f"未注册的域：{name!r}")

    def __repr__(self) -> str:
        return f"Namespace({sorted(self._domains)})"


class Signal:
    """进程内统一调用主干：对象寻址 + 单播 / 多播。"""

    def __init__(self) -> None:
        self.core = Namespace()
        self.feature = Namespace()
        self._events = EventBus()
        self._domains: dict[str, Domain] = {}

    def register(self, domain: Domain, *, namespace: str | None = None) -> Domain:
        """把域服务挂到地址树上（默认用域的 ``namespace``）。"""
        target = namespace or domain.namespace
        space = getattr(self, target, None)
        if not isinstance(space, Namespace):
            raise SignalError(f"未知命名空间：{target!r}")
        domain._signal = self  # noqa: SLF001 — 注册即绑定总线，域与主干同包强耦合
        space._add(domain.name, domain)  # noqa: SLF001 — 同上
        self._domains[domain.name] = domain
        return domain

    @property
    def events(self) -> EventBus:
        """底层事件总线（多播投递复用其同步、隔离语义）。"""
        return self._events

    def domains(self) -> dict[str, Domain]:
        """已注册的域（名字 → 服务）。"""
        return dict(self._domains)

    def invoke(self, action: Action, *args: Any, **kwargs: Any) -> Any:
        """单播：执行动作，异常原样透传。"""
        return action._func(action._owner, *args, **kwargs)  # noqa: SLF001 — 动作句柄与总线同包强耦合

    def emit(self, topic: BoundTopic, data: Any = None) -> None:
        """多播：发出信号（订阅者异常被隔离）。"""
        self._events.emit(_TopicEvent(topic=topic, data=data))

    def subscribe(self, topic: BoundTopic, handler: SignalHandler) -> Subscription:
        """多播：按信号订阅。"""
        target = topic

        def dispatch(event: Event) -> None:
            if isinstance(event, _TopicEvent) and event.topic is target:
                handler(event.data)

        return self._events.subscribe(dispatch, _TopicEvent)

    def __repr__(self) -> str:
        return f"Signal(domains={sorted(self._domains)})"


__all__ = [
    "Namespace",
    "Signal",
]
