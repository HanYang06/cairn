# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""端到端链路：内核写入 → Session → Bridge → 模型自动更新。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt

from cairn.core import Vault
from cairn.domains import Note
from cairn.ui.bridge import SessionBridge
from cairn.ui.models import ListModel
from cairn.ui.session import Session

if TYPE_CHECKING:
    from pathlib import Path

    from cairn.ui.rows import NoteRow


def test_kernel_change_flows_to_model(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    session = Session(vault)
    bridge = SessionBridge(session)
    model: ListModel[NoteRow] = ListModel([("title", lambda row: row.title)], display="title")

    # 页面里一行代码即可：桥一变，模型跟着变。
    bridge.changed.connect(lambda: model.set_rows(session.note_rows()))

    assert model.rowCount() == 0

    note = Note.create(vault, "x", title="甲")
    bridge.flush()
    assert model.rowCount() == 1
    assert model.data(model.index(0, 0), int(Qt.ItemDataRole.DisplayRole)) == "甲"

    note.update(title="乙")
    bridge.flush()
    assert model.data(model.index(0, 0), int(Qt.ItemDataRole.DisplayRole)) == "乙"

    vault.delete(note.oid)
    bridge.flush()
    assert model.rowCount() == 0

    bridge.dispose()
    session.close()
    vault.close()
