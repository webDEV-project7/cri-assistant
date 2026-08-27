from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.auth_routes import (
    SESSION_COOKIE_NAME,
    router as auth_router,
)
from app.auth_security import (
    hash_session_token,
)
from app.database import (
    get_database_session,
)
from app.models import (
    AuthSession,
    Base,
    User,
)


@pytest.fixture
def auth_environment():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(
        bind=engine
    )

    app = FastAPI()
    app.include_router(auth_router)

    def override_database():
        session = TestingSessionLocal()

        try:
            yield session

        finally:
            session.close()

    app.dependency_overrides[
        get_database_session
    ] = override_database

    with TestClient(app) as client:
        yield client, TestingSessionLocal


def register_user(
    client: TestClient,
    email: str = "investisseur@example.com",
):
    return client.post(
        "/auth/register",
        json={
            "name": "Investisseur Test",
            "email": email,
            "password": "MotDePasse2026!",
        },
    )


def test_register_creates_account_and_cookie(
    auth_environment,
):
    client, _ = auth_environment

    response = register_user(client)

    assert response.status_code == 201

    data = response.json()

    assert (
        data["email"]
        == "investisseur@example.com"
    )

    assert (
        data["auth_provider"]
        == "local"
    )

    assert "password" not in data
    assert "password_hash" not in data

    assert (
        client.cookies.get(
            SESSION_COOKIE_NAME
        )
        is not None
    )


def test_registered_password_is_not_plain_text(
    auth_environment,
):
    client, SessionLocal = (
        auth_environment
    )

    register_user(client)

    with SessionLocal() as session:
        user = session.scalar(
            select(User).where(
                User.email
                == "investisseur@example.com"
            )
        )

        assert user is not None

        assert (
            user.password_hash
            != "MotDePasse2026!"
        )

        assert user.password_hash.startswith(
            "$argon2id$"
        )


def test_duplicate_email_is_rejected(
    auth_environment,
):
    client, _ = auth_environment

    first = register_user(client)
    second = register_user(client)

    assert first.status_code == 201
    assert second.status_code == 409


def test_email_is_normalized(
    auth_environment,
):
    client, _ = auth_environment

    response = client.post(
        "/auth/register",
        json={
            "name": "Test",
            "email": (
                "  USER@EXAMPLE.COM  "
            ),
            "password": "MotDePasse2026!",
        },
    )

    assert response.status_code == 201

    assert (
        response.json()["email"]
        == "user@example.com"
    )


def test_me_requires_authentication(
    auth_environment,
):
    client, _ = auth_environment

    response = client.get(
        "/auth/me"
    )

    assert response.status_code == 401


def test_me_returns_logged_user(
    auth_environment,
):
    client, _ = auth_environment

    register_user(client)

    response = client.get(
        "/auth/me"
    )

    assert response.status_code == 200

    assert (
        response.json()["email"]
        == "investisseur@example.com"
    )


def test_logout_revokes_session(
    auth_environment,
):
    client, _ = auth_environment

    register_user(client)

    logout_response = client.post(
        "/auth/logout"
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {
        "ok": True
    }

    me_response = client.get(
        "/auth/me"
    )

    assert me_response.status_code == 401


def test_login_with_correct_password(
    auth_environment,
):
    client, _ = auth_environment

    register_user(client)

    client.post(
        "/auth/logout"
    )

    response = client.post(
        "/auth/login",
        json={
            "email": (
                "INVESTISSEUR@EXAMPLE.COM"
            ),
            "password": "MotDePasse2026!",
        },
    )

    assert response.status_code == 200

    assert (
        client.cookies.get(
            SESSION_COOKIE_NAME
        )
        is not None
    )


def test_login_with_wrong_password_is_rejected(
    auth_environment,
):
    client, _ = auth_environment

    register_user(client)

    client.post(
        "/auth/logout"
    )

    response = client.post(
        "/auth/login",
        json={
            "email": (
                "investisseur@example.com"
            ),
            "password": "MauvaisPassword",
        },
    )

    assert response.status_code == 401


def test_session_token_is_not_stored_plain_text(
    auth_environment,
):
    client, SessionLocal = (
        auth_environment
    )

    register_user(client)

    raw_token = client.cookies.get(
        SESSION_COOKIE_NAME
    )

    assert raw_token is not None

    with SessionLocal() as session:
        auth_session = session.scalar(
            select(AuthSession)
        )

        assert auth_session is not None

        assert (
            auth_session.token_hash
            != raw_token
        )

        assert (
            auth_session.token_hash
            == hash_session_token(
                raw_token
            )
        )


def test_expired_session_is_rejected(
    auth_environment,
):
    client, SessionLocal = (
        auth_environment
    )

    register_user(client)

    with SessionLocal() as session:
        auth_session = session.scalar(
            select(AuthSession)
        )

        assert auth_session is not None

        auth_session.expires_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=1)
        )

        session.commit()

    response = client.get(
        "/auth/me"
    )

    assert response.status_code == 401


def test_inactive_user_is_rejected(
    auth_environment,
):
    client, SessionLocal = (
        auth_environment
    )

    register_user(client)

    with SessionLocal() as session:
        user = session.scalar(
            select(User)
        )

        assert user is not None

        user.is_active = False
        session.commit()

    response = client.get(
        "/auth/me"
    )

    assert response.status_code == 403


def test_invalid_email_is_rejected(
    auth_environment,
):
    client, _ = auth_environment

    response = client.post(
        "/auth/register",
        json={
            "name": "Investisseur",
            "email": "adresse-invalide",
            "password": "MotDePasse2026!",
        },
    )

    assert response.status_code == 422


def test_short_password_is_rejected(
    auth_environment,
):
    client, _ = auth_environment

    response = client.post(
        "/auth/register",
        json={
            "name": "Investisseur",
            "email": "user@example.com",
            "password": "123",
        },
    )

    assert response.status_code == 422
