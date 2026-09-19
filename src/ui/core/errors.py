# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 内核错误。"""

from __future__ import annotations


class UiError(Exception):
    """UI 内核错误基类。"""


class LayoutError(UiError):
    """布局 / 槽操作非法（不可增、超容量等）。"""
