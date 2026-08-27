import hashlib
import re
from io import BytesIO
from urllib.parse import urlparse

import httpx
import pymupdf
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.rag import (
    MetadataValue,
    REQUIRED_METADATA_FIELDS,
    SourceDocument,
    index_documents,
)


ALLOWED_OFFICIAL_DOMAINS = (
    "sgg.gov.ma",
    "justice.gov.ma",
)

MAX_PDF_SIZE_BYTES = 30 * 1024 * 1024
DEFAULT_CHUNK_SIZE = 1800
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_BATCH_SIZE = 16
OCR_LANGUAGES = "fra+ara"
OCR_DPI = 300
OCR_NATIVE_TEXT_MIN_CHARS = 40


class PdfIngestionError(RuntimeError):
    """Erreur pendant le téléchargement ou l'analyse d'un PDF."""


def validate_official_source_url(source_url: str) -> None:
    parsed_url = urlparse(source_url)
    hostname = (parsed_url.hostname or "").lower()

    if parsed_url.scheme != "https":
        raise ValueError(
            "La source officielle doit utiliser HTTPS"
        )

    is_allowed = any(
        hostname == domain
        or hostname.endswith(f".{domain}")
        for domain in ALLOWED_OFFICIAL_DOMAINS
    )

    if not is_allowed:
        raise ValueError(
            "Le domaine de la source n'est pas autorisé"
        )


def validate_source_metadata(
    metadata: dict[str, MetadataValue],
) -> None:
    required_without_url = (
        REQUIRED_METADATA_FIELDS - {"source_url"}
    )

    missing_fields = required_without_url.difference(metadata)

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))

        raise ValueError(
            f"Métadonnées obligatoires absentes : {missing}"
        )

    for field in required_without_url:
        value = metadata[field]

        if isinstance(value, str) and not value.strip():
            raise ValueError(
                f"La métadonnée '{field}' ne doit pas être vide"
            )


def download_official_pdf(source_url: str) -> bytes:
    validate_official_source_url(source_url)

    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=httpx.Timeout(
                timeout=60.0,
                connect=15.0,
            ),
        ) as client:
            response = client.get(source_url)
            response.raise_for_status()

    except httpx.HTTPError as error:
        raise PdfIngestionError(
            "Impossible de télécharger le PDF officiel"
        ) from error

    pdf_content = response.content

    if not pdf_content.startswith(b"%PDF"):
        raise PdfIngestionError(
            "Le fichier téléchargé n'est pas un PDF valide"
        )

    if len(pdf_content) > MAX_PDF_SIZE_BYTES:
        raise PdfIngestionError(
            "Le PDF dépasse la taille maximale autorisée"
        )

    return pdf_content


def normalize_text(text: str) -> str:
    normalized = text.replace("\u00a0", " ")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n[ \t]+", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    return normalized.strip()


