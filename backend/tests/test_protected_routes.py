from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import ChatRequest, app


client = TestClient(app)


def test_chat_requires_authentication():
    response = client.post(
        "/chat",
        json={
            "message": "test-auth-only",
            "conversation_id": None,
            "analysis_context": None,
        },
    )

    assert response.status_code == 401


def test_conversation_list_requires_authentication():
    response = client.get(
        "/conversations"
    )

    assert response.status_code == 401


def test_conversation_creation_requires_authentication():
    response = client.post(
        "/conversations",
        json={
            "title": "Test",
        },
    )

    assert response.status_code == 401


def test_conversation_read_requires_authentication():
    response = client.get(
        "/conversations/"
        "00000000-0000-0000-0000-000000000001"
    )

    assert response.status_code == 401


def test_conversation_delete_requires_authentication():
    response = client.delete(
        "/conversations/"
        "00000000-0000-0000-0000-000000000001"
    )

    assert response.status_code == 401


def test_prime_calculation_requires_authentication():
    response = client.post(
        "/primes/calculate",
        json={},
    )

    assert response.status_code == 401


def test_document_inspection_requires_authentication():
    response = client.post(
        "/investment-dossiers/inspect"
    )

    assert response.status_code == 401


def test_document_audit_requires_authentication():
    response = client.post(
        "/investment-dossiers/audit"
    )

    assert response.status_code == 401


def test_document_report_requires_authentication():
    response = client.post(
        "/investment-dossiers/report",
        json={},
    )

    assert response.status_code == 401


def test_chat_request_does_not_accept_user_email():
    assert (
        "user_email"
        not in ChatRequest.model_fields
    )

def test_tpme_prime_calculation_requires_authentication():
    response = client.post(
        "/primes/tpme",
        json={
            "total_investment_mad": 10_000_000,
            "primable_investment_mad": 8_000_000,
            "stable_jobs": 30,
            "equity_financing_mad": 2_000_000,
            "company_age_years": 2,
            "activity_eligible": True,
            "priority_activity": True,
            "territorial_category": "B",
        },
    )

    assert response.status_code in {401, 403}
