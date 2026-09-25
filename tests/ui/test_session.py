# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from core import Core  # noqa: TC001 — fixture 注解
from core.storage import Block
from tests.conftest import make_kernel
from ui_tools.core.session import Session

if TYPE_CHECKING:
    from pathlib import Path


def _core(tmp_path: Path) -> Core:
    return make_kernel(tmp_path)


def test_session_observes_block_events(tmp_path: Path) -> None:
    core = _core(tmp_path)
    session = Session(core.signal)
    seen: list[object] = []
    session.watch(seen.append)

    core.put(Block(body=b"x"))

    assert len(seen) == 1
    assert seen[0].intent.name == "PUT"


def test_projection_invalidated_on_change(tmp_path: Path) -> None:
    core = _core(tmp_path)
    session = Session(core.signal)
    calls = {"n": 0}

    def loader() -> str:
        calls["n"] += 1
        return f"v{calls['n']}"

    assert session.projection("k", loader) == "v1"
    assert session.projection("k", loader) == "v1"
    core.put(Block(body=b"y"))
    assert session.projection("k", loader) == "v2"


def test_watch_cancel_stops_notifications(tmp_path: Path) -> None:
    core = _core(tmp_path)
    session = Session(core.signal)
    seen: list[object] = []
    cancel = session.watch(seen.append)

    cancel()
    core.put(Block(body=b"z"))

    assert seen == []


def test_close_is_terminal(tmp_path: Path) -> None:
    core = _core(tmp_path)
    session = Session(core.signal)
    session.close()

    with pytest.raises(RuntimeError, match="已关闭"):
        session.watch(lambda _event: None)


def test_release_stops_model_refresh(tmp_path: Path) -> None:
    core = _core(tmp_path)
    session = Session(core.signal)
    calls = {"n": 0}

    def loader() -> list[int]:
        calls["n"] += 1
        return []

    model = session.model(loader)
    session.release(model)
    core.put(Block(body=b"y"))

    assert calls["n"] == 1  # 注销后主干变更不再重算


def test_on_event_isolates_failing_observer(tmp_path: Path) -> None:
    core = _core(tmp_path)
    session = Session(core.signal)
    seen: list[object] = []

    def boom(_event: object) -> None:
        raise RuntimeError("boom")

    session.watch(boom)
    session.watch(seen.append)

    core.put(Block(body=b"w"))

    assert len(seen) == 1


def test_on_event_allows_model_change_from_loader(tmp_path: Path) -> None:
    core = _core(tmp_path)
    session = Session(core.signal)
    state = {"armed": False, "added": False}

    def loader() -> list[int]:
        if state["armed"] and not state["added"]:
            state["added"] = True
            session.model(list)  # 通知期间新增模型，不得中断迭代
        return []

    session.model(loader)
    state["armed"] = True

    core.put(Block(body=b"q"))

    assert state["added"] is True
