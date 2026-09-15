# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from cairn.core import Vault
from cairn.core.store import decode_canonical
from cairn.domains import Note
from cairn.domains.note.versions import compact


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_version_diff_reconstructs_history(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "v1", title="t")
    note.update(text="v2")
    note.update(text="v3")

    assert [item["seq"] for item in note.history()] == [2, 3]
    assert note.body_at(1) == ["v1"]
    assert note.body_at(2) == ["v2"]
    assert note.body_at(3) == ["v3"]
    assert note.text == "v3"


def test_metadata_only_change_does_not_version(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "x")
    note.update(title="新标题")
    assert note.history() == []


def test_version_diff_is_incremental(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "hello world")
    note.update(text="hello cairn")

    rows = vault.bucket.query("SELECT diff FROM versions WHERE oid = ?", (note.id,))
    assert len(rows) == 1
    diff = decode_canonical(bytes(rows[0]["diff"]))
    # 存的是"从新版回上一版"的 diff：把 "hello cairn" 改回 "hello world"
    assert diff == {"i": 0, "off": 6, "del": 5, "ins": "world"}


def test_lazy_compaction_drops_expired(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "v1")
    note.update(text="v2")
    assert note.history() != []

    removed = compact(vault, note.id, retention_ms=0)
    assert removed == 1
    assert note.history() == []
