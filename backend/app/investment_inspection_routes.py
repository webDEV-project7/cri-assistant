from __future__ import annotations

from pathlib import PurePath
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.ingestion import PdfIngestionError
from app.investment_dossier_pipeline import InvestmentPdfInput
from app.investment_profile_detection import (
    InvestmentDocumentInspectionResponse,
    inspect_investment_documents,
)


MAX_DOCUMENT_COUNT = 10
MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024

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
    tags=["Investment dossier inspection"],
)


def normalize_filename(
    filename: str | None,
) -> str:
    if not filename:
        return ""

    portable_name = filename.replace(
        "\\",
        "/",
    )

    return PurePath(
        portable_name
    ).name.strip()


@router.post(
    "/inspect",
    response_model=InvestmentDocumentInspectionResponse,
)
async def inspect_uploaded_documents(
    files: Annotated[list[UploadFile], File()],
) -> InvestmentDocumentInspectionResponse:
    if not files:
        raise HTTPException(
            status_code=400,
            detail=(
                "Au moins un document PDF ou une image "
                "est obligatoire."
            ),
        )

    if len(files) > MAX_DOCUMENT_COUNT:
        raise HTTPException(
            status_code=413,
            detail=(
                "Vous pouvez transmettre au maximum "
                f"{MAX_DOCUMENT_COUNT} documents."
            ),
        )

    document_inputs: list[
        InvestmentPdfInput
    ] = []

    for uploaded_file in files:
        try:
            filename = normalize_filename(
                uploaded_file.filename
            )

            if not filename:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Un document possède un nom invalide."
                    ),
                )

            suffix = PurePath(
                filename
            ).suffix.lower()

            if suffix not in SUPPORTED_DOCUMENT_EXTENSIONS:
                raise HTTPException(
                    status_code=415,
                    detail=(
                        f"Le format de {filename} n'est pas "
                        "pris en charge. Formats acceptés : "
                        "PDF, JPG, JPEG et PNG."
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
                        f"Type de fichier non autorisé pour "
                        f"{filename}."
                    ),
                )

            document_content = await uploaded_file.read(
                MAX_DOCUMENT_SIZE_BYTES + 1
            )

        finally:
            await uploaded_file.close()

        if not document_content:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Le document {filename} est vide."
                ),
            )

        if (
            len(document_content)
            > MAX_DOCUMENT_SIZE_BYTES
        ):
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Le document {filename} dépasse "
                    "la limite de 10 Mo."
                ),
            )

        if (
            suffix == ".pdf"
            and not document_content.startswith(b"%PDF-")
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Le contenu de {filename} n'est pas "
                    "un PDF valide."
                ),
            )

        document_inputs.append(
            InvestmentPdfInput(
                filename=filename,
                pdf_content=document_content,
            )
        )

    try:
        return inspect_investment_documents(
            document_inputs
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
