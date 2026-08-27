import hashlib
from dataclasses import dataclass

from app.investment_audit import ProjectProfile
from app.investment_document_pipeline import (
    ProcessedInvestmentPdf,
    process_investment_document,
)
from app.investment_dossier import (
    DossierAuditReport,
    SubmittedDocument,
    audit_dossier_presence,
)


@dataclass(frozen=True)
class InvestmentPdfInput:
    """PDF transmis pour l'analyse d'un dossier d'investissement."""

    filename: str
    pdf_content: bytes


@dataclass(frozen=True)
class ProcessedInvestmentDossier:
    """Résultat complet du traitement de plusieurs PDF."""

    documents: tuple[ProcessedInvestmentPdf, ...]
    audit: DossierAuditReport


def process_investment_dossier(
    profile: ProjectProfile,
    documents: list[InvestmentPdfInput],
) -> ProcessedInvestmentDossier:
    """
    Extrait et classe chaque PDF, puis réalise l'audit global
    de présence des pièces applicables au projet.
    """
    processed_documents: list[ProcessedInvestmentPdf] = []
    submitted_documents: list[SubmittedDocument] = []

    for document in documents:
        processed_document = process_investment_document(
            profile=profile,
            filename=document.filename,
            document_content=document.pdf_content,
        )

        checksum = hashlib.sha256(
            document.pdf_content
        ).hexdigest()

        processed_documents.append(
            processed_document
        )

        submitted_documents.append(
            SubmittedDocument(
                filename=processed_document.filename,
                requirement_code=(
                    processed_document
                    .classification
                    .requirement_code
                ),
                content_sha256=checksum,
            )
        )

    audit = audit_dossier_presence(
        profile=profile,
        documents=submitted_documents,
    )

    return ProcessedInvestmentDossier(
        documents=tuple(processed_documents),
        audit=audit,
    )
