from dataclasses import dataclass
from pathlib import Path

import pymupdf

from app.ingestion import (
    PdfIngestionError,
    extract_pdf_pages,
)
from app.investment_audit import ProjectProfile
from app.investment_classifier import (
    DocumentClassificationResult,
    DocumentToClassify,
    classify_document,
)


@dataclass(frozen=True)
class ProcessedInvestmentPdf:
    """Résultat de l'extraction et du classement d'un PDF."""

    filename: str
    page_count: int
    pages: tuple[tuple[int, str], ...]
    extracted_text: str
    classification: DocumentClassificationResult


def process_investment_pdf(
    profile: ProjectProfile,
    filename: str,
    pdf_content: bytes,
) -> ProcessedInvestmentPdf:
    """
    Extrait le texte natif ou OCR d'un PDF, puis le classe
    selon les pièces applicables au profil du projet.
    """
    normalized_filename = filename.strip()

    if not normalized_filename:
        raise ValueError(
            "Le nom du fichier PDF est obligatoire."
        )

    if not isinstance(pdf_content, bytes) or not pdf_content:
        raise ValueError(
            "Le contenu du fichier PDF est obligatoire."
        )

    extracted_pages = extract_pdf_pages(pdf_content)

    extracted_text = "\n\n".join(
        page_text
        for _, page_text in extracted_pages
        if page_text
    ).strip()

    document = DocumentToClassify(
        filename=normalized_filename,
        extracted_text=extracted_text,
    )

    classification = classify_document(
        profile,
        document,
    )

    return ProcessedInvestmentPdf(
        filename=normalized_filename,
        page_count=len(extracted_pages),
        pages=tuple(extracted_pages),
        extracted_text=extracted_text,
        classification=classification,
    )


SUPPORTED_INVESTMENT_IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
}

IMAGE_FILETYPE_BY_SUFFIX = {
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".png": "png",
}


def convert_investment_image_to_pdf(
    image_content: bytes,
    suffix: str,
) -> bytes:
    """
    Convertit une image JPG, JPEG ou PNG en PDF à une page.

    Le PDF obtenu est ensuite traité par le même moteur OCR
    que les autres documents du dossier.
    """
    normalized_suffix = suffix.lower().strip()

    filetype = IMAGE_FILETYPE_BY_SUFFIX.get(
        normalized_suffix
    )

    if filetype is None:
        raise ValueError(
            "Format d'image non pris en charge. "
            "Formats acceptés : JPG, JPEG et PNG."
        )

    if (
        not isinstance(image_content, bytes)
        or not image_content
    ):
        raise ValueError(
            "Le contenu de l'image est obligatoire."
        )

    image_document = None

    try:
        image_document = pymupdf.open(
            stream=image_content,
            filetype=filetype,
        )

        if image_document.page_count != 1:
            raise PdfIngestionError(
                "L'image transmise ne peut pas être "
                "interprétée comme une page unique."
            )

        pdf_content = image_document.convert_to_pdf()

    except (
        pymupdf.FileDataError,
        RuntimeError,
        ValueError,
    ) as error:
        raise PdfIngestionError(
            "L'image est illisible ou endommagée."
        ) from error

    finally:
        if image_document is not None:
            image_document.close()

    if not pdf_content:
        raise PdfIngestionError(
            "La conversion de l'image en PDF a échoué."
        )

    return bytes(pdf_content)


def process_investment_document(
    profile: ProjectProfile,
    filename: str,
    document_content: bytes,
) -> ProcessedInvestmentPdf:
    """
    Traite un PDF ou une image de document d'investissement.

    Les images sont converties en PDF interne avant le
    lancement de l'OCR et de la classification.
    """
    normalized_filename = filename.strip()

    if not normalized_filename:
        raise ValueError(
            "Le nom du document est obligatoire."
        )

    suffix = Path(
        normalized_filename
    ).suffix.lower()

    if suffix == ".pdf":
        pdf_content = document_content

    elif suffix in SUPPORTED_INVESTMENT_IMAGE_SUFFIXES:
        pdf_content = convert_investment_image_to_pdf(
            document_content,
            suffix,
        )

    else:
        raise ValueError(
            "Format non pris en charge. "
            "Formats acceptés : PDF, JPG, JPEG et PNG."
        )

    return process_investment_pdf(
        profile=profile,
        filename=normalized_filename,
        pdf_content=pdf_content,
    )
