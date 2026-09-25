# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""配置：**声明即事实，两个投影落在磁盘上**。

    config/settings/<包树>/<file_name>.<config_file_type>   ← 值（软配置）
    schema/settings/<包树>/<file_name>.json                 ← 词表（永远 json）

（``settings`` 是默认 hub；换 hub 即换一组投影，见 `core.conf.engine`。）

声明用 ``core.types.cfg.Cfg`` 写在各模块自己的声明模块里（**各管各的**；可叫 ``conf.py``，
但 ``core/conf`` 自己那个得叫 ``params.py``——包名与同名子模块会互相覆盖），绑上即报到；
引擎把声明展开成上面两个文件，并按「文件 → 默认值 → 报错」取用。细则见 `core.conf.engine`。
"""

from __future__ import annotations

from .engine import (
    CONFIG_FILE_TYPE,
    CONFIG_HUB,
    CONFIG_PATH,
    SCHEMA_FILE_TYPE,
    SETTINGS_SCHEMA_ID,
    ConfEngine,
    Folder,
    conf,
    find_root,
    source_path,
)
from .errors import (
    ConfigConflictError,
    ConfigError,
    ConfigFileError,
    ConfigKeyError,
    ConfigValueError,
)

__all__ = [
    "CONFIG_FILE_TYPE",
    "CONFIG_HUB",
    "CONFIG_PATH",
    "SCHEMA_FILE_TYPE",
    "SETTINGS_SCHEMA_ID",
    "ConfEngine",
    "ConfigConflictError",
    "ConfigError",
    "ConfigFileError",
    "ConfigKeyError",
    "ConfigValueError",
    "Folder",
    "conf",
    "find_root",
    "source_path",
]
