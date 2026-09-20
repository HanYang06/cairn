# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记域的 Facet（示例）：收**注入的**笔记域服务，声明列表页形态。

**不 import `feature`**：只按鸭子类型使用注入对象；类型提示用 `Any` 即可。
"""

from __future__ import annotations

from typing import Any

from .component import Label
from .core import Facet, Session
from .layout import VBox


class NoteFacet(Facet):
    """笔记域 UI 定义（列表页 + 简单条目）。"""

    def __init__(self, notes: Any, session: Session) -> None:
        super().__init__(notes, name="note")
        self.session = session
        self.set(VBox)
        self.add(Label("笔记"))
        for data in session.projection("notes", lambda: list(notes.list_notes())):
            self.add(Label(str(getattr(data, "title", "") or "（无标题）")))


__all__ = ["NoteFacet"]
