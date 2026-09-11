from __future__ import annotations

from pathlib import Path

from cairn.core import Vault
from cairn.domains import (
    Asset,
    Note,
    Project,
    Relation,
    ancestors,
    descendants,
    known_kinds,
)

PASSPHRASE = "correct horse battery staple"


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault", PASSPHRASE)


def test_registry_includes_three_piece_kinds() -> None:
    assert {
        "cairn.note",
        "cairn.asset",
        "cairn.project",
        "cairn.relation",
        "cairn.composition",
    } <= set(known_kinds())


def test_asset_from_bytes(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    asset = Asset.create(vault, b"\x89PNG...", name="logo.png")

    assert asset.name == "logo.png"
    assert asset.content_type == "image/png"
    assert asset.size == len(b"\x89PNG...")
    assert Asset.load(vault, asset.oid).read() == b"\x89PNG..."


def test_asset_from_path(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source = tmp_path / "data.bin"
    source.write_bytes(b"binary payload")

    asset = Asset.create(vault, source, name="data.bin")
    assert asset.read() == b"binary payload"


def test_note_embed_and_link(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    image = Asset.create(vault, b"img", name="a.png")
    other = Note.create(vault, "target")

    note = Note.create(vault, "see this")
    note.add_embed(image.oid, role="image", caption="figure 1")
    note.link(other.oid, relation="references")

    assert note.references == (image.oid,)
    assert note.embeds[0]["role"] == "image"
    assert note.embeds[0]["caption"] == "figure 1"

    backlinks = [edge.oid for edge in Relation.backlinks(vault, other.oid)]
    assert len(backlinks) == 1


def test_project_members(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    project = Project.create(vault, "Cairn", description="工作台")
    first = Note.create(vault, "a")
    second = Note.create(vault, "b")

    project.add_member(first.oid)
    project.add_member(second.oid)

    assert project.name == "Cairn"
    assert project.description == "工作台"
    assert set(project.members()) == {first.oid, second.oid}


def test_provenance_lineage(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    original = Note.create(vault, "original")
    remix = Note.create(vault, "remix")
    again = Note.create(vault, "again")

    Relation.create(vault, remix.oid, original.oid, relation="derived-from")
    Relation.create(vault, again.oid, remix.oid, relation="derived-from")

    assert descendants(vault, original.oid) == (remix.oid, again.oid)
    assert ancestors(vault, again.oid) == (remix.oid, original.oid)
