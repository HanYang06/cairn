# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from cairn.core import Vault
from cairn.core.store import VersionStore, decode_canonical
from cairn.domains import Note

if TYPE_CHECKING:
    from pathlib import Path


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_version_chain_reconstructs_history(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "v1", title="t")
    note.update(text="v2")
    note.update(text="v3")

    history = note.history()  # 最新在前：[v3, v2, root(v1)]
    assert len(history) == 3
    root = history[-1]["id"]
    middle = history[-2]["id"]

    assert note.text == "v3"
    assert [line["v"] for line in note.body_at(root)] == ["v1"]
    assert [line["v"] for line in note.body_at(middle)] == ["v2"]


def test_metadata_only_change_does_not_version(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "x")
    before = note.history()
    note.update(title="新标题")
    assert note.history() == before


def test_persist_defers_version_until_checkpoint(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "v1")
    assert len(note.history()) == 1

    note.set_text("v2")
    note.persist()
    note.set_text("v3")
    note.persist()

    # 自动保存（persist）只落盘，不进历史。
    assert len(note.history()) == 1
    assert Note.load(vault, note.oid).text == "v3"

    note.save()  # 检查点
    history = note.history()
    assert len(history) == 2
    assert [line["v"] for line in note.body_at(history[-1]["id"])] == ["v1"]
    assert [line["v"] for line in note.body_at(history[0]["id"])] == ["v3"]


def test_paragraph_attribute_is_versioned(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "x")
    lid = note.body[0]["id"]  # type: ignore[index]

    note.set_paragraph(lid, {"heading": 1})
    note.save()

    history = note.history()
    assert len(history) == 2
    assert note.body_at(history[-1]["id"])[0].get("p") is None
    assert note.body_at(history[0]["id"])[0].get("p") == {"heading": 1}


def test_diff_is_reverse_and_incremental(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "hello world")
    note.update(text="hello cairn")

    head = note.history()[0]["id"]
    rows = vault.bucket.query("SELECT payload FROM versions WHERE id = ?", (head,))
    patch = decode_canonical(bytes(rows[0]["payload"]))
    lids = [line["id"] for line in note.body]
    assert patch[lids[0]] == {"act": "PUT", "v": "hello world"}


def test_lazy_compaction_drops_expired(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "v1")
    note.update(text="v2")
    assert len(note.history()) == 2

    removed = VersionStore(vault.bucket).compact(note.id, retention_ms=0)
    assert removed == 2
    assert note.history() == []
