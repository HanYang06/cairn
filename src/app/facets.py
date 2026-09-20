# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""App 侧的领域 UI：笔记域的 `Facet`。

**不放工具箱**（`ui_tools` 只提供通用件）；领域 UI 由 App 承担、组装。
不 import `feature`：只按鸭子类型使用**注入的**域服务。
"""

from __future__ import annotations

from typing import Any

from ui_tools.component import Label
from ui_tools.core import Facet, Session
from ui_tools.layout import VBox


class NoteFacet(Facet):
    """笔记域 UI 定义（列表页 + 简单条目）。"""

    def __init__(self, note: Any, session: Session) -> None:
        super().__init__(note, name="note")
        self.session = session
        self.set(VBox)
        self.add(Label("笔记"))
        for data in session.projection("notes", lambda: list(note.list_notes())):
            self.add(Label(str(getattr(data, "title", "") or "（无标题）")))


__all__ = ["NoteFacet"]
