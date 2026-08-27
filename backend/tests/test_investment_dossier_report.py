from __future__ import annotations

import unicodedata

import pymupdf
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.investment_dossier_routes import (
    router,
)


app = FastAPI()
app.include_router(router)

client = TestClient(app)


def normalize_text(
    value: str,
) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    return (
        normalized
        .upper()
        .replace("’", "'")
    )


def create_payload() -> dict:
    return {
        "documents": [],
        "audit": {
            "project_profile": {
                "project_name": (
                    "Unité de transformation "
                    "agroalimentaire"
                ),
                "promoter_name": (
                    "ATLAS INVEST SUD SARL"
                ),
                "legal_form": "SARL",
                "sector": "Agroalimentaire",
                "region": "Guelmim-Oued Noun",
                "province": "Guelmim",
                "commune": "Guelmim",
                "investor_type": (
                    "societe_existante"
                ),
                "land_status": "proprietaire",
                "investment_amount_mad": (
                    20_000_000
                ),
                "planned_jobs": 45,
                "works": [
                    "construction",
                ],
                "requests_incentives": True,
                "requests_bank_financing": False,
                "potential_environmental_impact": False,
                "regulated_activity": False,
            },
            "results": [
                {
                    "requirement": {
                        "code": "project_summary",
                        "label": (
                            "Fiche synthétique "
                            "du projet"
                        ),
                        "category": "projet",
                        "level": "obligatoire",
                        "reason": (
                            "Présenter le projet."
                        ),
                        "authority": None,
                        "source_reference": None,
                    },
                    "status": (
                        "presente_non_verifiee"
                    ),
                    "submitted_files": [
                        "fiche_projet.pdf",
                    ],
                },
                {
                    "requirement": {
                        "code": "negative_certificate",
                        "label": "Certificat négatif",
                        "category": (
                            "creation_entreprise"
                        ),
                        "level": "conditionnelle",
                        "reason": (
                            "Identifier la société."
                        ),
                        "authority": None,
                        "source_reference": None,
                    },
                    "status": (
                        "presente_non_verifiee"
                    ),
                    "submitted_files": [
                        "certificat.pdf",
                    ],
                },
                {
                    "requirement": {
                        "code": "investment_program",
                        "label": (
                            "Programme détaillé "
                            "d'investissement"
                        ),
                        "category": "projet",
                        "level": "obligatoire",
                        "reason": (
                            "Présenter les dépenses."
                        ),
                        "authority": None,
                        "source_reference": None,
                    },
                    "status": "manquante",
                    "submitted_files": [],
                },
                {
                    "requirement": {
                        "code": "partners_identity",
                        "label": (
                            "CIN ou passeports "
                            "des associés"
                        ),
                        "category": (
                            "creation_entreprise"
                        ),
                        "level": "conditionnelle",
                        "reason": (
                            "Identifier les associés."
                        ),
                        "authority": None,
                        "source_reference": None,
                    },
                    "status": "manquante",
                    "submitted_files": [],
                },
                {
                    "requirement": {
                        "code": "project_schedule",
                        "label": (
                            "Calendrier prévisionnel "
                            "de réalisation"
                        ),
                        "category": "projet",
                        "level": "recommandee",
                        "reason": (
                            "Planifier le projet."
                        ),
                        "authority": None,
                        "source_reference": None,
                    },
                    "status": (
                        "recommandee_absente"
                    ),
                    "submitted_files": [],
                },
            ],
            "summary": {
                "submitted_document_count": 2,
                "applicable_requirement_count": 5,
                "present_requirement_count": 2,
                "missing_required_count": 1,
                "missing_conditional_count": 1,
                "recommended_absent_count": 1,
                "unclassified_document_count": 0,
                "unknown_requirement_code_count": 0,
                "duplicate_requirement_count": 0,
                "completeness_percentage": 50,
            },
            "unclassified_documents": [],
            "unknown_requirement_codes": [],
            "duplicates": [],
            "warning": (
                "Message technique interne."
            ),
        },
    }


