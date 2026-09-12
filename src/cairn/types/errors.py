# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""基础异常体系（跨层共享）。"""

from __future__ import annotations


class CairnError(Exception):
    """所有 cairn 异常的基类。"""


class InvalidIdError(CairnError, ValueError):
    """标识符格式非法。"""


class AuthError(CairnError):
    """认证或解密失败。"""


class VaultError(CairnError):
    """库级错误。"""


class VaultLockedError(VaultError):
    """库处于锁定状态。"""


class ObjectNotFoundError(CairnError):
    """对象不存在。"""


class SpaceNotFoundError(CairnError):
    """空间不存在。"""


class CorruptObjectError(CairnError):
    """对象数据损坏或校验失败。"""
