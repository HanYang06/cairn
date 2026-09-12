# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import random

from cairn.core.storage.chunker import AVG_SIZE, MAX_SIZE, MIN_SIZE, iter_chunks


def _random_bytes(size: int, seed: int = 0) -> bytes:
    return random.Random(seed).randbytes(size)


def test_iter_chunks_reassembles_input() -> None:
    for size in (0, 1, MIN_SIZE - 1, MIN_SIZE, AVG_SIZE * 3 + 17, MAX_SIZE * 2 + 12345):
        data = _random_bytes(size, seed=size)
        chunks = list(iter_chunks(data))
        assert b"".join(c.data for c in chunks) == data


def test_iter_chunks_offsets_are_contiguous() -> None:
    data = _random_bytes(1_000_000, seed=7)
    chunks = list(iter_chunks(data))
    cursor = 0
    for chunk in chunks:
        assert chunk.offset == cursor
        cursor += len(chunk.data)
    assert cursor == len(data)


def test_iter_chunks_respects_bounds() -> None:
    data = _random_bytes(2_000_000, seed=11)
    chunks = list(iter_chunks(data))
    assert len(chunks) > 1
    for chunk in chunks[:-1]:
        assert MIN_SIZE <= len(chunk.data) <= MAX_SIZE
    assert 0 < len(chunks[-1].data) <= MAX_SIZE


def test_iter_chunks_small_input_is_single_chunk() -> None:
    data = b"tiny"
    chunks = list(iter_chunks(data))
    assert len(chunks) == 1
    assert chunks[0].offset == 0
    assert chunks[0].data == data


def test_chunk_boundaries_are_stable_under_insertion() -> None:
    min_size, avg_size, max_size = 2048, 4096, 16384
    cut = 300_000
    base = _random_bytes(1_000_000, seed=3)
    modified = base[:cut] + b"INSERTED" + base[cut:]

    def prefix(data: bytes) -> bytes:
        out = bytearray()
        for chunk in iter_chunks(
            data, min_size=min_size, avg_size=avg_size, max_size=max_size
        ):
            if chunk.offset + len(chunk.data) > cut:
                break
            out += chunk.data
        return bytes(out)

    stable = prefix(base)
    assert stable  # 至少有一个完整块落在插入点之前
    assert prefix(modified) == stable