def split_text(
    text: str,
    max_chars: int = DEFAULT_CHUNK_SIZE,
    overlap_chars: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    normalized_text = normalize_text(text)

    if not normalized_text:
        return []

    if max_chars < 200:
        raise ValueError(
            "La taille d'un segment doit être au moins de 200"
        )

    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError(
            "Le chevauchement doit être positif "
            "et inférieur à la taille d'un segment"
        )

    chunks: list[str] = []
    start = 0
    text_length = len(normalized_text)

    while start < text_length:
        hard_end = min(start + max_chars, text_length)
        end = hard_end

        if hard_end < text_length:
            candidate = normalized_text[start:hard_end]

            boundaries = [
                candidate.rfind("\n\n"),
                candidate.rfind(". "),
                candidate.rfind("؛ "),
                candidate.rfind("؟ "),
            ]

            best_boundary = max(boundaries)

            if best_boundary >= max_chars // 2:
                end = start + best_boundary + 1

        chunk = normalized_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(
            end - overlap_chars,
            start + 1,
        )

    return chunks


def extract_page_with_ocr(
    document: pymupdf.Document,
    page_index: int,
) -> str:
    """Extrait le texte d'une page scannée avec Tesseract."""
    page = document.load_page(page_index)

    try:
        text_page = page.get_textpage_ocr(
            language=OCR_LANGUAGES,
            dpi=OCR_DPI,
            full=True,
        )

        return normalize_text(
            page.get_text(
                "text",
                textpage=text_page,
            )
        )

    except (RuntimeError, ValueError) as error:
        raise PdfIngestionError(
            f"Échec de l'OCR à la page {page_index + 1}"
        ) from error


def extract_pdf_pages(
    pdf_content: bytes,
) -> list[tuple[int, str]]:
    """
    Extrait prioritairement le texte natif du PDF.

    L'OCR est utilisé uniquement pour les pages ne contenant
    aucun texte ou contenant un texte natif insuffisant.
    """
    try:
        reader = PdfReader(BytesIO(pdf_content))

    except PdfReadError as error:
        raise PdfIngestionError(
            "Le PDF officiel est illisible"
        ) from error

    pages: list[tuple[int, str]] = []
    ocr_document: pymupdf.Document | None = None

    try:
        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            native_text = normalize_text(
                page.extract_text() or ""
            )

            extracted_text = native_text

            if len(native_text) < OCR_NATIVE_TEXT_MIN_CHARS:
                if ocr_document is None:
                    try:
                        ocr_document = pymupdf.open(
                            stream=pdf_content,
                            filetype="pdf",
                        )

                    except (
                        pymupdf.FileDataError,
                        RuntimeError,
                        ValueError,
                    ) as error:
                        raise PdfIngestionError(
                            "Le PDF ne peut pas être ouvert pour l'OCR"
                        ) from error

                ocr_text = extract_page_with_ocr(
                    ocr_document,
                    page_number - 1,
                )

                if len(ocr_text) > len(native_text):
                    extracted_text = ocr_text

            if extracted_text:
                pages.append(
                    (
                        page_number,
                        extracted_text,
                    )
                )

    finally:
        if ocr_document is not None:
            ocr_document.close()

    if not pages:
        raise PdfIngestionError(
            "Aucun texte exploitable n'a été trouvé dans le PDF"
        )

    return pages


def ingest_official_pdf(
    source_url: str,
    metadata: dict[str, MetadataValue],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, MetadataValue]:
    validate_official_source_url(source_url)
    validate_source_metadata(metadata)

    if batch_size < 1 or batch_size > 64:
        raise ValueError(
            "La taille du lot doit être comprise entre 1 et 64"
        )

    pdf_content = download_official_pdf(source_url)
    checksum = hashlib.sha256(pdf_content).hexdigest()
    source_id = checksum[:16]
    pages = extract_pdf_pages(pdf_content)

    documents: list[SourceDocument] = []

    for page_number, page_text in pages:
        chunks = split_text(
            page_text,
            max_chars=chunk_size,
            overlap_chars=chunk_overlap,
        )

        for chunk_number, chunk in enumerate(
            chunks,
            start=1,
        ):
            document_metadata = {
                **metadata,
                "source_url": source_url,
                "source_id": source_id,
                "checksum_sha256": checksum,
                "page_number": page_number,
                "chunk_number": chunk_number,
                "total_pages": len(pages),
            }

            documents.append(
                SourceDocument(
                    id=(
                        f"{source_id}"
                        f"-p{page_number:04d}"
                        f"-c{chunk_number:03d}"
                    ),
                    content=chunk,
                    metadata=document_metadata,
                )
            )

    indexed_count = 0

    for start in range(0, len(documents), batch_size):
        batch = documents[start:start + batch_size]
        indexed_count += index_documents(batch)

    return {
        "source_id": source_id,
        "checksum_sha256": checksum,
        "pages_with_text": len(pages),
        "chunks_indexed": indexed_count,
        "source_url": source_url,
    }