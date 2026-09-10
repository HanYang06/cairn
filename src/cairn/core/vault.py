"""Vault：Core 的唯一公共入口。

对外只暴露一个门面与一套极简动词：create/load/unlock/lock、
put/open/info/delete/iter、space/create_space。所有内容都是对象。
"""

from __future__ import annotations

import base64
import io
import secrets
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

import tomli_w

from .chunker import iter_chunks
from .codec import (
    FORMAT_VERSION,
    chunk_aad,
    decode_cbor,
    encode_cbor,
    manifest_aad,
    pack_record,
    unpack_record,
)
from .crypto import (
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
    KEY_LEN,
    SALT_LEN,
    Identity,
    derive_kek,
    derive_subkey,
    keyed_hash,
    new_master_key,
    seal,
    unseal,
)
from .manifest import Manifest, sign_manifest, verify_manifest
from .pool import Pool, atomic_write, prune_empty_dirs
from .types import (
    AuthError,
    ChunkRef,
    Cid,
    CorruptObjectError,
    ObjectInfo,
    ObjectNotFoundError,
    Oid,
    Space,
    SpaceId,
    SpaceNotFoundError,
    VaultError,
    VaultLockedError,
    Visibility,
    now_ms,
)

_TOML_NAME = "cairn.toml"
_CTX_VAULT_META = "cairn/v1/vault/meta"
_DEFAULT_SPACE = "default"


def _space_contexts(space_id: SpaceId) -> tuple[str, str, str]:
    base = f"cairn/v1/space/{space_id}"
    return (
        f"{base}/chunk-address",
        f"{base}/chunk-data",
        f"{base}/manifest-data",
    )


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


@dataclass(frozen=True, slots=True)
class _SpaceKeys:
    space: Space
    secret: bytes
    addr_key: bytes
    data_key: bytes
    meta_key: bytes

    @classmethod
    def from_secret(cls, space: Space, secret: bytes) -> _SpaceKeys:
        addr_ctx, data_ctx, meta_ctx = _space_contexts(space.space_id)
        return cls(
            space=space,
            secret=secret,
            addr_key=derive_subkey(secret, addr_ctx),
            data_key=derive_subkey(secret, data_ctx),
            meta_key=derive_subkey(secret, meta_ctx),
        )


class _ObjectReader(io.RawIOBase):
    """按需解密块的只读流。"""

    def __init__(self, refs: list[ChunkRef], fetch: Any) -> None:
        self._refs = refs
        self._fetch = fetch
        self._index = 0
        self._buffer = b""
        self._offset = 0

    def readable(self) -> bool:
        return True

    def readinto(self, target: Any) -> int:
        while self._offset >= len(self._buffer):
            if self._index >= len(self._refs):
                return 0
            self._buffer = self._fetch(self._refs[self._index])
            self._index += 1
            self._offset = 0
        count = min(len(target), len(self._buffer) - self._offset)
        target[:count] = self._buffer[self._offset : self._offset + count]
        self._offset += count
        return count


def _read_all(src: bytes | bytearray | memoryview | BinaryIO) -> bytes:
    if isinstance(src, (bytes, bytearray, memoryview)):
        return bytes(src)
    return src.read()


def _envelope(space_id: SpaceId, sealed_manifest: bytes) -> bytes:
    return pack_record(
        encode_cbor(
            {
                "v": FORMAT_VERSION,
                "space_id": str(space_id),
                "manifest": sealed_manifest,
            }
        )
    )


def _open_envelope(blob: bytes) -> tuple[SpaceId, bytes]:
    raw = decode_cbor(unpack_record(blob))
    try:
        return SpaceId.parse(raw["space_id"]), raw["manifest"]
    except (KeyError, TypeError, ValueError) as exc:
        raise CorruptObjectError("对象信封解析失败") from exc


