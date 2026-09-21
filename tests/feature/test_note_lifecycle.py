# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记领域底层的端到端生命周期：一次把整体跑通，暴露缺口。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from core import ObjectNotFoundError, Vault
from feature import AssetData, CanvasData, Note, Relation
from feature.note import Form, Graphic

if TYPE_CHECKING:
    from pathlib import Path


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_note_full_lifecycle(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    notes = Note(vault)
    target = notes.create("被引用", title="B")

    # 1) 创建 + 属性
    note = notes.create("原始正文", title="A", tags={"作者": "韩"}, props={"color": "red"})
    note.author = "韩"
    note.authors = ["韩", "石"]
    note.signature = "sig-001"
    notes.save(note)

    # 2) 正文版本（文本编辑）
    notes.update(note, text="中间版")
    notes.update(note, text="改过")

    # 3) 画板 + 外联资源嵌入（各自都会 save 并记版本）
    asset = AssetData.create(vault, b"PNG-DATA", name="a.png")
    notes.add_access(note, asset.oid, mime="image/png", name="a.png")
    canvas = CanvasData.create(
        vault,
        graphics=[Graphic(form=Form.CIRCLE, cx=0.0, cy=0.0, w=2.0, h=2.0)],
    )
    notes.add_canvas(note, canvas)

    # 4) 关系（引用）
    notes.link(note, target.oid, relation="references")

    # 5) 重开：整体持久化校验
    vault.close()
    reopened = Vault.load(tmp_path / "vault")
    reloaded = Note(reopened)
    loaded = reloaded.load(note.oid)

    assert loaded.title == "A"
    assert loaded.tags == {"作者": "韩"}
    assert loaded.author == "韩"
    assert loaded.authors == ["韩", "石"]
    assert loaded.signature == "sig-001"
    assert loaded.props()["color"] == "red"

    assert loaded.canvas
    loaded_canvas = CanvasData.load(reopened, loaded.canvas[0])
    assert loaded_canvas.body.graphics[0].form == int(Form.CIRCLE)
    assert loaded.access[0] == str(asset.oid)
    assert loaded.references == (asset.oid,)
    assert loaded.body[-1]["v"] == {"canvas": 0}

    # 6) 版本可重建（最新在前：canvas → access → 改过 → 中间版 → 原始正文）
    history = reloaded.history(loaded)
    assert len(history) == 5
    assert [line["v"] for line in reloaded.body_at(loaded, history[2]["id"])] == ["改过"]
    assert [line["v"] for line in reloaded.body_at(loaded, history[3]["id"])] == ["中间版"]
    assert [line["v"] for line in reloaded.body_at(loaded, history[-1]["id"])] == ["原始正文"]
    assert loaded.text == "改过"

    # 7) 关系拓扑
    outbound = list(Relation.outbound(reopened, loaded.oid, relation="references"))
    assert [edge.target for edge in outbound] == [target.oid]
    backlinks = list(Relation.backlinks(reopened, target.oid, relation="references"))
    assert [edge.source for edge in backlinks] == [loaded.oid]

    # 8) 检索
    assert str(loaded.oid) in {str(oid) for oid in reopened.search("改过")}

    # 9) 删除
    loaded.delete()
    with pytest.raises(ObjectNotFoundError):
        reloaded.load(note.oid)
