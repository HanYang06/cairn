"""FastCDC 内容定义分块。

同内容产生相同边界，插入/删除只影响局部，利于去重与增量传输。
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import fastcdc

MIN_SIZE = 16 * 1024
AVG_SIZE = 64 * 1024
MAX_SIZE = 256 * 1024


@dataclass(frozen=True, slots=True)
class Chunk:
    """一个内容定义块：在对象明文中的偏移与字节。"""

    offset: int
    data: bytes


def iter_chunks(
    data: bytes | bytearray | memoryview,
    *,
    min_size: int = MIN_SIZE,
    avg_size: int = AVG_SIZE,
    max_size: int = MAX_SIZE,
) -> Iterator[Chunk]:
    """把字节缓冲切分为内容定义块序列。"""
    view = memoryview(data)
    for piece in fastcdc.fastcdc(
        view,
        min_size=min_size,
        avg_size=avg_size,
        max_size=max_size,
    ):
        end = piece.offset + piece.length
        yield Chunk(offset=piece.offset, data=bytes(view[piece.offset:end]))
