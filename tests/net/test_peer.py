from __future__ import annotations

import socket
import threading
from pathlib import Path
from typing import Any

from cairn.core import Vault
from cairn.core.types import Cid
from cairn.net import ChunkServer, PeerClient

PASSPHRASE = "correct horse battery staple"


def _start_server(source: Any) -> tuple[socket.socket, threading.Thread]:
    server = ChunkServer(source)
    client_sock, server_sock = socket.socketpair()

    def run() -> None:
        try:
            server.serve_connection(server_sock)
        finally:
            server_sock.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return client_sock, thread


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault", PASSPHRASE)


def test_fetch_chunks_roundtrip(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    vault.put(b"hello network " * 1000)
    cids = [str(cid) for cid in vault.pool.iter_chunk_cids()]
    assert cids

    client_sock, thread = _start_server(vault.pool)
    client = PeerClient(client_sock)
    received = client.fetch_chunks(cids)

    for cid in cids:
        assert received[cid] == vault.pool.read_chunk(cid)

    client_sock.close()
    thread.join(timeout=2)


def test_fetch_object_envelope(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    oid = vault.put(b"payload")

    client_sock, thread = _start_server(vault.pool)
    client = PeerClient(client_sock)
    envelope = client.fetch_object(oid)

    assert envelope == vault.pool.read_object(oid)

    client_sock.close()
    thread.join(timeout=2)


def test_missing_chunk_is_omitted(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    vault.put(b"x")

    client_sock, thread = _start_server(vault.pool)
    client = PeerClient(client_sock)
    received = client.fetch_chunks([Cid.from_digest(bytes(32))])

    assert received == {}

    client_sock.close()
    thread.join(timeout=2)
