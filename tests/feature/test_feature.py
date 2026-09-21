# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from core import Vault
from feature import (
    KindMismatchError,
    Note,
    Relation,
    Signature,
    known_kinds,
)

if TYPE_CHECKING:
    from pathlib import Path


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_registry_has_builtin_kinds() -> None:
    assert {"notedata", "asset", "projectdata"} <= set(known_kinds())


def test_note_roundtrip(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    note = notes.create("hello world", title="Hi", tags=["a", "b"])

    assert note.text == "hello world"
    assert note.title == "Hi"
    assert note.tags == {"a": None, "b": None}
    assert note.info.type == "notedata"

    loaded = notes.load(note.oid)
    assert loaded.text == "hello world"


def test_note_update_preserves_created_meta(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    note = notes.create("v1", title="t1", props={"color": "red"})
    before = vault.info(note.oid)

    notes.update(note, text="v2")

    assert note.text == "v2"
    assert note.title == "t1"
    assert note.props()["color"] == "red"

    after = vault.info(note.oid)
    assert after.created == before.created
    assert after.updated >= before.updated


def test_note_list_and_delete(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    first = notes.create("a")
    second = notes.create("b")

    assert {note.oid for note in notes.list_notes()} == {first.oid, second.oid}

    first.delete()
    assert {note.oid for note in notes.list_notes()} == {second.oid}


def test_kind_mismatch(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = Note(vault).create("x")

    with pytest.raises(KindMismatchError):
        Relation.load(vault, note.oid)


def test_note_authors_and_dict_tags(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    note = notes.create("x", tags={"作者": "韩", "草稿": None})
    note.author = "韩"
    note.authors = ["韩", {"name": "石"}]
    notes.save(note)

    loaded = notes.load(note.oid)
    assert loaded.tags == {"作者": "韩", "草稿": None}
    assert loaded.author == "韩"
    assert loaded.authors == ["韩", {"name": "石"}]

    assert {info.oid for info in vault.iter(tags={"作者": "韩"})} == {note.oid}
    assert {info.oid for info in vault.iter(tags={"作者": "石"})} == set()


def test_body_pool_dedupes_across_attrs(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    first = notes.create("same body", title="A")
    second = notes.create("same body", title="B")

    assert first.body.hash == second.body.hash
    assert vault.bucket.catalog.count_bodies() == 1  # body 内容池里只有一份
    assert vault.bucket.catalog.count_blocks() == 2  # 属性各自独立


def test_same_content_different_line_ids_coexist(tmp_path: Path) -> None:
    """同文但行 id 不同的两条笔记：去重键含行 id，读回不得串成别人的行 id。"""
    vault = _vault(tmp_path)
    notes = Note(vault)
    first = notes.create("same body")
    second = notes.create("same body")
    # 模拟编辑过程中行 id 变化（拆分 / 删除重插等），正文内容保持不变
    second.body.text = [dict(second.body[0], id="01ARZ3NDEKTSV4RRFFQ69G5FAV")]
    second.body.refresh()
    notes.save(second)

    assert first.body.hash == second.body.hash  # 内容签名（剥离行 id）一致
    assert vault.bucket.catalog.count_bodies() == 2  # 负载口径不同 → 各存一份
    loaded = notes.load(second.oid)
    assert loaded.body[0]["id"] == "01ARZ3NDEKTSV4RRFFQ69G5FAV"


def test_note_creation_signature_is_composite(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    note = notes.create("正文", title="T")

    signature = note.signature
    assert isinstance(signature, Signature)
    assert signature.verify()
    assert signature.subject == note.body.hash
    assert signature.encoded().startswith("cn1.")

    loaded = notes.load(note.oid)
    assert isinstance(loaded.signature, Signature)
    assert loaded.signature.verify()
    assert loaded.signature.value == signature.value


def test_signature_tamper_is_detected() -> None:
    signature = Signature.create(author="韩", subject="abc")
    assert signature.verify()

    tampered = Signature.from_data({**signature.to_data(), "author": "石"})
    assert not tampered.verify()


def test_signature_from_data_fails_closed() -> None:
    assert Signature.from_data(None).verify() is False
    assert Signature.from_data({"created": None}).verify() is False
    with pytest.raises(TypeError):
        Signature.from_data([1])


def test_relation_backlinks_and_outbound(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    source = notes.create("source")
    target = notes.create("target")

    relation = Relation.create(vault, source.oid, target.oid, relation="annotates")
    assert relation.source == source.oid
    assert relation.target == target.oid
    assert relation.relation == "annotates"

    backlinks = [rel.oid for rel in Relation.backlinks(vault, target.oid)]
    assert backlinks == [relation.oid]

    outbound = [rel.oid for rel in Relation.outbound(vault, source.oid)]
    assert outbound == [relation.oid]
