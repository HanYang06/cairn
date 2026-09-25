# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""应用层：组合内核 / 领域 / `ui_tools`，按平台发布。

**只有 App 认识领域**（建域服务、受内核管辖）；平台 UI 在子包（`win` / …）。

内核是**单例**：域服务只需要建一次；重复建会撞名字（`core.role("note")` 已经是它）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from feature import Note

if TYPE_CHECKING:
    from core.core import Core


class Feature:
    """静态声明的领域装配：**已经有了就取用，没有才建**。"""

    Note: Note

    def __init__(self, core: Core) -> None:
        existing = core.role("note")
        self.Note = existing if isinstance(existing, Note) else Note(core)


__all__ = ["Feature"]
