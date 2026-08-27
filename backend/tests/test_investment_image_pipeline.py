from __future__ import annotations

from types import SimpleNamespace

import pymupdf
import pytest

from app import investment_document_pipeline as pipeline


def create_test_image(
    image_format: str,
) -> bytes:
    document = pymupdf.open()

    try:
        page = document.new_page(
            width=500,
            height=220,
        )

        page.insert_text(
            (40, 90),
            "CARTE NATIONALE IDENTITE",
            fontsize=20,
        )

        page.insert_text(
            (40, 130),
            "DOCUMENT TEST OCR",
            fontsize=15,
        )

        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(2, 2),
        )

        return pixmap.tobytes(
            image_format
        )

    finally:
        document.close()


def test_png_is_converted_to_pdf_before_ocr(
    monkeypatch,
):
    captured = {}

    def fake_extract_pdf_pages(
        pdf_content: bytes,
    ):
        captured["pdf_content"] = pdf_content

        return [
            (
                1,
                "CARTE NATIONALE IDENTITE",
            )
        ]

    fake_classification = SimpleNamespace(
        status="classe",
        requirement_code="identity_document",
    )

    monkeypatch.setattr(
        pipeline,
        "extract_pdf_pages",
        fake_extract_pdf_pages,
    )

    monkeypatch.setattr(
        pipeline,
        "classify_document",
        lambda profile, document: fake_classification,
    )

    result = pipeline.process_investment_document(
        profile=object(),
        filename="cin_test.png",
        document_content=create_test_image("png"),
    )

    assert captured["pdf_content"].startswith(
        b"%PDF"
    )

    assert result.filename == "cin_test.png"
    assert result.page_count == 1

    assert (
        "CARTE NATIONALE"
        in result.extracted_text
    )


def test_jpeg_is_converted_to_pdf(
    monkeypatch,
):
    monkeypatch.setattr(
        pipeline,
        "extract_pdf_pages",
        lambda pdf_content: [
            (1, "PIECE IDENTITE")
        ],
    )

    monkeypatch.setattr(
        pipeline,
        "classify_document",
        lambda profile, document: SimpleNamespace(
            status="classe",
            requirement_code="identity_document",
        ),
    )

    result = pipeline.process_investment_document(
        profile=object(),
        filename="photo_cin.jpeg",
        document_content=create_test_image("jpeg"),
    )

    assert result.page_count == 1
    assert result.filename == "photo_cin.jpeg"


def test_unsupported_image_format_is_rejected():
    with pytest.raises(
        ValueError,
        match="Format non pris en charge",
    ):
        pipeline.process_investment_document(
            profile=object(),
            filename="document.gif",
            document_content=b"GIF89a",
        )
