# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from ui_tools.core import Bind, Facet, Model, UiError, UiSignal


class FakeDomain:
    def save(self) -> None:
        return None


def test_bind_compile_ok() -> None:
    bind = Bind()
    bind.add(UiSignal("clicked"), lambda: None)

    assert len(bind.compile()) == 1


def test_bind_compile_rejects_bad_source() -> None:
    bind = Bind()
    bind.add("not-a-signal", lambda: None)

    with pytest.raises(UiError, match="不是 UI 信号"):
        bind.compile()


def test_bind_compile_rejects_bad_target() -> None:
    bind = Bind()
    bind.add(UiSignal("clicked"), 42)

    with pytest.raises(UiError, match="不可调用"):
        bind.compile()


def test_bind_add_deduplicates() -> None:
    bind = Bind()
    signal = UiSignal("clicked")

    def target() -> None:
        return None

    bind.add(signal, target)
    bind.add(signal, target)

    assert len(bind.items()) == 1


def test_facet_compile_bindings() -> None:
    facet = Facet(FakeDomain())
    facet.bind.add(UiSignal("save"), facet.domain.save)

    assert len(facet.compile_bindings()) == 1


def test_model_notifies() -> None:
    model: Model[int] = Model([1])
    seen: list[int] = []
    model.watch(lambda: seen.append(len(model)))

    model.append(2)
    model.replace([9])

    assert model.items() == [9]
    assert seen == [2, 1]


def test_model_watch_cancel() -> None:
    model: Model[int] = Model()
    calls: list[int] = []
    cancel = model.watch(lambda: calls.append(1))

    cancel()
    model.append(1)

    assert calls == []


def test_model_replace_skips_equal() -> None:
    model: Model[int] = Model([1, 2])
    seen: list[int] = []
    model.watch(lambda: seen.append(1))

    model.replace([1, 2])
    assert seen == []

    model.replace([1, 3])
    assert seen == [1]


def test_model_watch_dedup_and_cancel_all() -> None:
    model: Model[int] = Model()
    calls: list[int] = []

    def callback() -> None:
        calls.append(1)

    model.watch(callback)
    cancel = model.watch(callback)  # 重复注册去重
    model.append(1)
    assert calls == [1]

    cancel()
    model.append(2)
    assert calls == [1]


def test_model_notify_isolates_failing_observer() -> None:
    model: Model[int] = Model()
    seen: list[int] = []

    def boom() -> None:
        raise RuntimeError("boom")

    model.watch(boom)
    model.watch(lambda: seen.append(1))

    model.append(1)

    assert seen == [1]
