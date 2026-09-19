# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from core import Vault
from feature import Note, Relation
from feature.provenance import DERIVED_FROM

if TYPE_CHECKING:
    from pathlib import Path


def test_relation_pins_version(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault", "pw")
    source = Note.create(vault, "源", title="源")
    child = Note.create(vault, "子", title="子")

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