class Vault:
    """本地加密对象池的门面。"""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.pool = Pool(self.root / "pool")
        self._header: dict[str, Any] = {}
        self._master_key: bytes | None = None
        self._vault_key: bytes | None = None
        self._identity: Identity | None = None
        self._spaces: dict[str, _SpaceKeys] = {}
        self._by_id: dict[SpaceId, _SpaceKeys] = {}

    @classmethod
    def create(cls, path: Path | str, passphrase: str) -> Vault:
        root = Path(path)
        toml_path = root / _TOML_NAME
        if toml_path.exists():
            raise VaultError(f"库已存在: {root}")
        root.mkdir(parents=True, exist_ok=True)
        vault = cls(root)
        vault.pool.ensure()

        master = new_master_key()
        salt = secrets.token_bytes(SALT_LEN)
        kek = derive_kek(passphrase, salt)
        vault_key = derive_subkey(master, _CTX_VAULT_META)
        identity = Identity.generate()

        header = {
            "format_version": FORMAT_VERSION,
            "vault_id": str(Oid.new()),
            "created": now_ms(),
            "kdf": {
                "algo": "argon2id",
                "salt": _b64(salt),
                "time_cost": ARGON2_TIME_COST,
                "memory_cost": ARGON2_MEMORY_COST,
                "parallelism": ARGON2_PARALLELISM,
            },
            "wrap": {"algo": "chacha20poly1305", "blob": _b64(seal(kek, master))},
            "identity": {
                "sign": _b64(seal(vault_key, identity.sign_seed)),
                "kex": _b64(seal(vault_key, identity.kex_seed)),
            },
        }

        vault._header = header
        vault._master_key = master
        vault._vault_key = vault_key
        vault._identity = identity
        vault._create_space(_DEFAULT_SPACE, Visibility.PRIVATE)
        atomic_write(toml_path, tomli_w.dumps(header).encode("utf-8"))
        return vault

    @classmethod
    def load(cls, path: Path | str) -> Vault:
        root = Path(path)
        toml_path = root / _TOML_NAME
        if not toml_path.is_file():
            raise VaultError(f"不是有效的 Cairn 库: {root}")
        vault = cls(root)
        with toml_path.open("rb") as handle:
            vault._header = tomllib.load(handle)
        if vault._header.get("format_version") != FORMAT_VERSION:
            raise VaultError("库格式版本不受支持")
        return vault

    def unlock(self, passphrase: str) -> None:
        if not self._header:
            raise VaultError("库未加载")
        kdf = self._header["kdf"]
        kek = derive_kek(
            passphrase,
            _unb64(kdf["salt"]),
            time_cost=kdf["time_cost"],
            memory_cost=kdf["memory_cost"],
            parallelism=kdf["parallelism"],
        )
        master = unseal(kek, _unb64(self._header["wrap"]["blob"]))
        vault_key = derive_subkey(master, _CTX_VAULT_META)
        identity = self._header["identity"]
        self._master_key = master
        self._vault_key = vault_key
        self._identity = Identity(
            sign_seed=unseal(vault_key, _unb64(identity["sign"])),
            kex_seed=unseal(vault_key, _unb64(identity["kex"])),
        )
        self._load_spaces()

    def lock(self) -> None:
        self._master_key = None
        self._vault_key = None
        self._identity = None
        self._spaces.clear()
        self._by_id.clear()

    @property
    def is_locked(self) -> bool:
        return self._master_key is None

    def spaces(self) -> list[Space]:
        return [keys.space for keys in self._spaces.values()]

    def space(self, name: str = _DEFAULT_SPACE) -> Space:
        return self._keys(name).space

    def create_space(self, name: str, visibility: Visibility = Visibility.PRIVATE) -> Space:
        self._require_unlocked()
        if name in self._spaces:
            raise VaultError(f"空间已存在: {name}")
        return self._create_space(name, visibility).space

    def put(
        self,
        src: bytes | bytearray | memoryview | BinaryIO,
        *,
        space: str = _DEFAULT_SPACE,
        type: str = "blob",
        mime: str | None = None,
        meta: dict[str, Any] | None = None,
        oid: Oid | str | None = None,
    ) -> Oid:
        self._require_unlocked()
        keys = self._keys(space)
        data = _read_all(src)
        new_oid = Oid.parse(str(oid)) if oid is not None else Oid.new()

        refs: list[ChunkRef] = []
        for chunk in iter_chunks(data):
            cid = Cid.from_digest(keyed_hash(keys.addr_key, chunk.data))
            if not self.pool.has_chunk(cid):
                sealed = seal(keys.data_key, chunk.data, chunk_aad())
                self.pool.write_chunk(cid, pack_record(sealed))
            refs.append(ChunkRef(cid=cid, size=len(chunk.data)))

        timestamp = now_ms()
        manifest = Manifest(
            oid=new_oid,
            space_id=keys.space.space_id,
            type=type,
            mime=mime,
            size=len(data),
            created=timestamp,
            updated=timestamp,
            chunks=tuple(refs),
            meta=dict(meta or {}),
            seq=1,
            prev=None,
            author=b"",
            sig=b"",
        )
        if self._identity is None:
            raise VaultLockedError("库已锁定")
        signed = sign_manifest(manifest, self._identity)
        sealed_manifest = seal(keys.meta_key, signed.to_cbor(), manifest_aad(new_oid))
        self.pool.write_object(new_oid, _envelope(keys.space.space_id, sealed_manifest))
        return new_oid

    def open(self, oid: Oid | str) -> io.RawIOBase:
        self._require_unlocked()
        target = Oid.parse(str(oid))
        keys, manifest = self._load_manifest(target)
        return _ObjectReader(list(manifest.chunks), lambda ref: self._fetch(keys, ref))

    def info(self, oid: Oid | str) -> ObjectInfo:
        self._require_unlocked()
        target = Oid.parse(str(oid))
        _, manifest = self._load_manifest(target)
        return _manifest_info(manifest)

    def delete(self, oid: Oid | str) -> None:
        self._require_unlocked()
        target = Oid.parse(str(oid))
        self.pool.delete_object(target)

    def iter(
        self,
        *,
        space: str | None = None,
        type: str | None = None,
    ) -> Any:
        self._require_unlocked()
        wanted = self._keys(space).space.space_id if space is not None else None
        for oid in self.pool.iter_object_ids():
            _, manifest = self._load_manifest(oid)
            if wanted is not None and manifest.space_id != wanted:
                continue
            if type is not None and manifest.type != type:
                continue
            yield _manifest_info(manifest)

    def iter_manifests(self) -> Iterator[Manifest]:
        self._require_unlocked()
        for oid in self.pool.iter_object_ids():
            _, manifest = self._load_manifest(oid)
            yield manifest

    def rebuild_index(self) -> int:
        self._require_unlocked()
        from .index import Index

        index = Index(self.root / ".cairn" / "index.sqlite")
        try:
            return index.rebuild(self)
        finally:
            index.close()

    def gc(self) -> int:
        self._require_unlocked()
        live = {str(ref.cid) for manifest in self.iter_manifests() for ref in manifest.chunks}
        removed = 0
        for cid in list(self.pool.iter_chunk_cids()):
            if str(cid) not in live:
                self.pool.delete_chunk(cid)
                removed += 1
        prune_empty_dirs(self.pool.chunks_dir)
        return removed

    def _create_space(self, name: str, visibility: Visibility) -> _SpaceKeys:
        assert self._vault_key is not None
        space_id = SpaceId.new()
        secret = secrets.token_bytes(KEY_LEN)
        created = now_ms()
        record = {
            "v": FORMAT_VERSION,
            "space_id": str(space_id),
            "name": name,
            "visibility": visibility.value,
            "created": created,
            "key_epoch": 1,
            "secret": secret,
        }
        blob = pack_record(seal(self._vault_key, encode_cbor(record)))
        atomic_write(self.pool.spaces_dir / str(space_id), blob)
        keys = _SpaceKeys.from_secret(
            Space(space_id=space_id, name=name, visibility=visibility, created=created),
            secret,
        )
        self._spaces[name] = keys
        self._by_id[space_id] = keys
        return keys

    def _load_spaces(self) -> None:
        assert self._vault_key is not None
        self._spaces.clear()
        self._by_id.clear()
        if not self.pool.spaces_dir.exists():
            return
        for entry in self.pool.spaces_dir.iterdir():
            if not entry.is_file() or entry.name.startswith(".tmp-"):
                continue
            record = decode_cbor(unseal(self._vault_key, unpack_record(entry.read_bytes())))
            space = Space(
                space_id=SpaceId.parse(record["space_id"]),
                name=record["name"],
                visibility=Visibility(record["visibility"]),
                created=record["created"],
            )
            keys = _SpaceKeys.from_secret(space, record["secret"])
            self._spaces[space.name] = keys
            self._by_id[space.space_id] = keys

    def _keys(self, name: str) -> _SpaceKeys:
        self._require_unlocked()
        try:
            return self._spaces[name]
        except KeyError as exc:
            raise SpaceNotFoundError(name) from exc

    def _keys_by_id(self, space_id: SpaceId) -> _SpaceKeys:
        try:
            return self._by_id[space_id]
        except KeyError as exc:
            raise SpaceNotFoundError(str(space_id)) from exc

    def _load_manifest(self, oid: Oid) -> tuple[_SpaceKeys, Manifest]:
        try:
            blob = self.pool.read_object(oid)
        except FileNotFoundError as exc:
            raise ObjectNotFoundError(str(oid)) from exc
        space_id, sealed = _open_envelope(blob)
        keys = self._keys_by_id(space_id)
        manifest = Manifest.from_cbor(unseal(keys.meta_key, sealed, manifest_aad(oid)))
        if not verify_manifest(manifest):
            raise CorruptObjectError(f"manifest 签名无效: {oid}")
        return keys, manifest

    def _fetch(self, keys: _SpaceKeys, ref: ChunkRef) -> bytes:
        try:
            blob = self.pool.read_chunk(ref.cid)
        except FileNotFoundError as exc:
            raise CorruptObjectError(f"块缺失: {ref.cid}") from exc
        data = unseal(keys.data_key, unpack_record(blob), chunk_aad())
        if Cid.from_digest(keyed_hash(keys.addr_key, data)) != ref.cid:
            raise CorruptObjectError(f"块校验失败: {ref.cid}")
        return data

    def _require_unlocked(self) -> None:
        if self._master_key is None:
            raise VaultLockedError("库已锁定")


def _manifest_info(manifest: Manifest) -> ObjectInfo:
    meta = manifest.meta or {}
    tags = meta.get("tags") or ()
    return ObjectInfo(
        oid=manifest.oid,
        space_id=manifest.space_id,
        type=manifest.type,
        mime=manifest.mime,
        size=manifest.size,
        created=manifest.created,
        updated=manifest.updated,
        title=meta.get("title"),
        tags=tuple(tags),
    )


__all__ = ["AuthError", "Vault", "VaultError", "Visibility"]
