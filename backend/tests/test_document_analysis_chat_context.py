import pytest
from pydantic import ValidationError

from app.main import ChatRequest


def test_chat_request_accepts_document_analysis_context():
    request = ChatRequest(
        message="Quelles pièces manquent ?",
        analysis_context=(
            "Score de complétude : 60%. "
            "Pièce manquante : plan de financement."
        ),
    )

    assert request.analysis_context is not None
    assert "plan de financement" in request.analysis_context


def test_chat_request_analysis_context_is_optional():
    request = ChatRequest(
        message="Quels sont les critères d'éligibilité ?",
    )

    assert request.analysis_context is None


def test_chat_request_rejects_oversized_analysis_context():
    with pytest.raises(ValidationError):
        ChatRequest(
            message="Analyse mon dossier.",
            analysis_context="x" * 12001,
        )
