# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from core import Vault
from feature import (
    Asset,
    Note,
    Project,
    Relation,
    ancestors,
    descendants,
    known_kinds,
)
from feature.asset import transcode, unified_target

if TYPE_CHECKING:
    from pathlib import Path


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_registry_includes_three_piece_kinds() -> None:
    assert {
        "cairn.note",
        "cairn.asset",
        "cairn.project",
    } <= set(known_kinds())


def test_asset_from_bytes(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    asset = Asset.create(vault, b"\x89PNG...", name="logo.png")

    assert asset.name == "logo.png"
    assert asset.content_type == "image/png"
    assert asset.size == len(b"\x89PNG...")
    assert Asset.load(vault, asset.oid).read() == b"\x89PNG..."


def test_unified_target_and_identity_transcode() -> None:
    assert unified_target("image/jpeg") == "image/png"
    assert unified_target("audio/wav") == "audio/flac"
    assert unified_target("application/pdf") is None
    assert unified_target(None) is None

    data, mime = transcode(b"\x00\x01", "image/jpeg")
    assert data == b"\x00\x01"
    assert mime == "image/jpeg"


def test_asset_records_origin_mime(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    asset = Asset.create(vault, b"raw", name="clip.mp4", mime="video/mp4")
    assert asset.attrs["origin_mime"] == "video/mp4"


def test_asset_from_path(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source = tmp_path / "data.bin"
    source.write_bytes(b"binary payload")

    asset = Asset.create(vault, source, name="data.bin")
    assert asset.read() == b"binary payload"


def test_note_embed_and_link(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    image = Asset.create(vault, b"img", name="a.png")
    notes = Note(vault)
    other = notes.create("target")

    note = notes.create("see this")
    notes.add_access(note, image.oid, mime="image/png", name="a.png")
    notes.link(note, other.oid, relation="references")

    assert note.references == (image.oid,)
    assert note.access[0] == str(image.oid)
    assert note.body[-1]["v"] == {"access": 0}

    backlinks = [edge.oid for edge in Relation.backlinks(vault, other.oid)]
    assert len(backlinks) == 1


def test_project_members(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    project = Project.create(vault, "Cairn", description="工作台")
    notes = Note(vault)
    first = notes.create("a")
    second = notes.create("b")

    project.add_member(first.oid)
    project.add_member(second.oid)

    assert project.name == "Cairn"
    assert project.description == "工作台"
    assert set(project.members()) == {first.oid, second.oid}


def test_provenance_lineage(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    original = notes.create("original")
    remix = notes.create("remix")
    again = notes.create("again")

    Relation.create(vault, remix.oid, original.oid, relation="derived-from")
    Relation.create(vault, again.oid, remix.oid, relation="derived-from")

    assert descendants(vault, original.oid) == (remix.oid, again.oid)
    assert ancestors(vault, again.oid) == (remix.oid, original.oid)
