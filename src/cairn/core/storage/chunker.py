# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""FastCDC 内容定义分块。

同内容产生相同边界，插入/删除只影响局部，利于去重与增量传输。
支持字节缓冲与文件路径（后者经 mmap，避免大文件整块进内存）。
"""

from __future__ import annotations

import mmap
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import fastcdc

MIN_SIZE = 16 * 1024
AVG_SIZE = 64 * 1024
MAX_SIZE = 256 * 1024

Source = bytes | bytearray | memoryview | str | Path


@dataclass(frozen=True, slots=True)
class Chunk:
    """一个内容定义块：在对象明文中的偏移与字节。"""

    offset: int
    data: bytes


def _chunk_view(
    view: memoryview,
    min_size: int,
    avg_size: int,
    max_size: int,
) -> Iterator[Chunk]:
    if not view:
        return
    for piece in fastcdc.fastcdc(
        view,
        min_size=min_size,
        avg_size=avg_size,
        max_size=max_size,
    ):
        end = piece.offset + piece.length
        yield Chunk(offset=piece.offset, data=bytes(view[piece.offset:end]))


def _chunk_path(
    path: Path,
    min_size: int,
    avg_size: int,
    max_size: int,
) -> Iterator[Chunk]:
    if not path.stat().st_size:
        return
    with (
        path.open("rb") as handle,
        mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as mapped,
        memoryview(mapped) as view,
    ):
        yield from _chunk_view(view, min_size, avg_size, max_size)


def iter_chunks(
    data: Source,
    *,
    min_size: int = MIN_SIZE,
    avg_size: int = AVG_SIZE,
    max_size: int = MAX_SIZE,
) -> Iterator[Chunk]:
    """把字节缓冲或文件切分为内容定义块序列。"""
    if isinstance(data, (str, Path)):
        yield from _chunk_path(Path(data), min_size, avg_size, max_size)
    else:
        yield from _chunk_view(memoryview(data), min_size, avg_size, max_size)
