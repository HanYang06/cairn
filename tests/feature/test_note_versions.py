# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from core import Vault
from core.storage import VersionStore, decode_canonical
from feature import Note

if TYPE_CHECKING:
    from pathlib import Path


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_version_chain_reconstructs_history(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    note = notes.create("v1", title="t")
    notes.update(note, text="v2")
    notes.update(note, text="v3")

    history = notes.history(note)  # 最新在前：[v3, v2, root(v1)]
    assert len(history) == 3
    root = history[-1]["id"]
    middle = history[-2]["id"]

    assert note.text == "v3"
    assert [line["v"] for line in notes.body_at(note, root)] == ["v1"]
    assert [line["v"] for line in notes.body_at(note, middle)] == ["v2"]


def test_metadata_only_change_does_not_version(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    note = notes.create("x")
    before = notes.history(note)
    notes.update(note, title="新标题")
    assert notes.history(note) == before


def test_persist_defers_version_until_checkpoint(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    note = notes.create("v1")
    assert len(notes.history(note)) == 1

    notes.set_text(note, "v2")
    notes.persist(note)
    notes.set_text(note, "v3")
    notes.persist(note)

    # 自动保存（persist）只落盘，不进历史。
    assert len(notes.history(note)) == 1
    assert notes.load(note.oid).text == "v3"

    notes.save(note)  # 检查点
    history = notes.history(note)
    assert len(history) == 2
    assert [line["v"] for line in notes.body_at(note, history[-1]["id"])] == ["v1"]
    assert [line["v"] for line in notes.body_at(note, history[0]["id"])] == ["v3"]


def test_paragraph_attribute_is_versioned(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    note = notes.create("x")
    lid = note.body[0]["id"]  # type: ignore[index]

    notes.set_paragraph(note, lid, {"heading": 1})
    notes.save(note)

    history = notes.history(note)
    assert len(history) == 2
    assert notes.body_at(note, history[-1]["id"])[0].get("p") is None
    assert notes.body_at(note, history[0]["id"])[0].get("p") == {"heading": 1}


def test_diff_is_reverse_and_incremental(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    note = notes.create("hello world")
    notes.update(note, text="hello cairn")

    head = notes.history(note)[0]["id"]
    rows = vault.bucket.query("SELECT payload FROM version WHERE id = ?", (head,))
    patch = decode_canonical(bytes(rows[0]["payload"]))
    lids = [line["id"] for line in note.body]
    assert patch[lids[0]] == {"act": "PUT", "v": "hello world"}


def test_lazy_compaction_drops_expired(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    note = notes.create("v1")
    notes.update(note, text="v2")
    assert len(notes.history(note)) == 2

    removed = VersionStore(vault.bucket).compact(note.id, retention_ms=0)
    assert removed == 2
    assert notes.history(note) == []
