# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`Signal`：**信号与事件处理引擎**。

作者口述的设计（2026-09-22）：

1. 引擎解析 `Event` 数据结构：这是个什么事件（意图）、ID 是什么、谁发的、目标是谁；
2. 拿到信息后**指挥 `actions` 里那堆动作**：按顺序，每一步找到目标里某个身份的对象，
   对该对象的某个地方执行操作，最后把执行结果**落到槽里**；
3. **引擎受内核管辖**——两张对象表属于 `Core`；内核**自带**引擎并在建好时把表交给它
   （`Core.__init__` → `engine.connect(内部表, 外部表)`）。**引擎自己不持表**；
4. 对象从两张表里找：找得到就干活，找不到就报错（报错怎么处理交给业务）。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from core.types import ObjectNotFoundError
from core.types.event import Action, Event, Slot
from core.types.kind import identity_key

_logger = logging.getLogger(__name__)

type Table = dict[str, dict[Any, object]]
type Handler = Callable[[Event], None]

_IDENTITIES = ("role_id", "role_name", "role_obj")


class Subscription:
    """订阅句柄：``cancel()`` 后不再收到事件，支持 ``with``。"""

    def __init__(self, engine: Signal, handler: Handler) -> None:
        self._engine = engine
        self.handler = handler
        self.active = True

    def cancel(self) -> None:
        """取消订阅（幂等）。"""
        if self.active:
            self.active = False
            self._engine.unsubscribe(self)

    def __enter__(self) -> Subscription:  # noqa: PYI034 — 句柄自身即上下文对象
        return self

    def __exit__(self, *_exc: object) -> None:
        self.cancel()


@dataclass
class Step:
    """一步执行的**经过**（结果是否合理由调用方按它判断）。"""

    action: Action
    identity: str = ""
    target: object | None = None
    result: Any = None
    error: Exception | None = None

    @property
    def ok(self) -> bool:
        """这一步是否有结果。"""
        return self.error is None

    def __repr__(self) -> str:
        state = "ok" if self.ok else f"err={type(self.error).__name__}"
        return f"Step({self.action.call_function}:{state})"


@dataclass
class Outcome:
    """一次事件处理的**全貌**：每一步的经过 + 结果槽。"""

    event: Event
    steps: list[Step] = field(default_factory=list)
    slot: Slot = field(default_factory=Slot)

    @property
    def ok(self) -> bool:
        """是否每一步都有结果（**期望 vs 实得**的粗判）。"""
        return all(step.ok for step in self.steps)

    @property
    def failed(self) -> list[Step]:
        """没有结果的那些步骤。"""
        return [step for step in self.steps if not step.ok]

    def __repr__(self) -> str:
        return f"Outcome({self.event.intent.name}, {len(self.steps)} 步, ok={self.ok})"


class Signal:
    """信号与事件处理引擎（内核固定件，**不自己注册**：它与内核同生共死）。"""

    def __init__(self) -> None:
        # 两张表由内核在建好引擎时交进来；引擎只引用、不持有。
        self._internal: Table = {key: {} for key in _IDENTITIES}
        self._external: Table = {key: {} for key in _IDENTITIES}
        # 观察者：事件包在链路上跑，想看的人订阅链路（派发后收到包）。
        self._observers: list[Subscription] = []

    # ---- 内核把表交进来（`Core.__init__` / `Core.use()` 时调用）----
    def connect(self, internal: Table, external: Table) -> None:
        """接上内核的两张表（**引擎不持表**，只是引用内核的）。"""
        self._internal = internal
        self._external = external

    # ---- 订阅链路（通信）----
    def subscribe(self, handler: Handler) -> Subscription:
        """订阅事件流：每次 :meth:`handle` 之后收到那个包；返回取消句柄。"""
        entry = Subscription(self, handler)
        self._observers.append(entry)
        return entry

    def unsubscribe(self, entry: Subscription) -> None:
        """取消订阅（幂等）。"""
        self._observers = [item for item in self._observers if item is not entry]

    def _notify(self, event: Event) -> None:
        """派发后通知观察者；单个观察者出错**隔离**，不影响链路与其它观察者。"""
        for entry in list(self._observers):
            if not entry.active:
                continue
            try:
                entry.handler(event)
            except Exception:
                _logger.exception("事件观察者异常：%s", event.intent.name)

    # ---- 查对象 ----
    def lookup(self, identity: str, value: Any) -> object | None:
        """按身份查对象：**先表二（外部）、再表一（内部）**；找不到返回 ``None``。"""
        if not identity:
            return None
        key = identity_key(identity, value)
        found = self._external.get(identity, {}).get(key)
        if found is not None:
            return found
        return self._internal.get(identity, {}).get(key)

    def resolve(self, action: Action) -> object:
        """按动作自带的身份解析目标对象；找不到即报错（交业务处理）。"""
        identity, value = action.identity()
        if not identity:
            raise ObjectNotFoundError(f"动作未给出目标身份：{action.call_function}")
        target = self.lookup(identity, value)
        if target is None:
            raise ObjectNotFoundError(f"找不到目标：{identity}={value!r}")
        return target

    # ---- 解析与指挥 ----
    def handle(self, event: Event) -> Outcome:
        """**统一处理入口**：解析事件 → 逐步指挥 → 结果落槽。

        找不到目标这种**机制性错误**：本步记为失败、放进 `Step.error`，**继续往下走**——
        因为"结果是否合理"是调用方按全貌判断的（见 `Outcome.failed`）。
        """
        outcome = Outcome(event=event)
        if not event.is_sendable():
            _logger.debug("意图为 NOEN，事件不发：%r", event)
            return outcome

        for action in event.actions:
            step = Step(action=action)
            outcome.steps.append(step)
            step.identity, _ = action.identity()
            try:
                step.target = self.resolve(action)
                step.result = self.invoke(step.target, action)
                self.stash(action, step)
            except Exception as exc:  # noqa: BLE001 — 机制性失败交出去，不吞不掩
                step.error = exc
                _logger.debug("步骤失败：%r -> %s", action, exc)
        self._notify(event)  # 链路跑完，通知观察者（隔离单个观察者的错误）
        return outcome

    def invoke(self, target: object, action: Action) -> Any:
        """对该对象的某个地方执行操作（按名字取方法，带参调用）。"""
        method = getattr(target, action.call_function, None)
        if method is None:
            raise ObjectNotFoundError(
                f"{type(target).__name__} 没有这种方法：{action.call_function}"
            )
        if not callable(method):
            raise TypeError(f"{type(target).__name__}.{action.call_function} 不是可调用的")
        return method(**action.call_arges)

    def stash(self, action: Action, step: Step) -> None:
        """把结果落进**寄存器**：拿什么查的，就按什么返回。"""
        identity, value = action.identity()
        if not value:
            return
        action.slot.add(identity, step.result)


__all__ = ["Handler", "Outcome", "Signal", "Step", "Subscription", "Table"]
