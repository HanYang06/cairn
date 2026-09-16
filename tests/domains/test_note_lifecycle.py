# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记领域底层的端到端生命周期：一次把整体跑通，暴露缺口。"""

from __future__ import annotations

from pathlib import Path

import pytest

from cairn.core import ObjectNotFoundError, Vault
from cairn.domains import Asset, Note, Relation
from cairn.domains.note.types import Canvas, Form, Graphic


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_note_full_lifecycle(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    target = Note.create(vault, "被引用", title="B")

    # 1) 创建 + 属性
    note = Note.create(vault, "原始正文", title="A", tags={"作者": "韩"}, props={"color": "red"})
    note.author = "韩"
    note.authors = ["韩", "石"]
    note.signature = "sig-001"
    note.save()

    # 2) 正文版本（文本编辑）
    note.update(text="中间版")
    note.update(text="改过")

    # 3) 画板 + 多媒体嵌入（各自都会 save 并记版本）
    asset = Asset.create(vault, b"PNG-DATA", name="a.png")
    note.add_access(asset.oid, mime="image/png", name="a.png")
    note.add_canvas(Canvas(graphics=[Graphic(form=Form.CIRCLE, cx=0.0, cy=0.0, w=2.0, h=2.0)]))

    # 4) 关系（引用）
    note.link(target.oid, relation="references")

    # 5) 重开：整体持久化校验
    vault.close()
    reopened = Vault.load(tmp_path / "vault")
    loaded = Note.load(reopened, note.oid)

    assert loaded.title == "A"
    assert loaded.tags == {"作者": "韩"}
    assert loaded.author == "韩"
    assert loaded.authors == ["韩", "石"]
    assert loaded.signature == "sig-001"
    assert loaded.props()["color"] == "red"

    assert isinstance(loaded.canvas[0], Canvas)
    assert loaded.canvas[0].graphics[0].form == int(Form.CIRCLE)
    assert loaded.access[0].oid == str(asset.oid)
    assert loaded.references == (asset.oid,)
    assert loaded.body[-1]["v"] == {"canvas": 0}

    # 6) 版本可重建（最新在前：canvas → access → 改过 → 中间版 → 原始正文）
    history = loaded.history()
    assert len(history) == 5
    assert [line["v"] for line in loaded.body_at(history[2]["id"])] == ["改过"]
    assert [line["v"] for line in loaded.body_at(history[3]["id"])] == ["中间版"]
    assert [line["v"] for line in loaded.body_at(history[-1]["id"])] == ["原始正文"]
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
        Note.load(reopened, note.oid)
