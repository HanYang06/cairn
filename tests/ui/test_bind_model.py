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
