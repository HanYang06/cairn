# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

import pytest

from cairn.core import Vault
from cairn.domains import (
    KindMismatchError,
    Note,
    Relation,
    Signature,
    known_kinds,
)

PASSPHRASE = "correct horse battery staple"


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault", PASSPHRASE)


def test_registry_has_builtin_kinds() -> None:
    assert {"cairn.note", "cairn.asset", "cairn.project"} <= set(known_kinds())


def test_note_roundtrip(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "hello world", title="Hi", tags=["a", "b"])

    assert note.text == "hello world"
    assert note.title == "Hi"
    assert note.tags == {"a": None, "b": None}
    assert note.info.type == "cairn.note"

    loaded = Note.load(vault, note.oid)
    assert loaded.text == "hello world"


def test_note_update_preserves_created_meta(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "v1", title="t1", props={"color": "red"})
    before = vault.info(note.oid)

    note.update(text="v2")

    assert note.text == "v2"
    assert note.title == "t1"
    assert note.props()["color"] == "red"

    after = vault.info(note.oid)
    assert after.created == before.created
    assert after.updated >= before.updated


def test_note_list_and_delete(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    first = Note.create(vault, "a")
    second = Note.create(vault, "b")

    assert {note.oid for note in Note.list(vault)} == {first.oid, second.oid}

    first.delete()
    assert {note.oid for note in Note.list(vault)} == {second.oid}


def test_kind_mismatch(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "x")

    with pytest.raises(KindMismatchError):
        Relation.load(vault, note.oid)


def test_note_authors_and_dict_tags(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "x", tags={"作者": "韩", "草稿": None})
    note.author = "韩"
    note.authors = ["韩", {"name": "石"}]
    note.save()

    loaded = Note.load(vault, note.oid)
    assert loaded.tags == {"作者": "韩", "草稿": None}
    assert loaded.author == "韩"
    assert loaded.authors == ["韩", {"name": "石"}]

    assert {info.oid for info in vault.iter(tags={"作者": "韩"})} == {note.oid}
    assert {info.oid for info in vault.iter(tags={"作者": "石"})} == set()


def test_body_pool_dedupes_across_attrs(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    first = Note.create(vault, "same body", title="A")
    second = Note.create(vault, "same body", title="B")

    assert first.body.hash == second.body.hash
    assert vault.bucket.catalog.count_contents() == 1   # body 内容池里只有一份
    assert vault.bucket.catalog.count_blocks() == 2      # 属性各自独立


def test_note_creation_signature_is_composite(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note.create(vault, "正文", title="T")

    signature = note.signature
    assert isinstance(signature, Signature)
    assert signature.verify()
    assert signature.subject == note.body.hash
    assert signature.encoded().startswith("cn1.")

    loaded = Note.load(vault, note.oid)
    assert isinstance(loaded.signature, Signature)
    assert loaded.signature.verify()
    assert loaded.signature.value == signature.value


def test_signature_tamper_is_detected() -> None:
    signature = Signature.create(author="韩", subject="abc")
    assert signature.verify()

    tampered = Signature.from_data({**signature.to_data(), "author": "石"})
    assert not tampered.verify()


def test_relation_backlinks_and_outbound(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source = Note.create(vault, "source")
    target = Note.create(vault, "target")

    relation = Relation.create(vault, source.oid, target.oid, relation="annotates")
    assert relation.source == source.oid
    assert relation.target == target.oid
    assert relation.relation == "annotates"

    backlinks = [rel.oid for rel in Relation.backlinks(vault, target.oid)]
    assert backlinks == [relation.oid]

    outbound = [rel.oid for rel in Relation.outbound(vault, source.oid)]
    assert outbound == [relation.oid]
