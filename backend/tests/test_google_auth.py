from __future__ import annotations

import pytest
from fastapi import HTTPException

from app import auth_routes


CLIENT_ID = (
    "123456789-test"
    ".apps.googleusercontent.com"
)


def google_claims():
    return {
        "iss": "https://accounts.google.com",
        "sub": "google-user-123",
        "email": "google.user@example.com",
        "email_verified": True,
        "name": "Google User",
    }


def test_google_routes_exist():
    paths = {
        getattr(route, "path", None)
        for route in auth_routes.router.routes
    }

    assert "/auth/google" in paths
    assert "/auth/google-config" in paths


def test_valid_google_token(
    monkeypatch,
):
    monkeypatch.setattr(
        auth_routes,
        "GOOGLE_CLIENT_ID",
        CLIENT_ID,
    )

    monkeypatch.setattr(
        auth_routes.google_id_token,
        "verify_oauth2_token",
        lambda credential, request, audience:
            google_claims(),
    )

    result = (
        auth_routes.verify_google_credential(
            "fake-valid-google-token"
        )
    )

    assert result["sub"] == "google-user-123"


def test_invalid_google_token(
    monkeypatch,
):
    monkeypatch.setattr(
        auth_routes,
        "GOOGLE_CLIENT_ID",
        CLIENT_ID,
    )

    def reject(
        credential,
        request,
        audience,
    ):
        raise ValueError(
            "invalid token"
        )

    monkeypatch.setattr(
        auth_routes.google_id_token,
        "verify_oauth2_token",
        reject,
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        auth_routes.verify_google_credential(
            "invalid-google-token"
        )

    assert (
        exc_info.value.status_code
        == 401
    )


def test_invalid_google_issuer(
    monkeypatch,
):
    monkeypatch.setattr(
        auth_routes,
        "GOOGLE_CLIENT_ID",
        CLIENT_ID,
    )

    claims = google_claims()
    claims["iss"] = "https://example.com"

    monkeypatch.setattr(
        auth_routes.google_id_token,
        "verify_oauth2_token",
        lambda credential, request, audience:
            claims,
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        auth_routes.verify_google_credential(
            "fake-google-token"
        )

    assert (
        exc_info.value.status_code
        == 401
    )


def test_unverified_google_email(
    monkeypatch,
):
    monkeypatch.setattr(
        auth_routes,
        "GOOGLE_CLIENT_ID",
        CLIENT_ID,
    )

    claims = google_claims()
    claims["email_verified"] = False

    monkeypatch.setattr(
        auth_routes.google_id_token,
        "verify_oauth2_token",
        lambda credential, request, audience:
            claims,
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        auth_routes.verify_google_credential(
            "fake-google-token"
        )

    assert (
        exc_info.value.status_code
        == 401
    )
