from __future__ import annotations

import pymupdf
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.investment_inspection_routes import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def create_pdf() -> bytes:
    document = pymupdf.open()

    try:
        page = document.new_page()
        page.insert_text(
            (50, 80),
            "PROJET : Unite industrielle",
            fontsize=12,
        )
        page.insert_text(
            (50, 110),
            "INVESTISSEMENT TOTAL : 5000000 MAD",
            fontsize=12,
        )

        return document.tobytes()

    finally:
        document.close()


def test_inspection_does_not_require_project_profile():
    response = client.post(
        "/investment-dossiers/inspect",
        files=[
            (
                "files",
                (
                    "projet.pdf",
                    create_pdf(),
                    "application/pdf",
                ),
            )
        ],
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["documents"]
    assert "detected_profile" in payload
    assert (
        payload["detected_profile"][
            "investment_amount_mad"
        ]
        == 5_000_000
    )
