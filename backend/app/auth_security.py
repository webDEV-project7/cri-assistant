from __future__ import annotations

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
from argon2.low_level import Type


SESSION_TOKEN_BYTES = 32

_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    if not password:
        raise ValueError(
            "Le mot de passe ne peut pas être vide."
        )

    return _password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    if not password or not password_hash:
        return False

    try:
        return _password_hasher.verify(
            password_hash,
            password,
        )

    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError,
    ):
        return False


def password_hash_needs_rehash(
    password_hash: str,
) -> bool:
    if not password_hash:
        return True

    try:
        return _password_hasher.check_needs_rehash(
            password_hash
        )

    except InvalidHashError:
        return True


def generate_session_token() -> str:
    return secrets.token_urlsafe(
        SESSION_TOKEN_BYTES
    )


def hash_session_token(
    token: str,
) -> str:
    if not token:
        raise ValueError(
            "Le token de session ne peut pas être vide."
        )

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()
