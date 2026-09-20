# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from core.signal import Domain, Signal, SignalError, Topic, action


class Counter(Domain):
    name = "Counter"

    def __init__(self) -> None:
        self.value = 0

    @action
    def bump(self, n: int = 1) -> int:
        self.value += n
        return self.value


class Notebook(Domain):
    name = "Note"

    changed = Topic()

    def __init__(self) -> None:
        self.saved: list[int] = []

    @action
    def save(self, value: int) -> str:
        self.saved.append(value)
        self.changed.emit(value)
        return "ok"


class Core:
    """静态域容器（示例；无运行时注册）。"""

    Counter: Counter

    def __init__(self, counter: Counter) -> None:
        self.Counter = counter


def test_action_routes_through_bound_bus() -> None:
    sig = Signal()
    counter = Counter().bind(sig)

    assert counter.bump(2) == 2
    assert counter.value == 2


def test_action_without_bus_calls_directly() -> None:
    counter = Counter()

    assert counter.bump(3) == 3


def test_action_exception_propagates() -> None:
    sig = Signal()

    class Boom(Domain):
        @action
        def go(self) -> None:
            raise RuntimeError("boom")

    boom = Boom().bind(sig)
    with pytest.raises(RuntimeError, match="boom"):
        boom.go()


def test_unbound_domain_bus_raises() -> None:
    with pytest.raises(SignalError, match="未绑定总线"):
        _ = Counter().bus


def test_static_tree_attach() -> None:
    sig = Signal()
    sig.core = Core(Counter().bind(sig))

    assert sig.core is not None
    assert sig.core.Counter.bump(1) == 1


def test_topic_multicast_and_isolation() -> None:
    sig = Signal()
    note = Notebook().bind(sig)
    seen: list[int] = []
    note.changed.subscribe(seen.append)

    def boom(_data: object) -> None:
        raise RuntimeError("boom")

    note.changed.subscribe(boom)
    assert note.save(1) == "ok"
    assert seen == [1]


def test_topic_subscription_cancel() -> None:
    sig = Signal()
    note = Notebook().bind(sig)
    seen: list[int] = []
    sub = note.changed.subscribe(seen.append)

    note.changed.emit(1)
    sub.cancel()
    note.changed.emit(2)
    assert seen == [1]


def test_two_signals_are_isolated() -> None:
    first = Signal()
    second = Signal()
    a = Counter().bind(first)
    b = Counter().bind(second)

    a.bump(5)
    assert a.value == 5
    assert b.value == 0
