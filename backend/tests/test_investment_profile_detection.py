from __future__ import annotations

import pymupdf

from app.investment_dossier_pipeline import InvestmentPdfInput
from app.investment_profile_detection import (
    inspect_investment_documents,
)


def create_native_pdf(
    lines: list[str],
) -> bytes:
    document = pymupdf.open()

    try:
        page = document.new_page(
            width=595,
            height=842,
        )

        y_position = 70

        for line in lines:
            page.insert_text(
                (50, y_position),
                line,
                fontsize=12,
            )

            y_position += 28

        return document.tobytes()

    finally:
        document.close()


def test_detects_project_information_without_profile():
    pdf_content = create_native_pdf(
        [
            "NOM DU PROJET : Unite de production de glace",
            "RAISON SOCIALE : ATLAS FROID SARL",
            "SECTEUR : Industrie agroalimentaire",
            "INVESTISSEMENT TOTAL : 12 000 000 MAD",
            "EMPLOIS PREVUS : 35",
            "LOCALISATION : GUELMIM",
            "NATURE DES TRAVAUX : Construction",
        ]
    )

    response = inspect_investment_documents(
        [
            InvestmentPdfInput(
                filename="fiche_projet.pdf",
                pdf_content=pdf_content,
            )
        ]
    )

    detected = response.detected_profile

    assert detected.project_name is not None
    assert "production de glace" in detected.project_name.lower()
    assert detected.promoter_name is not None
    assert detected.legal_form == "SARL"
    assert detected.sector == "Agroalimentaire"
    assert detected.investment_amount_mad == 12_000_000
    assert detected.planned_jobs == 35
    assert "construction" in detected.works


def test_cin_only_reports_missing_project_information():
    pdf_content = create_native_pdf(
        [
            "ROYAUME DU MAROC",
            "CARTE NATIONALE D IDENTITE",
            "DOCUMENT DE TEST",
        ]
    )

    response = inspect_investment_documents(
        [
            InvestmentPdfInput(
                filename="cin_test.pdf",
                pdf_content=pdf_content,
            )
        ]
    )

    assert response.documents[0].detected_type == "Pièce d'identité"
    assert "sector" in response.missing_fields
    assert "investment_amount_mad" in response.missing_fields
