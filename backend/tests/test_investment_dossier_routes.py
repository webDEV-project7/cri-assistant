import pymupdf
import pytest
from fastapi.testclient import TestClient

from app import investment_dossier_routes as routes
from app.investment_audit import (
    InvestorType,
    LandStatus,
    ProjectProfile,
)
from app.main import app
from app.auth_routes import get_current_user
from app.models import User


client = TestClient(app)


@pytest.fixture(autouse=True)
def authenticated_user():
    def override_current_user():
        return User(
            name="Investisseur Test",
            email=(
                "investisseur.test@example.com"
            ),
            auth_provider="local",
            is_active=True,
        )

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    try:
        yield

    finally:
        app.dependency_overrides.pop(
            get_current_user,
            None,
        )



def create_profile() -> ProjectProfile:
    return ProjectProfile(
        sector="Industrie agroalimentaire",
        region="Guelmim-Oued Noun",
        province="Guelmim",
        commune="Guelmim",
        investor_type=InvestorType.EXISTING_COMPANY,
        land_status=LandStatus.OWNER,
        investment_amount_mad=20_000_000,
        planned_jobs=80,
        works=[],
        requests_incentives=False,
        requests_bank_financing=False,
        potential_environmental_impact=False,
        regulated_activity=False,
    )


def create_pdf(text: str) -> bytes:
    document = pymupdf.open()

    try:
        page = document.new_page()
        page.insert_text(
            (72, 140),
            text,
            fontsize=20,
        )

        return document.tobytes(
            garbage=4,
            deflate=True,
        )
    finally:
        document.close()


def test_audits_multiple_uploaded_pdfs():
    response = client.post(
        "/investment-dossiers/audit",
        data={
            "profile": create_profile().model_dump_json(),
        },
        files=[
            (
                "files",
                (
                    "registre.pdf",
                    create_pdf("REGISTRE DE COMMERCE"),
                    "application/pdf",
                ),
            ),
            (
                "files",
                (
                    "statuts.pdf",
                    create_pdf("STATUTS DE LA SOCIETE"),
                    "application/pdf",
                ),
            ),
        ],
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload["documents"]) == 2
    assert payload["audit"]["summary"][
        "submitted_document_count"
    ] == 2


def test_rejects_invalid_project_profile():
    response = client.post(
        "/investment-dossiers/audit",
        data={"profile": '{"invalid": true}'},
        files=[
            (
                "files",
                (
                    "document.pdf",
                    create_pdf("REGISTRE DE COMMERCE"),
                    "application/pdf",
                ),
            )
        ],
    )

    assert response.status_code == 422


def test_rejects_non_pdf_file():
    response = client.post(
        "/investment-dossiers/audit",
        data={
            "profile": create_profile().model_dump_json(),
        },
        files=[
            (
                "files",
                (
                    "document.txt",
                    b"simple text",
                    "text/plain",
                ),
            )
        ],
    )

    assert response.status_code == 415


def test_rejects_oversized_pdf(monkeypatch):
    monkeypatch.setattr(
        routes,
        "MAX_PDF_SIZE_BYTES",
        16,
    )

    response = client.post(
        "/investment-dossiers/audit",
        data={
            "profile": create_profile().model_dump_json(),
        },
        files=[
            (
                "files",
                (
                    "large.pdf",
                    b"%PDF-" + b"x" * 20,
                    "application/pdf",
                ),
            )
        ],
    )

    assert response.status_code == 413
