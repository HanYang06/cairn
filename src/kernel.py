# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""应用内核（组合根）：通信主干 + 静态领域树。

**只有这里认识领域**（构造域服务并静态挂到主干上）；`subject` 的数据内核 `core` 保持领域无关，
`ui/` 不 import `feature`。主干本体在 `core.signal`，领域树在此**静态声明**（无动态注册 / 内省）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from feature import Note

if TYPE_CHECKING:
    from core import Vault
    from core.signal import Signal


class Feature:
    """静态声明的领域容器（IDE 可识别）。"""

    Note: Note

    def __init__(self, vault: Vault, signal: Signal) -> None:
        self.Note = Note(vault).bind(signal)


class Kernel:
    """一个库的应用内核：主干 + 领域树。"""

    def __init__(self, vault: Vault) -> None:
        self.signal = vault.signal
        self.feature = Feature(vault, self.signal)
        self.signal.feature = self.feature  # 挂到主干（普通属性赋值）


__all__ = ["Feature", "Kernel"]
