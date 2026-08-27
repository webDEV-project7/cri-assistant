import pymupdf
import pytest

from app.investment_audit import (
    InvestorType,
    LandStatus,
    ProjectProfile,
)
from app.investment_classifier import ClassificationStatus
from app.investment_document_pipeline import (
    process_investment_pdf,
)


def create_profile(**overrides) -> ProjectProfile:
    values = {
        "sector": "Industrie agroalimentaire",
        "region": "Guelmim-Oued Noun",
        "province": "Guelmim",
        "commune": "Guelmim",
        "investor_type": InvestorType.EXISTING_COMPANY,
        "land_status": LandStatus.OWNER,
        "investment_amount_mad": 20_000_000,
        "planned_jobs": 80,
        "works": [],
        "requests_incentives": False,
        "requests_bank_financing": False,
        "potential_environmental_impact": False,
        "regulated_activity": False,
    }

    values.update(overrides)
    return ProjectProfile(**values)


def create_native_pdf(text: str) -> bytes:
    document = pymupdf.open()

    try:
        page = document.new_page(
            width=595,
            height=842,
        )

        page.insert_text(
            (72, 140),
            text,
            fontsize=22,
        )

        return document.tobytes(
            garbage=4,
            deflate=True,
        )

    finally:
        document.close()


def create_scanned_pdf(text: str) -> bytes:
    source_document = pymupdf.open()
    scanned_document = pymupdf.open()

    try:
        source_page = source_document.new_page(
            width=595,
            height=842,
        )

        source_page.insert_text(
            (72, 140),
            text,
            fontsize=28,
        )

        image = source_page.get_pixmap(
            matrix=pymupdf.Matrix(3, 3),
            alpha=False,
        )

        scanned_page = scanned_document.new_page(
            width=595,
            height=842,
        )

        scanned_page.insert_image(
            scanned_page.rect,
            pixmap=image,
        )

        return scanned_document.tobytes(
            garbage=4,
            deflate=True,
        )

    finally:
        source_document.close()
        scanned_document.close()


def test_classifies_native_pdf():
    result = process_investment_pdf(
        create_profile(),
        "document.pdf",
        create_native_pdf(
            "EXTRAIT DU REGISTRE DE COMMERCE"
        ),
    )

    assert result.page_count == 1
    assert "REGISTRE DE COMMERCE" in result.extracted_text
    assert (
        result.classification.status
        == ClassificationStatus.CLASSIFIED
    )
    assert (
        result.classification.requirement_code
        == "commercial_register"
    )


def test_classifies_scanned_pdf_after_ocr():
    result = process_investment_pdf(
        create_profile(),
        "document_scane.pdf",
        create_scanned_pdf(
            "REGISTRE DE COMMERCE"
        ),
    )

    assert result.page_count == 1
    assert "registre" in result.extracted_text.lower()
    assert "commerce" in result.extracted_text.lower()
    assert (
        result.classification.status
        == ClassificationStatus.CLASSIFIED
    )
    assert (
        result.classification.requirement_code
        == "commercial_register"
    )


def test_respects_requirements_applicable_to_profile():
    result = process_investment_pdf(
        create_profile(
            land_status=LandStatus.TENANT,
        ),
        "titre_foncier.pdf",
        create_native_pdf(
            "CERTIFICAT DE PROPRIETE"
        ),
    )

    assert (
        result.classification.status
        == ClassificationStatus.UNCLASSIFIED
    )
    assert result.classification.requirement_code is None


def test_rejects_empty_filename():
    with pytest.raises(
        ValueError,
        match="nom du fichier",
    ):
        process_investment_pdf(
            create_profile(),
            "   ",
            create_native_pdf(
                "REGISTRE DE COMMERCE"
            ),
        )
