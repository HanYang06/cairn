# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""应用层：组合内核 / 领域 / `ui_tools`，按平台发布。

**只有 App 认识领域**（构造域服务、静态挂载）；平台 UI 在子包（`win` / …）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from feature import Note

if TYPE_CHECKING:
    from core import Vault
    from core.signal import Signal


class Feature:
    """静态声明的领域容器（IDE 可识别；无动态注册 / 内省）。"""

    Note: Note

    def __init__(self, vault: Vault, signal: Signal) -> None:
        self.Note = Note(vault).bind(signal)


__all__ = ["Feature"]
