# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""配置管理器（**尚未接线**：配置引擎随下一片引入）。"""

from __future__ import annotations


class Conf:
    """内核配置入口（**预留**）。

    现状：本片只做内核主干，配置引擎（声明即事实、两个投影落盘）随下一片引入，
    故这里**实例化即报错**——给一个什么都不做的空壳，只会让使用方以为配置已经可用。
    """

    def __init__(self) -> None:
        raise NotImplementedError("配置引擎尚未接线：随下一片引入")


__all__ = ["Conf"]
