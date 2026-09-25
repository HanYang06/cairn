# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""配置错误：**能补的补，补不了的喊**，不猜、不静默。"""

from __future__ import annotations

from core.types import CairnError


class ConfigError(CairnError):
    """配置层错误基类。"""


class ConfigKeyError(ConfigError):
    """配置项没有登记默认值，文件里也丢了——**补不了**。"""


class ConfigValueError(ConfigError):
    """配置项在文件里存在但值是空的——文件被改坏了，**不自动修**。"""


class ConfigFileError(ConfigError):
    """配置文件本身不可用（JSON 坏了 / 根对象不是映射）。"""


class ConfigConflictError(ConfigError):
    """投影目标路径上压着**不是本引擎写的**文件——拒写，绝不覆盖别人的东西。"""


__all__ = [
    "ConfigConflictError",
    "ConfigError",
    "ConfigFileError",
    "ConfigKeyError",
    "ConfigValueError",
]
