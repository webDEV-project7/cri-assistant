from __future__ import annotations

import pymupdf

from app.investment_dossier_pipeline import (
    InvestmentPdfInput,
)
from app.investment_profile_detection import (
    inspect_investment_documents,
)


def create_pdf(lines: list[str]) -> bytes:
    document = pymupdf.open()

    try:
        page = document.new_page(
            width=595,
            height=842,
        )

        y = 70

        for line in lines:
            page.insert_text(
                (50, y),
                line,
                fontsize=12,
            )

            y += 28

        return document.tobytes()

    finally:
        document.close()


def missing_codes(response) -> set[str]:
    return {
        item.code
        for item
        in response.provisional_missing_documents
    }


def determine_codes(response) -> set[str]:
    return {
        item.code
        for item
        in response.documents_to_determine
    }


def test_cin_only_reports_provisional_missing_documents():
    response = inspect_investment_documents(
        [
            InvestmentPdfInput(
                filename="cin_test.pdf",
                pdf_content=create_pdf(
                    [
                        "ROYAUME DU MAROC",
                        "CARTE NATIONALE D IDENTITE",
                    ]
                ),
            )
        ]
    )

    assert (
        "Pièce d'identité"
        in response.detected_documents
    )

    codes = missing_codes(response)

    assert "project_summary" in codes
    assert "investment_program" in codes
    assert "land_or_location_document" in codes

    assert (
        "investor_legal_documents"
        in determine_codes(response)
    )


def test_detected_project_and_land_are_not_missing():
    response = inspect_investment_documents(
        [
            InvestmentPdfInput(
                filename="fiche_projet.pdf",
                pdf_content=create_pdf(
                    [
                        "FICHE PROJET",
                        "PROJET D INVESTISSEMENT",
                        "MONTANT DE L INVESTISSEMENT : 5000000 MAD",
                    ]
                ),
            ),
            InvestmentPdfInput(
                filename="titre_foncier.pdf",
                pdf_content=create_pdf(
                    [
                        "TITRE FONCIER",
                        "ATTESTATION DE PROPRIETE",
                    ]
                ),
            ),
        ]
    )

    codes = missing_codes(response)

    assert "project_summary" not in codes
    assert "land_or_location_document" not in codes
