# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""``Cfg``：**配置项声明**（工具单元家族里的一员，与 ``Attr`` 同族）。

两件事一起干，所以声明与取值不会是两份东西：

1. **声明即登记**：在类体里当类属性绑上时（``__set_name__``），它向登记表报到——
   路径、类型、默认值、说明、归属（宿主类 / 模块）。声明怎么写，配置就长什么样；
2. **读属性即取值**：``StorageConf.pack_max_blocks`` 读到的就是引擎算出来的值
   （文件里的值 → 默认值），不要求使用方知道文件在哪、叫什么。

默认值的语义（作者 2026-09-26 定）：

- 传了值 → 这条**带值注册**，会展开进 ``config/``；
- 没传值 → 只有 ``schema/`` 里出现，``config/`` 里不呈现，值缺失即报错；
- ``empty_ok=True``（增强写法）→ **哪怕值是空的也按默认处理**（``""`` / ``None`` / ``[]``）。

本模块**只依赖标准库**：它属 ``core.types``（地基），不许反向依赖 ``core.conf`` 引擎。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_MISSING = object()


@dataclass(frozen=True, slots=True)
class CfgItem:
    """一条配置声明的**静态描述**（登记表里的事实）。"""

    key: str
    """点分路径（``storage.pack.max_blocks``）。"""

    owner: str
    """宿主类名（给人看）。"""

    module: str
    """宿主类所在模块（决定它展开进哪个文件）。"""

    item: str
    """宿主类里的字段名。"""

    type: type[Any] | None = None
    default: Any = None
    doc: str = ""
    empty_ok: bool = False
    """``default=True`` 的增强写法：空值也按默认处理。"""
    fillable: bool = False
    """是否带值注册（带值才能补进 ``config/``）。"""

    def __post_init__(self) -> None:
        """路径必须是点分形式：空段会让文件归属算不出来。"""
        if not self.key or any(not part for part in self.key.split(".")):
            raise ValueError(f"配置路径非法：{self.key!r}")


_ITEMS: dict[str, CfgItem] = {}


def register(item: CfgItem) -> CfgItem:
    """登记一条配置声明；同一路径重复登记且内容不一致即报错（不静默覆盖）。"""
    found = _ITEMS.get(item.key)
    if found is not None and found != item:
        raise ValueError(f"配置项重复登记且声明不一致：{item.key!r}")
    _ITEMS[item.key] = item
    return item


def items() -> list[CfgItem]:
    """全部声明（按路径排序）。"""
    return [_ITEMS[key] for key in sorted(_ITEMS)]


def item(path: str) -> CfgItem | None:
    """按路径取声明；没登记返回 ``None``。"""
    return _ITEMS.get(path)


def clear() -> None:
    """清空登记表（**给测试隔离用**；产品代码不该调）。"""
    _ITEMS.clear()


class Cfg:
    """配置项声明 / 取值描述符。

    用法::

        class StorageCfg:
            pack_max_blocks: Cfg = Cfg("storage.pack.max_blocks", 4096, doc="单个载体最多装多少块")
            catalog_version: Cfg = Cfg("storage.catalog.version", doc="格式版本：只登记，不给值")

    读到的值由引擎（``core.conf``）算：文件里有 → 文件说了算；文件里没有 → 默认值；
    默认值也没有 → 报错（不猜）。
    """

    def __init__(
        self,
        path: str,
        default: Any = _MISSING,
        *,
        doc: str = "",
        empty_ok: bool = False,
        item_type: type[Any] | None = None,
    ) -> None:
        self.path = path
        self._default = default
        self.doc = doc
        self.empty_ok = empty_ok
        self._item_type = item_type
        self.key = path
        self.owner = ""
        self.field = ""
        self.type: type[Any] | None = None
        self.fillable = default is not _MISSING
        self._default_value = None if default is _MISSING else default
        self._resolved = False

    # ---- 登记：类体里绑上即报到 ----
    def __set_name__(self, owner: type, name: str) -> None:
        self.key = self.path
        self.owner = owner.__name__
        self.field = name
        self._resolve_type(owner)
        register(
            CfgItem(
                key=self.key,
                owner=self.owner,
                module=owner.__module__,
                item=name,
                type=self.type,
                default=self._default_value,
                doc=self.doc or self._doc_of(owner),
                empty_ok=self.empty_ok,
                fillable=self.fillable,
            )
        )

    def _resolve_type(self, owner: type) -> None:
        """定下这条声明的类型，供词表（schema）使用。

        注解写成 ``Cfg[str]`` 最好（类型就是它）；写裸 ``Cfg`` 时，注解不带信息，
        就**按默认值推**（``4096`` → ``int``）——不猜、只推有把握的。
        """
        if self._resolved:
            return
        self._resolved = True
        hint: Any = self._item_type
        if hint is None:
            try:
                from typing import get_type_hints  # noqa: PLC0415 — 仅此处需要

                hint = get_type_hints(owner).get(self.field)
            except Exception:  # noqa: BLE001 — 注解解析失败不该挡住登记
                hint = None
        if not isinstance(hint, type) or hint is Cfg:
            hint = type(self._default_value) if self.fillable else None
        self.type = hint if isinstance(hint, type) else None

    @staticmethod
    def _doc_of(owner: type) -> str:
        """字段说明兜底：类体里那行注释取不到，退而用类 docstring 的首行。"""
        return (owner.__doc__ or "").strip().splitlines()[0] if owner.__doc__ else ""

    # ---- 取值：属性访问即向引擎要 ----
    def __get__(self, instance: object, owner: type | None = None) -> Any:
        from core.conf.engine import conf  # noqa: PLC0415 — 延迟导入，避免地基依赖引擎

        try:
            return conf.get(self.key)
        except Exception:  # noqa: BLE001 — 引擎缺失 / 读不到时退回家底，别让属性访问炸
            return self._default_value

    def __set__(self, instance: object, value: Any) -> None:
        """赋值 = 写进配置文件（不是写内存字段）——配置只有文件一个真源。"""
        from core.conf.engine import conf  # noqa: PLC0415

        conf.set(self.key, value)

    @property
    def default(self) -> Any:
        """声明里写的默认值（可能为 ``None``：没传值）。"""
        return self._default_value


__all__ = ["Cfg", "CfgItem", "clear", "item", "items", "register"]
