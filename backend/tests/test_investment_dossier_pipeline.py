import pymupdf

from app.investment_audit import (
    InvestorType,
    LandStatus,
    ProjectProfile,
)
from app.investment_classifier import ClassificationStatus
from app.investment_dossier_pipeline import (
    InvestmentPdfInput,
    process_investment_dossier,
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

        page.insert_textbox(
            pymupdf.Rect(72, 100, 520, 300),
            text,
            fontsize=16,
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


def test_processes_multiple_pdfs_and_audits_presence():
    result = process_investment_dossier(
        profile=create_profile(),
        documents=[
            InvestmentPdfInput(
                filename="registre_commerce.pdf",
                pdf_content=create_native_pdf(
                    "EXTRAIT DU REGISTRE DE COMMERCE "
                    "DE LA SOCIETE INDUSTRIELLE GUELMIM"
                ),
            ),
            InvestmentPdfInput(
                filename="statuts_societe.pdf",
                pdf_content=create_native_pdf(
                    "STATUTS DE LA SOCIETE A RESPONSABILITE "
                    "LIMITEE INDUSTRIELLE GUELMIM"
                ),
            ),
        ],
    )

    assert len(result.documents) == 2
    assert result.audit.summary.submitted_document_count == 2
    assert result.audit.summary.present_requirement_count >= 2
    assert result.audit.summary.unclassified_document_count == 0

    requirement_codes = {
        document.classification.requirement_code
        for document in result.documents
    }

    assert "commercial_register" in requirement_codes
    assert "company_statutes" in requirement_codes


def test_scanned_pdf_is_included_in_global_audit():
    result = process_investment_dossier(
        profile=create_profile(),
        documents=[
            InvestmentPdfInput(
                filename="registre_scane.pdf",
                pdf_content=create_scanned_pdf(
                    "REGISTRE DE COMMERCE"
                ),
            )
        ],
    )

    processed = result.documents[0]

    assert (
        processed.classification.status
        == ClassificationStatus.CLASSIFIED
    )
    assert (
        processed.classification.requirement_code
        == "commercial_register"
    )
    assert result.audit.summary.present_requirement_count >= 1


def test_unclassified_document_is_forwarded_to_audit():
    result = process_investment_dossier(
        profile=create_profile(),
        documents=[
            InvestmentPdfInput(
                filename="facture_electricite.pdf",
                pdf_content=create_native_pdf(
                    "FACTURE DE CONSOMMATION ELECTRIQUE "
                    "SANS RAPPORT AVEC LES PIECES DU PROJET"
                ),
            )
        ],
    )

    assert (
        result.documents[0].classification.status
        == ClassificationStatus.UNCLASSIFIED
    )
    assert result.audit.unclassified_documents == [
        "facture_electricite.pdf"
    ]
    assert result.audit.summary.unclassified_document_count == 1


def test_duplicate_classifications_are_reported():
    commercial_register_text = (
        "EXTRAIT DU REGISTRE DE COMMERCE "
        "DE LA SOCIETE INDUSTRIELLE GUELMIM"
    )

    result = process_investment_dossier(
        profile=create_profile(),
        documents=[
            InvestmentPdfInput(
                filename="registre_commerce_1.pdf",
                pdf_content=create_native_pdf(
                    commercial_register_text
                ),
            ),
            InvestmentPdfInput(
                filename="registre_commerce_2.pdf",
                pdf_content=create_native_pdf(
                    commercial_register_text
                ),
            ),
        ],
    )

    assert result.audit.summary.duplicate_requirement_count == 1
    assert len(result.audit.duplicates) == 1

    duplicate = result.audit.duplicates[0]

    assert duplicate.requirement_code == "commercial_register"
    assert set(duplicate.filenames) == {
        "registre_commerce_1.pdf",
        "registre_commerce_2.pdf",
    }


def test_empty_dossier_produces_missing_requirements():
    result = process_investment_dossier(
        profile=create_profile(),
        documents=[],
    )

    assert result.documents == ()
    assert result.audit.summary.submitted_document_count == 0
    assert result.audit.summary.present_requirement_count == 0
    assert result.audit.summary.missing_required_count > 0
