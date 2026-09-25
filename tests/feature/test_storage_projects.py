# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""资产 / 项目 / 关系：数据落盘走 `core.put`，数据结构仍继承 `Block`。"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import pytest

from core import Core  # noqa: TC001 — 运行期用作 fixture 注解
from feature import (
    AssetData,
    Note,
    Project,
    Relation,
    ancestors,
    descendants,
    known_kinds,
)
from feature.shared.asset import transcode, unified_target

if TYPE_CHECKING:
    from pathlib import Path


def test_registry_includes_three_piece_kinds() -> None:
    assert {
        "notedata",
        "asset",
        "projectdata",
    } <= set(known_kinds())


def test_asset_from_bytes(core: Core) -> None:
    asset = AssetData.create(core, b"\x89PNG...", name="logo.png")

    assert asset.name == "logo.png"
    assert asset.content_type == "image/png"
    assert asset.size == len(b"\x89PNG...")
    assert AssetData.load(core, asset.oid).read() == b"\x89PNG..."


def test_unified_target_and_identity_transcode() -> None:
    assert unified_target("image/jpeg") == "image/png"
    assert unified_target("audio/wav") == "audio/flac"
    raw = b"\x00\x01"
    assert transcode(raw, "image/png") == (raw, "image/png")


def test_asset_records_origin_mime(core: Core) -> None:
    asset = AssetData.create(core, b"x", name="a.jpg", mime="image/jpeg")

    assert asset.origin_mime == "image/jpeg"


def test_asset_mime_reads_back_as_field(core: Core) -> None:
    """mime 是**声明字段**（不再是 ClassVar）：写进去、读回来一致。

    注：JPEG→PNG 的转码是草案占位（`transcode` 目前恒等），故这里不断言被改写。
    """
    asset = AssetData.create(core, b"x", name="a.jpg", mime="image/jpeg")

    assert AssetData.load(core, asset.oid).mime == asset.mime


def test_asset_from_path(core: Core, tmp_path: Path) -> None:
    source = tmp_path / "data.bin"
    source.write_bytes(b"payload")

    asset = AssetData.create(core, source, name="data.bin")

    assert AssetData.load(core, asset.oid).read() == b"payload"


def test_asset_rejects_text_stream(core: Core) -> None:
    with pytest.raises(TypeError):
        AssetData.create(core, io.StringIO("text"), name="x.txt")


def test_note_embed_and_link(core: Core) -> None:
    notes = Note(core)
    note = notes.create("正文")
    asset = AssetData.create(core, b"x", name="a.png")

    notes.add_access(note, asset.oid)
    notes.link(note, asset.oid, relation="references")

    loaded = notes.load(note.oid)
    assert loaded.access == [str(asset.oid)]
    edges = list(Relation.outbound(core, loaded.oid, relation="references"))
    assert [edge.target for edge in edges] == [asset.oid]


def test_project_members(core: Core) -> None:
    projects = Project(core)
    project = projects.create("P")
    note = Note(core).create("n")

    projects.add_member(project, note.oid)

    assert projects.members(project) == [note.oid]


def test_project_update_description_overrides_props(core: Core) -> None:
    projects = Project(core)
    project = projects.create("P", props={"description": "旧"})

    projects.update(project, props={"description": "新"})

    assert project.description == "新"


def test_add_member_is_idempotent(core: Core) -> None:
    projects = Project(core)
    project = projects.create("P")
    note = Note(core).create("n")

    projects.add_member(project, note.oid)
    projects.add_member(project, note.oid)

    assert projects.members(project) == [note.oid]


def test_provenance_lineage(core: Core) -> None:
    notes = Note(core)
    first = notes.create("一")
    second = notes.create("二")

    notes.link(second, first.oid, relation="derived-from")

    assert set(descendants(core, first.oid)) == {second.oid}
    assert set(ancestors(core, second.oid)) == {first.oid}


def test_provenance_cycle_excludes_origin(core: Core) -> None:
    notes = Note(core)
    first = notes.create("一")
    second = notes.create("二")
    notes.link(second, first.oid, relation="derived-from")
    notes.link(first, second.oid, relation="derived-from")

    assert first.oid not in set(ancestors(core, first.oid))
    assert second.oid not in set(descendants(core, second.oid))


def test_relation_normalizes_id_case(core: Core) -> None:
    notes = Note(core)
    note = notes.create("n")

    edge = Relation.create(core, str(note.oid).lower(), note.oid)

    assert str(edge.source) == str(note.oid)
