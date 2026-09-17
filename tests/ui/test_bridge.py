# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`SessionBridge`：内核变更 → Qt 信号（合并）测试。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cairn.core import Vault
from cairn.domains import Note
from cairn.ui.bridge import SessionBridge
from cairn.ui.session import Session

if TYPE_CHECKING:
    from pathlib import Path


def test_bridge_flush_emits_coalesced(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    session = Session(vault)
    bridge = SessionBridge(session)

    changes: list[int] = []
    oids: list[str] = []
    bridge.changed.connect(lambda: changes.append(1))
    bridge.object_changed.connect(oids.append)

    note = Note.create(vault, "x")
    assert changes == []  # 事件循环未跑，尚未发出

    bridge.flush()
    assert changes == [1]
    assert str(note.oid) in oids

    bridge.dispose()
    session.close()
    vault.close()
