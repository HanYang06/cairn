# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from cairn.core import Vault


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault", "pw")


def test_search_find_update_delete(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = vault.put(b"", type="cairn.note", search_text="apple banana")
    other = vault.put(b"", type="cairn.note", search_text="cherry")

    found = {str(oid) for oid in vault.search("banana")}
    assert str(note) in found
    assert str(other) not in found

    vault.put(b"", oid=note, type="cairn.note", search_text="apple durian")
    assert str(note) not in {str(oid) for oid in vault.search("banana")}
    assert str(note) in {str(oid) for oid in vault.search("durian")}

    vault.delete(note)
    assert str(note) not in {str(oid) for oid in vault.search("durian")}


def test_rebuild_index_populates_search(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    oid = vault.put(b"", type="cairn.note")  # 未提供检索文本
    assert vault.search("seeded") == []

    vault.rebuild_index(text_of=lambda _manifest: "seeded body")
    assert str(oid) in {str(item) for item in vault.search("seeded")}
