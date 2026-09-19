# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记域服务挂到通信主干：单播动作经总线派发，``changed`` 多播回传。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from core import ObjectNotFoundError, Vault
from core.signal import Signal
from core.types import Oid
from feature import Note

if TYPE_CHECKING:
    from pathlib import Path


def _signal(tmp_path: Path) -> tuple[Signal, Note]:
    signal = Signal()
    notes = signal.register(Note(Vault.create(tmp_path / "vault")))
    return signal, notes


def test_service_lands_on_address_tree(tmp_path: Path) -> None:
    signal, notes = _signal(tmp_path)

    assert signal.feature.Note is notes
    assert signal.domains() == {"Note": notes}


def test_action_dispatches_through_bus(tmp_path: Path) -> None:
    signal, notes = _signal(tmp_path)

    note = signal.feature.Note.create("hello", title="T")

    assert note.text == "hello"
    assert note.title == "T"
    assert notes.load(note.oid).text == "hello"


def test_changed_topic_multicasts_on_save(tmp_path: Path) -> None:
    _, notes = _signal(tmp_path)
    seen: list[object] = []
    notes.changed.subscribe(seen.append)

    note = notes.create("v1")
    notes.update(note, text="v2")

    assert seen == [note.oid, note.oid]


def test_bus_propagates_action_errors(tmp_path: Path) -> None:
    signal, _ = _signal(tmp_path)

    with pytest.raises(ObjectNotFoundError):
        signal.feature.Note.load(Oid.new())


def test_two_buses_do_not_share_domains(tmp_path: Path) -> None:
    first = Signal()
    second = Signal()
    first.register(Note(Vault.create(tmp_path / "a")))
    second.register(Note(Vault.create(tmp_path / "b")))

    assert first.feature.Note is not second.feature.Note
