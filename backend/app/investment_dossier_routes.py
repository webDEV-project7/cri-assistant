from app.investment_dossier_report import (
    build_investment_dossier_report,
)
from fastapi.responses import Response
from pathlib import PurePath
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ValidationError

from app.ingestion import PdfIngestionError
from app.investment_audit import ProjectProfile
from app.investment_classifier import DocumentClassificationResult
from app.investment_dossier import DossierAuditReport
from app.investment_dossier_pipeline import (
    InvestmentPdfInput,
    process_investment_dossier,
)


MAX_PDF_COUNT = 10
MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024

SUPPORTED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}

SUPPORTED_DOCUMENT_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "application/octet-stream",
}

router = APIRouter(
    prefix="/investment-dossiers",
    tags=["Investment dossiers"],
)


class ProcessedDocumentResponse(BaseModel):
    filename: str
    page_count: int
    classification: DocumentClassificationResult


class InvestmentDossierAuditResponse(BaseModel):
    documents: list[ProcessedDocumentResponse]
    audit: DossierAuditReport


def normalize_filename(filename: str | None) -> str:
    if not filename:
        return ""

    portable_name = filename.replace("\\", "/")
    return PurePath(portable_name).name.strip()


@router.post(
    "/audit",
    response_model=InvestmentDossierAuditResponse,
)
async def audit_investment_dossier(
    profile: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File()],
) -> InvestmentDossierAuditResponse:
    try:
        project_profile = ProjectProfile.model_validate_json(
            profile
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Le profil du projet est invalide.",
                "errors": error.errors(include_url=False),
            },
        ) from error

    if not files:
        raise HTTPException(
            status_code=400,
            detail="Au moins un fichier PDF est obligatoire.",
        )

    if len(files) > MAX_PDF_COUNT:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Le dossier ne peut pas contenir plus de "
                f"{MAX_PDF_COUNT} fichiers."
            ),
        )

    pdf_inputs: list[InvestmentPdfInput] = []

    for uploaded_file in files:
        try:
            filename = normalize_filename(
                uploaded_file.filename
            )

            if not filename:
                raise HTTPException(
                    status_code=400,
                    detail="Un fichier possède un nom invalide.",
                )
            suffix = PurePath(
                filename
            ).suffix.lower()

            if suffix not in SUPPORTED_DOCUMENT_EXTENSIONS:
                raise HTTPException(
                    status_code=415,
                    detail=(
                        f"Le format du fichier {filename} "
                        "n'est pas pris en charge. "
                        "Formats acceptés : PDF, JPG, JPEG et PNG."
                    ),
                )

            content_type = (
                uploaded_file.content_type or ""
            ).lower()

            if (
                content_type
                not in SUPPORTED_DOCUMENT_CONTENT_TYPES
            ):
                raise HTTPException(
                    status_code=415,
                    detail=(
                        f"Type non autorisé pour {filename} : "
                        f"{uploaded_file.content_type}"
                    ),
                )

            pdf_content = await uploaded_file.read(
                MAX_PDF_SIZE_BYTES + 1
            )

        finally:
            await uploaded_file.close()

        if not pdf_content:
            raise HTTPException(
                status_code=400,
                detail=f"Le fichier {filename} est vide.",
            )

        if len(pdf_content) > MAX_PDF_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Le fichier {filename} dépasse la taille "
                    f"maximale de 10 Mo."
                ),
            )

        if (
            suffix == ".pdf"
            and not pdf_content.startswith(b"%PDF-")
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Le contenu de {filename} n'est pas "
                    f"un PDF valide."
                ),
            )

        pdf_inputs.append(
            InvestmentPdfInput(
                filename=filename,
                pdf_content=pdf_content,
            )
        )

    try:
        result = process_investment_dossier(
            profile=project_profile,
            documents=pdf_inputs,
        )
    except PdfIngestionError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return InvestmentDossierAuditResponse(
        documents=[
            ProcessedDocumentResponse(
                filename=document.filename,
                page_count=document.page_count,
                classification=document.classification,
            )
            for document in result.documents
        ],
        audit=result.audit,
    )



@router.post(
    "/report",
    response_class=Response,
)
async def download_investment_dossier_report(
    payload: dict,
) -> Response:
    """
    Génère un rapport PDF temporaire à partir du résultat
    structuré de l'audit.

    Le rapport n'est pas enregistré sur le serveur.
    """
    try:
        pdf_content, filename = (
            build_investment_dossier_report(
                payload
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )
