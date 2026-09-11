from __future__ import annotations

from pathlib import Path

from cairn.core import (
    Event,
    ObjectDeleted,
    ObjectPut,
    SpaceCreated,
    Vault,
    VaultLocked,
    VaultUnlocked,
)

PASSPHRASE = "correct horse battery staple"


def _create(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault", PASSPHRASE)


def test_events_emitted_in_order(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    seen: list[Event] = []
    vault.subscribe(seen.append)

    vault.create_space("photos")
    oid = vault.put(b"x", type="note")
    vault.put(b"y", oid=oid, type="note")
    vault.delete(oid)
    vault.lock()

    assert [type(event).__name__ for event in seen] == [
        "SpaceCreated",
        "ObjectPut",
        "ObjectPut",
        "ObjectDeleted",
        "VaultLocked",
    ]
    assert isinstance(seen[0], SpaceCreated)
    assert isinstance(seen[1], ObjectPut)
    assert seen[1].created is True
    assert seen[2].created is False
    assert seen[2].seq == 2


def test_filtered_subscription(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    puts: list[Event] = []
    vault.subscribe(puts.append, event_type=ObjectPut)

    vault.create_space("s")
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


def test_unlock_and_lock_events(tmp_path: Path) -> None:
    _create(tmp_path)
    vault = Vault.load(tmp_path / "vault")
    seen: list[Event] = []
    vault.subscribe(seen.append)

    vault.unlock(PASSPHRASE)
    assert any(isinstance(event, VaultUnlocked) for event in seen)

    vault.lock()
    assert any(isinstance(event, VaultLocked) for event in seen)


def test_delete_missing_emits_nothing(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    seen: list[Event] = []
    vault.subscribe(seen.append, event_type=ObjectDeleted)

    vault.delete(vault.put(b"a"))
    seen.clear()
    vault.delete("01M26N4DXANY9TDMSJQBEP8B4J")

    assert seen == []