def test_generates_simple_black_and_white_report():
    response = client.post(
        "/investment-dossiers/report",
        json=create_payload(),
    )

    assert response.status_code == 200

    assert response.content.startswith(
        b"%PDF"
    )

    assert (
        response.headers[
            "content-type"
        ].startswith(
            "application/pdf"
        )
    )

    pdf_document = pymupdf.open(
        stream=response.content,
        filetype="pdf",
    )

    try:
        assert len(pdf_document) >= 1

        extracted_text = "\n".join(
            page.get_text()
            for page in pdf_document
        )

        normalized = normalize_text(
            extracted_text
        )

        assert (
            "IDENTIFICATION DU PORTEUR DE PROJET"
            in normalized
        )

        assert (
            "PRESENTATION DU PROJET"
            in normalized
        )

        assert (
            "PIECES JOINTES AU DOSSIER"
            in normalized
        )

        assert (
            "PIECES OBLIGATOIRES OU CONDITIONNELLES MANQUANTES"
            in normalized
        )

        assert (
            "ATLAS INVEST SUD SARL"
            in normalized
        )

        assert (
            "20 000 000 DH"
            in normalized
        )

        assert (
            "FICHE SYNTHETIQUE DU PROJET"
            in normalized
        )

        assert (
            "PROGRAMME DETAILLE D'INVESTISSEMENT"
            in normalized
        )

        assert (
            "CIN OU PASSEPORTS DES ASSOCIES"
            in normalized
        )

        assert (
            "CALENDRIER PREVISIONNEL"
            in normalized
        )

        forbidden_terms = (
            "OCR",
            "NON VERIFIE",
            "NON VERIFIEE",
            "NIVEAU :",
            "FICHIER(S) ASSOCIE(S)",
        )

        for forbidden_term in forbidden_terms:
            assert (
                forbidden_term
                not in normalized
            )

        first_page = pdf_document[0]

        rendered_page = (
            first_page.get_pixmap(
                matrix=pymupdf.Matrix(
                    1.2,
                    1.2,
                ),
                alpha=False,
            )
        )

        assert rendered_page.width > 0
        assert rendered_page.height > 0

        font_page = next(
            page
            for page in pdf_document
            if (
                "FICHE SYNTHETIQUE"
                in normalize_text(
                    page.get_text()
                )
            )
        )

        text_dictionary = (
            font_page.get_text(
                "dict"
            )
        )

        matching_fonts = []

        for block in text_dictionary[
            "blocks"
        ]:
            for line in block.get(
                "lines",
                [],
            ):
                for span in line.get(
                    "spans",
                    [],
                ):
                    span_text = normalize_text(
                        span.get(
                            "text",
                            "",
                        )
                    )

                    if (
                        "FICHE SYNTHETIQUE"
                        in span_text
                    ):
                        matching_fonts.append(
                            span.get(
                                "font",
                                "",
                            )
                        )

        assert matching_fonts

        assert any(
            "BOLD" in font.upper()
            for font in matching_fonts
        )

    finally:
        pdf_document.close()

def test_report_includes_all_missing_requirement_levels():
    response = client.post(
        "/investment-dossiers/report",
        json=create_payload(),
    )

    assert response.status_code == 200

    pdf_document = pymupdf.open(
        stream=response.content,
        filetype="pdf",
    )

    try:
        extracted_text = "\n".join(
            page.get_text()
            for page in pdf_document
        )

        normalized = normalize_text(
            extracted_text
        )

        assert (
            "PIECES OBLIGATOIRES OU "
            "CONDITIONNELLES MANQUANTES"
            in normalized
        )

        assert (
            "CIN OU PASSEPORTS DES ASSOCIES"
            in normalized
        )

        assert (
            "PIECES RECOMMANDEES ABSENTES"
            in normalized
        )

        assert (
            "CALENDRIER PREVISIONNEL "
            "DE REALISATION"
            in normalized
        )

    finally:
        pdf_document.close()

