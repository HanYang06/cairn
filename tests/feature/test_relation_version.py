# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from core import Vault
from feature import Note, Relation
from feature.shared.provenance import DERIVED_FROM

if TYPE_CHECKING:
    from pathlib import Path


def test_relation_pins_version(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    notes = Note(vault)
    source = notes.create("源", title="源")
    child = notes.create("子", title="子")

    edge = Relation.create(
        vault,
        child.oid,
        source.oid,
        relation=DERIVED_FROM,
        props={"at": str(source.info.seq)},
    )
    assert edge.at == str(source.info.seq)
    assert edge.source == child.oid
    assert edge.target == source.oid


def test_relation_delete_removes_matching_edges(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    notes = Note(vault)
    source = notes.create("源")
    child = notes.create("子")
    Relation.create(vault, child.oid, source.oid, relation=DERIVED_FROM)
    Relation.create(vault, child.oid, source.oid, relation="references")

    removed = Relation.delete(vault, source=child.oid, target=source.oid, relation=DERIVED_FROM)

    assert removed == 1
    assert [edge.relation for edge in Relation.outbound(vault, child.oid)] == ["references"]


def test_relation_delete_without_kind_removes_all(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    notes = Note(vault)
    source = notes.create("源")
    child = notes.create("子")
    Relation.create(vault, child.oid, source.oid, relation=DERIVED_FROM)
    Relation.create(vault, child.oid, source.oid, relation="references")

    removed = Relation.delete(vault, source=child.oid, target=source.oid)

    assert removed == 2
    assert list(Relation.outbound(vault, child.oid)) == []
