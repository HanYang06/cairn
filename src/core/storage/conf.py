# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""存储自己的一组配置（**存储的参数由存储声明，配置端只负责展开**）。

跑一次 ``uv run python tools/gen_conf.py`` 就会把它们展开成两份投影::

    config/settings/core/storage/conf.json    值（带默认值）
    schema/settings/core/storage/conf.json    词表（IDE 提示用）

（``settings`` 是默认 hub；换 hub 即换一组投影，见 `core.conf.engine`。）

取用::

    from core.storage.conf import conf

    batch = conf.pack_max_blocks
"""

from __future__ import annotations

from core.types.cfg import Cfg


class StorageConf:
    """存储参数（分片粒度 / 载体 / 版本保留窗）。"""

    block_max_bytes: Cfg = Cfg(
        "storage.block.max_bytes",
        1024 * 1024,
        doc="单个块的字节上限，超过即分片（分片 + 索引块）",
    )
    pack_max_blocks: Cfg = Cfg(
        "storage.pack.max_blocks",
        4096,
        doc="单个载体最多装多少块，写满即封口",
    )
    pack_max_bytes: Cfg = Cfg(
        "storage.pack.max_bytes",
        1024 * 1024 * 1024,
        doc="单个载体字节上限，写满即封口",
    )
    version_retention_days: Cfg = Cfg(
        "storage.version.retention_days",
        30,
        doc="版本保留窗（天）：**预留**——惰性压实尚未实现，当前无读取点",
    )


conf = StorageConf()
"""存储配置入口。"""


__all__ = ["StorageConf", "conf"]
