from __future__ import annotations

from app.auth_security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    normalize_email,
    password_hash_needs_rehash,
    verify_password,
)
from app.models import Base


def test_normalize_email():
    assert (
        normalize_email("  Investor@Example.COM ")
        == "investor@example.com"
    )


def test_password_is_hashed_with_argon2id():
    password = "MotDePasse-Test-2026"

    encoded = hash_password(password)

    assert encoded != password
    assert encoded.startswith("$argon2id$")


def test_password_verification():
    password = "MotDePasse-Test-2026"
    encoded = hash_password(password)

    assert verify_password(
        password,
        encoded,
    )

    assert not verify_password(
        "mauvais-mot-de-passe",
        encoded,
    )


def test_password_hash_uses_random_salt():
    password = "MotDePasse-Test-2026"

    first = hash_password(password)
    second = hash_password(password)

    assert first != second


def test_session_tokens_are_random_and_hashed():
    first = generate_session_token()
    second = generate_session_token()

    assert first != second
    assert len(first) >= 40

    first_hash = hash_session_token(first)

    assert first_hash != first
    assert len(first_hash) == 64

    assert (
        hash_session_token(first)
        == first_hash
    )


def test_password_hash_configuration_is_current():
    encoded = hash_password(
        "MotDePasse-Test-2026"
    )

    assert not password_hash_needs_rehash(
        encoded
    )


def test_auth_tables_are_registered():
    tables = Base.metadata.tables

    assert "users" in tables
    assert "auth_sessions" in tables

    users = tables["users"]
    sessions = tables["auth_sessions"]

    assert "email" in users.c
    assert "password_hash" in users.c
    assert "google_sub" in users.c
    assert "auth_provider" in users.c

    assert "user_id" in sessions.c
    assert "token_hash" in sessions.c
    assert "expires_at" in sessions.c


def test_auth_session_foreign_key_targets_users():
    sessions = Base.metadata.tables[
        "auth_sessions"
    ]

    foreign_keys = {
        str(key.column)
        for key in sessions.foreign_keys
    }

    assert "users.id" in foreign_keys
