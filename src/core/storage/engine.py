# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""存储侧的**引擎角色**：对象进 / 出 / 删（表一里的固定件）。

内核的 `Core.put/get/drop` 组出事件包，引擎按 ``role_name="storage"`` 找到它，
调用这里的 :meth:`Storage.store` / :meth:`Storage.fetch` / :meth:`Storage.drop`。

存储本身（桶 / 块 / 目录）仍在 `core.storage`；这一层只是**给引擎一个可调用的面**，
并且**不认识领域语义**（不知道什么是笔记、什么是项目）。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from core.storage import Block, Bucket

if TYPE_CHECKING:
    from collections.abc import Iterator


class Storage:
    """表一成员：引擎调用它完成对象进 / 出 / 删。"""

    name = "storage"

    def __init__(self, root: Path | str, bucket: Bucket) -> None:
        self.id = "storage"
        self.root = Path(root)
        self._bucket = bucket

    # ---- 生命周期 ----
    @classmethod
    def create(cls, path: Path | str) -> Storage:
        """建新库。"""
        return cls(path, Bucket.create(Path(path)))

    @classmethod
    def open(cls, path: Path | str) -> Storage:
        """开库（不存在则建）。"""
        root = Path(path)
        if (root / "catalog.db").is_file():
            return cls(root, Bucket.open(root))
        return cls.create(root)

    def close(self) -> None:
        """关闭底层桶。"""
        self._bucket.close()

    # ---- 引擎调用的动作面 ----
    def store(self, obj: Block) -> Block:
        """**存**一个对象（写 块行 + 内容池）。"""
        self._bucket.put(obj)
        self._bucket.commit()
        return obj

    def get[T: Block](self, cls: type[T], oid: str) -> T:
        """**取**一个对象（按类型还原）——与旧调用点对齐的入口。"""
        return cast("T", self._bucket.get(cls, str(oid)))

    def fetch(self, oid: str) -> Block:
        """**取**一个对象（未知类型时按基类还原）。"""
        return self._bucket.get(Block, str(oid))

    def drop(self, oid: str) -> bool:
        """**删**一个对象；返回它此前是否存在。"""
        removed = self._bucket.delete(str(oid))
        if removed:
            self._bucket.commit()
        return removed

    # ---- 库级视图 ----
    def commit(self) -> None:
        """提交当前事务。"""
        self._bucket.commit()

    def ids(self) -> Iterator[str]:
        """遍历全部对象 id。"""
        return self._bucket.iter_block_ids()

    def table(self, name: str, **columns: str) -> Any:
        """挂载 / 取一张通用表（关系等）。"""
        return self._bucket.table(name, **columns)

    def info_of(self, oid: str) -> Any:
        """取对象的中立视图（类型 / 标题 / 标签 / 时间）。"""
        from core.storage.block import Block as _Block  # noqa: PLC0415
        from core.types.kind import type_name as _type_name  # noqa: PLC0415
        from core.types.objects import ObjectInfo  # noqa: PLC0415 — 避免加载期互引

        block = self._bucket.get(_Block, str(oid))
        attrs = block.attrs
        return ObjectInfo(
            oid=block.oid,
            type=_type_name(block.type),
            mime=attrs.get("mime"),
            size=block.size,
            created=block.created,
            updated=block.updated,
            title=attrs.get("title"),
            tags=_tags_of(attrs.get("tags")),
            seq=1,
            author=str(attrs.get("author") or ""),
        )

    def query(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> list[Any]:
        """只读查询。"""
        return self._bucket.query(sql, params)

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> int:
        """写语句。"""
        return self._bucket.execute(sql, params)

    @property
    def catalog(self) -> Any:
        """目录（库级事实）。"""
        return self._bucket.catalog

    def __repr__(self) -> str:
        return f"Storage({self.root})"


__all__ = ["Storage"]


def _tags_of(raw: Any) -> dict[str, Any]:
    """标签归一：映射原样（键转字符串）、裸字符串算单标签、序列算一组按键存在。"""
    if not raw:
        return {}
    if isinstance(raw, dict):
        return {str(key): value for key, value in raw.items()}
    if isinstance(raw, str):
        return {raw: None}
    return {str(tag): None for tag in raw}
