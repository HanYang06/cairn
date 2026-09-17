# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from cairn.core import Event, ObjectDeleted, ObjectPut, Vault
from cairn.core.store import Block

if TYPE_CHECKING:
    from pathlib import Path


def _create(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_put_and_delete_events_in_order(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    seen: list[Event] = []
    vault.subscribe(seen.append)

    oid = vault.put(b"x", type="note")
    vault.put(b"y", oid=oid, type="note")
    vault.delete(oid)

    assert [type(event).__name__ for event in seen] == [
        "ObjectPut",
        "ObjectPut",
        "ObjectDeleted",
    ]
    assert isinstance(seen[0], ObjectPut)
    assert seen[0].created is True
    assert isinstance(seen[1], ObjectPut)
    assert seen[1].created is False


def test_filtered_subscription(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    puts: list[Event] = []
    vault.subscribe(puts.append, event_type=ObjectPut)

    vault.put(b"a")
    vault.delete(vault.put(b"b"))

    assert len(puts) == 2
    assert all(isinstance(event, ObjectPut) for event in puts)


def test_cancel_stops_delivery(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    seen: list[Event] = []
    subscription = vault.subscribe(seen.append)
    vault.put(b"a")
    subscription.cancel()
    vault.put(b"b")

    assert len(seen) == 1


def test_subscription_context_manager(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    seen: list[Event] = []
    with vault.subscribe(seen.append):
        vault.put(b"a")
    vault.put(b"b")

    assert len(seen) == 1


def test_handler_exception_is_isolated(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    received: list[Event] = []

    def boom(_event: Event) -> None:
        raise RuntimeError("boom")

    vault.subscribe(boom)
    vault.subscribe(received.append)

    oid = vault.put(b"a")
    assert oid
    assert len(received) == 1


def test_delete_missing_emits_nothing(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    seen: list[Event] = []
    vault.subscribe(seen.append, event_type=ObjectDeleted)

    vault.delete(vault.put(b"a"))
    seen.clear()
    vault.delete("01M26N4DXANY9TDMSJQBEP8B4J")

    assert seen == []


def test_put_block_emits_checksum_and_created(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    puts: list[ObjectPut] = []
    vault.subscribe(puts.append, event_type=ObjectPut)

    block = Block(body=b"x", type="blob")
    vault.put_block(block)
    assert len(puts) == 1
    assert puts[0].created is True
    assert puts[0].type == "blob"
    assert puts[0].checksum == block.checksum

    block.body = b"y"
    vault.put_block(block)
    assert puts[-1].created is False
    assert puts[-1].checksum == block.checksum
