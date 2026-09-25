# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""核心层：**内核**（配置 + 信号引擎 + 存储 + 类型地基）。

对外：

- `core.core.Core`：内核本体（单例；两张对象表 + 引擎挂载点 + 最小 API）
- `core.signal.Signal`：信号与事件处理引擎
- `core.storage`：存储实现（桶 / 块 / 目录）与它的引擎角色
- `core.conf.Conf`：配置
- `core.types`：类型地基（错误 / 标识符 / 类型表 / 标注 / 事件数据结构）
"""

from __future__ import annotations

from .conf import Conf
from .core import Core, Managed
from .signal import Signal
from .types import (
    CairnError,
    CorruptObjectError,
    ObjectInfo,
    ObjectNotFoundError,
    Oid,
)

__all__ = [
    "CairnError",
    "Conf",
    "Core",
    "CorruptObjectError",
    "Managed",
    "ObjectInfo",
    "ObjectNotFoundError",
    "Oid",
    "Signal",
]
