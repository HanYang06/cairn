# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""核心密码学原语：密钥派生、AEAD、身份。

依赖 ``cryptography`` / ``blake3`` / ``argon2-cffi``。
AEAD 采用 ChaCha20-Poly1305（12 字节随机 nonce）；XChaCha20 待运行库支持后再切换。
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from argon2.low_level import Type, hash_secret_raw
from blake3 import blake3
from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .types import AuthError

KEY_LEN = 32
NONCE_LEN = 12
TAG_LEN = 16
SALT_LEN = 16

ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 64 * 1024
ARGON2_PARALLELISM = 4

_HKDF_SALT = b"cairn/v1/kex"


def random_bytes(length: int) -> bytes:
    return secrets.token_bytes(length)


def new_master_key() -> bytes:
    return secrets.token_bytes(KEY_LEN)


def derive_kek(
    passphrase: str,
    salt: bytes,
    *,
    time_cost: int = ARGON2_TIME_COST,
    memory_cost: int = ARGON2_MEMORY_COST,
    parallelism: int = ARGON2_PARALLELISM,
) -> bytes:
    """由口令经 Argon2id 派生 32 字节 KEK。"""
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=KEY_LEN,
        type=Type.ID,
    )


def derive_subkey(master: bytes, context: str) -> bytes:
    """用 BLAKE3 derive_key 从主密钥派生带域分隔的子密钥。"""
    return blake3(master, derive_key_context=context).digest()


def keyed_hash(key: bytes, data: bytes) -> bytes:
    """带密钥的 BLAKE3，用作内容标识（CID）。"""
    return blake3(data, key=key).digest()


def seal(key: bytes, plaintext: bytes, aad: bytes | None = None) -> bytes:
    """加密并前置随机 nonce，返回 ``nonce || ciphertext||tag``。"""
    nonce = secrets.token_bytes(NONCE_LEN)
    ciphertext = ChaCha20Poly1305(key).encrypt(nonce, plaintext, aad)
    return nonce + ciphertext


def unseal(key: bytes, blob: bytes, aad: bytes | None = None) -> bytes:
    """还原 ``seal`` 的输出；认证失败抛 ``AuthError``。"""
    if len(blob) < NONCE_LEN + TAG_LEN:
        raise AuthError("密文长度不足")
    nonce, ciphertext = blob[:NONCE_LEN], blob[NONCE_LEN:]
    try:
        return ChaCha20Poly1305(key).decrypt(nonce, ciphertext, aad)
    except InvalidTag as exc:
        raise AuthError("认证失败") from exc


@dataclass(frozen=True, slots=True)
class Identity:
    """库身份：Ed25519 签名 + X25519 密钥协商。"""

    sign_seed: bytes
    kex_seed: bytes

    @classmethod
    def generate(cls) -> Identity:
        return cls(secrets.token_bytes(32), secrets.token_bytes(32))

    @property
    def sign_public(self) -> bytes:
        return Ed25519PrivateKey.from_private_bytes(self.sign_seed).public_key().public_bytes_raw()

    @property
    def kex_public(self) -> bytes:
        return X25519PrivateKey.from_private_bytes(self.kex_seed).public_key().public_bytes_raw()

    def sign(self, message: bytes) -> bytes:
        return Ed25519PrivateKey.from_private_bytes(self.sign_seed).sign(message)


def verify_signature(public: bytes, signature: bytes, message: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(public).verify(signature, message)
    except (InvalidSignature, ValueError):
        return False
    return True


def _shared_kek(shared: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=_HKDF_SALT,
        info=b"keywrap",
    ).derive(shared)


def wrap_to_recipient(
    recipient_kex_public: bytes,
    key: bytes,
    aad: bytes | None = None,
) -> bytes:
    """ECIES 式封装：临时 X25519 协商出密钥，加密 ``key``。"""
    ephemeral = X25519PrivateKey.generate()
    shared = ephemeral.exchange(X25519PublicKey.from_public_bytes(recipient_kex_public))
    kek = _shared_kek(shared)
    ephemeral_public = ephemeral.public_key().public_bytes_raw()
    return ephemeral_public + seal(kek, key, aad)


def unwrap_from_sender(
    recipient_kex_seed: bytes,
    blob: bytes,
    aad: bytes | None = None,
) -> bytes:
    if len(blob) < 32 + NONCE_LEN + TAG_LEN:
        raise AuthError("封装数据长度不足")
    ephemeral_public, boxed = blob[:32], blob[32:]
    shared = X25519PrivateKey.from_private_bytes(recipient_kex_seed).exchange(
        X25519PublicKey.from_public_bytes(ephemeral_public)
    )
    kek = _shared_kek(shared)
    return unseal(kek, boxed, aad)
