# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""内核自身的一组配置。

**约定**：一组配置一个声明模块（就在声明方自己的包里，文件名用 ``params.py`` 之类，
**别叫** ``conf.py``——包名与同名子模块会互相覆盖），类体里用 ``Cfg`` 声明::

    from core.conf.params import conf

    level = conf.log_level

声明即登记——引擎据此把两份投影展开到 ``config/settings/core/conf/params.json``
与 ``schema/settings/core/conf/params.json``（``settings`` 是默认 hub，见 `core.conf.engine`）。
"""

from __future__ import annotations

from core.types.cfg import Cfg


class CoreConf:
    """内核参数（基础件那一层）。"""

    log_level: Cfg = Cfg("core.log.level", "WARNING", doc="内核日志级别")


conf = CoreConf()
"""内核配置入口（实例化只为当门面；值由声明 + 配置文件共同决定）。"""


__all__ = ["CoreConf", "conf"]
