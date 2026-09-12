# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import blake3
import pytest

from cairn.core.crypto import (
    Identity,
    derive_kek,
    derive_subkey,
    keyed_hash,
    new_master_key,
    seal,
    unseal,
    unwrap_from_sender,
    verify_signature,
    wrap_to_recipient,
)
from cairn.core.types import AuthError


def _fast_kek(passphrase: str, salt: bytes) -> bytes:
    return derive_kek(passphrase, salt, time_cost=1, memory_cost=8 * 1024, parallelism=1)


def test_derive_kek_deterministic_and_salt_dependent() -> None:
    salt = b"0123456789abcdef"
    assert _fast_kek("pw", salt) == _fast_kek("pw", salt)
    assert _fast_kek("pw", salt) != _fast_kek("pw", b"fedcba9876543210")
    assert _fast_kek("pw", salt) != _fast_kek("other", salt)
    assert len(_fast_kek("pw", salt)) == 32


def test_derive_subkey_domain_separated() -> None:
    master = new_master_key()
    a = derive_subkey(master, "cairn/v1/a")
    b = derive_subkey(master, "cairn/v1/b")
    assert a == derive_subkey(master, "cairn/v1/a")
    assert a != b
    assert len(a) == 32


def test_keyed_hash_matches_blake3_and_is_key_dependent() -> None:
    key = new_master_key()
    data = b"hello cairn"
    assert keyed_hash(key, data) == blake3.blake3(data, key=key).digest()
    assert keyed_hash(key, data) != keyed_hash(new_master_key(), data)


def test_seal_unseal_roundtrip() -> None:
    key = new_master_key()
    assert unseal(key, seal(key, b"payload")) == b"payload"
    assert unseal(key, seal(key, b"payload", aad=b"ctx"), aad=b"ctx") == b"payload"


def test_unseal_rejects_wrong_aad_tamper_and_short() -> None:
    key = new_master_key()
    blob = seal(key, b"payload", aad=b"ctx")
    with pytest.raises(AuthError):
        unseal(key, blob, aad=b"other")
    with pytest.raises(AuthError):
        unseal(new_master_key(), blob, aad=b"ctx")
    with pytest.raises(AuthError):
        unseal(key, blob[:-1], aad=b"ctx")
    with pytest.raises(AuthError):
        unseal(key, b"short")


def test_identity_sign_and_verify() -> None:
    identity = Identity.generate()
    message = b"manifest-bytes"
    signature = identity.sign(message)
    assert verify_signature(identity.sign_public, signature, message)
    assert not verify_signature(identity.sign_public, signature, b"other")
    assert not verify_signature(Identity.generate().sign_public, signature, message)


def test_wrap_unwrap_to_recipient() -> None:
    sender = Identity.generate()
    recipient = Identity.generate()
    key = new_master_key()
    blob = wrap_to_recipient(recipient.kex_public, key, aad=b"space")
    assert unwrap_from_sender(recipient.kex_seed, blob, aad=b"space") == key
    with pytest.raises(AuthError):
        unwrap_from_sender(Identity.generate().kex_seed, blob, aad=b"space")
    with pytest.raises(AuthError):
        unwrap_from_sender(recipient.kex_seed, blob, aad=b"other")
    assert sender.kex_public  # sender identity is well-formed


def test_wrap_produces_distinct_ephemeral_output() -> None:
    recipient = Identity.generate()
    key = new_master_key()
    assert wrap_to_recipient(recipient.kex_public, key) != wrap_to_recipient(
        recipient.kex_public, key
    )
