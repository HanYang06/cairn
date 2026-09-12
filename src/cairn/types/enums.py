# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""枚举类型。"""

from __future__ import annotations

from enum import Enum


class Visibility(Enum):
    """可见性档位，决定密钥分发与去重范围。"""

    PRIVATE = "private"
    COMMUNAL = "communal"
    PUBLIC = "public"
    DIRECT = "direct"
