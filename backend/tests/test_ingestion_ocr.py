import pymupdf
import pytest

import app.ingestion as ingestion
from app.ingestion import PdfIngestionError


def create_native_pdf(text: str) -> bytes:
    document = pymupdf.open()

    try:
        page = document.new_page(
            width=595,
            height=842,
        )
        page.insert_text(
            (72, 120),
            text,
            fontsize=18,
        )
        return document.tobytes()

    finally:
        document.close()


def create_scanned_image(text: str) -> bytes:
    document = pymupdf.open()

    try:
        page = document.new_page(
            width=595,
            height=842,
        )
        page.insert_text(
            (72, 120),
            text,
            fontsize=24,
        )
        pixmap = page.get_pixmap(
            dpi=200,
            alpha=False,
        )
        return pixmap.tobytes("png")

    finally:
        document.close()


def create_scanned_pdf(text: str) -> bytes:
    image_content = create_scanned_image(text)
    document = pymupdf.open()

    try:
        page = document.new_page(
            width=595,
            height=842,
        )
        page.insert_image(
            page.rect,
            stream=image_content,
        )
        return document.tobytes()

    finally:
        document.close()


def test_native_pdf_uses_native_text(monkeypatch):
    pdf_content = create_native_pdf(
        "DOCUMENT OFFICIEL DU CENTRE REGIONAL D INVESTISSEMENT"
    )

    def forbid_ocr(*args, **kwargs):
        raise AssertionError(
            "PyMuPDF ne doit pas être appelé "
            "pour un texte natif suffisant"
        )

    monkeypatch.setattr(
        ingestion.pymupdf,
        "open",
        forbid_ocr,
    )

    pages = ingestion.extract_pdf_pages(pdf_content)

    assert len(pages) == 1
    assert pages[0][0] == 1
    assert "DOCUMENT OFFICIEL" in pages[0][1]


def test_scanned_pdf_uses_ocr():
    pdf_content = create_scanned_pdf(
        "CENTRE REGIONAL D INVESTISSEMENT"
    )

    pages = ingestion.extract_pdf_pages(pdf_content)

    assert len(pages) == 1
    assert pages[0][0] == 1
    assert "CENTRE REGIONAL" in pages[0][1].upper()


def test_mixed_pdf_preserves_page_order():
    image_content = create_scanned_image(
        "SERVICE AUX INVESTISSEURS"
    )

    document = pymupdf.open()

    try:
        native_page = document.new_page(
            width=595,
            height=842,
        )
        native_page.insert_text(
            (72, 120),
            (
                "PREMIERE PAGE AVEC UN TEXTE OFFICIEL "
                "COMPLET ET EXPLOITABLE"
            ),
            fontsize=16,
        )

        scanned_page = document.new_page(
            width=595,
            height=842,
        )
        scanned_page.insert_image(
            scanned_page.rect,
            stream=image_content,
        )

        pdf_content = document.tobytes()

    finally:
        document.close()

    pages = ingestion.extract_pdf_pages(pdf_content)

    assert [number for number, _ in pages] == [1, 2]
    assert "PREMIERE PAGE" in pages[0][1]
    assert "SERVICE AUX" in pages[1][1].upper()


def test_empty_pdf_is_rejected():
    document = pymupdf.open()

    try:
        document.new_page(
            width=595,
            height=842,
        )
        pdf_content = document.tobytes()

    finally:
        document.close()

    with pytest.raises(
        PdfIngestionError,
        match="Aucun texte exploitable",
    ):
        ingestion.extract_pdf_pages(pdf_content)