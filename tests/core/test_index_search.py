# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from core import Vault
from core.storage import Block

if TYPE_CHECKING:
    from pathlib import Path


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_search_find_update_delete(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    note = vault.put_block(Block(body=b"", type="test.note"), search_text="apple banana").id
    other = vault.put_block(Block(body=b"", type="test.note"), search_text="cherry").id

    found = {str(oid) for oid in vault.search("banana")}
    assert note in found
    assert other not in found

    vault.put_block(Block(id=note, body=b"", type="test.note"), search_text="apple durian")
    assert note not in {str(oid) for oid in vault.search("banana")}
    assert note in {str(oid) for oid in vault.search("durian")}

    vault.delete(note)
    assert note not in {str(oid) for oid in vault.search("durian")}


def test_rebuild_index_populates_search(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    oid = vault.put_block(Block(body=b"", type="test.note")).id  # 未提供检索文本
    assert vault.search("seeded") == []

    vault.rebuild_index(text_of=lambda _manifest: "seeded body")
    assert oid in {str(item) for item in vault.search("seeded")}


def test_resave_without_search_text_keeps_index(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    oid = vault.put_block(Block(body=b"", type="test.note"), search_text="keep me").id
    vault.put_block(Block(id=oid, body=b"", type="test.note"))  # 不带检索文本
    assert oid in {str(item) for item in vault.search("keep")}


def test_rebuild_index_requires_text_of(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    with pytest.raises(ValueError, match="text_of"):
        vault.rebuild_index()


def test_search_treats_like_wildcards_literally(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    oid = vault.put_block(Block(body=b"", type="test.note"), search_text="100% real_value").id
    found = {str(item) for item in vault.search("%")}
    assert oid in found
    assert oid in {str(item) for item in vault.search("_value")}
    assert vault.search("%_") == []  # 组合通配不当作匹配
    assert oid not in {str(item) for item in vault.search("realXvalue")}
