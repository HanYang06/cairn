# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from core import Vault
from core.storage import Block
from ui_tools.core.session import Session

if TYPE_CHECKING:
    from pathlib import Path


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_session_observes_block_events(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    session = Session(vault.signal)
    seen: list[object] = []
    session.watch(seen.append)

    vault.put_block(Block(body=b"x"))

    assert len(seen) == 1
    assert getattr(seen[0], "type", None) == "block"


def test_projection_invalidated_on_change(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    session = Session(vault.signal)
    calls = {"n": 0}

    def loader() -> str:
        calls["n"] += 1
        return f"v{calls['n']}"

    assert session.projection("k", loader) == "v1"
    assert session.projection("k", loader) == "v1"
    vault.put_block(Block(body=b"y"))
    assert session.projection("k", loader) == "v2"


def test_watch_cancel_stops_notifications(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    session = Session(vault.signal)
    seen: list[object] = []
    cancel = session.watch(seen.append)

    cancel()
    vault.put_block(Block(body=b"z"))

    assert seen == []


def test_close_is_terminal(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    session = Session(vault.signal)
    session.close()

    with pytest.raises(RuntimeError, match="已关闭"):
        session.watch(lambda _event: None)


def test_release_stops_model_refresh(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    session = Session(vault.signal)
    calls = {"n": 0}

    def loader() -> list[int]:
        calls["n"] += 1
        return []

    model = session.model(loader)
    session.release(model)
    vault.put_block(Block(body=b"y"))

    assert calls["n"] == 1  # 注销后主干变更不再重算


def test_on_event_isolates_failing_observer(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    session = Session(vault.signal)
    seen: list[object] = []

    def boom(_event: object) -> None:
        raise RuntimeError("boom")

    session.watch(boom)
    session.watch(seen.append)

    vault.put_block(Block(body=b"w"))

    assert len(seen) == 1
