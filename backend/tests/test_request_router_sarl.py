import asyncio
import json
from typing import Any

import app.request_router as request_router
from app.request_router import (
    RoutageDemande,
    analyser_demande,
    normaliser,
)


OLLAMA_BASE_URL = "http://ollama.test"
OLLAMA_MODEL = "qwen3:8b"

SARL_CLARIFICATION_HISTORY = [
    {
        "role": "user",
        "content": "Je souhaite créer une SARL.",
    },
    {
        "role": "assistant",
        "content": (
            "Souhaitez-vous créer :\n"
            "1. une SARL à associé unique (SARL AU) ;\n"
            "2. une SARL avec plusieurs associés ?"
        ),
    },
]


def install_router_response(
    monkeypatch,
    payload: dict[str, Any],
) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "message": {
                    "content": json.dumps(
                        payload,
                        ensure_ascii=False,
                    )
                }
            }

    class FakeAsyncClient:
        def __init__(
            self,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            pass

        async def __aenter__(
            self,
        ) -> "FakeAsyncClient":
            return self

        async def __aexit__(
            self,
            exc_type: Any,
            exc_value: Any,
            traceback: Any,
        ) -> bool:
            return False

        async def post(
            self,
            *args: Any,
            **kwargs: Any,
        ) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(
        request_router.httpx,
        "AsyncClient",
        FakeAsyncClient,
    )


def route(
    message: str,
    history: list[dict[str, str]],
) -> RoutageDemande:
    return asyncio.run(
        analyser_demande(
            message=message,
            history=history,
            ollama_base_url=OLLAMA_BASE_URL,
            ollama_model=OLLAMA_MODEL,
        )
    )


def test_generic_sarl_request_requires_clarification(
    monkeypatch,
) -> None:
    install_router_response(
        monkeypatch,
        {
            "action": "search",
            "category": "general",
            "standalone_query": (
                "Procédure de création d'une SARL en France."
            ),
            "clarification": "",
        },
    )

    result = route(
        "Je veux créer une SARL",
        [],
    )

    assert result.action == "clarify"
    assert result.category == "entreprise"
    assert result.standalone_query == ""

    assert (
        "SARL à associé unique"
        in result.clarification
    )

    assert (
        "SARL avec plusieurs associés"
        in result.clarification
    )


def test_explicit_sarl_unique_routes_to_morocco(
    monkeypatch,
) -> None:
    install_router_response(
        monkeypatch,
        {
            "action": "search",
            "category": "general",
            "standalone_query": (
                "Créer une SASU en France."
            ),
            "clarification": "",
        },
    )

    result = route(
        "Je veux créer une SARL AU",
        [],
    )

    normalized_query = normaliser(
        result.standalone_query
    )

    assert result.action == "search"
    assert result.category == "entreprise"
    assert result.clarification == ""

    assert "maroc" in normalized_query

    assert (
        "responsabilite limitee"
        in normalized_query
    )

    assert (
        "associe unique"
        in normalized_query
    )

    assert "france" not in normalized_query

    assert (
        "actions simplifiee"
        not in normalized_query
    )


def test_first_choice_routes_to_sarl_unique(
    monkeypatch,
) -> None:
    install_router_response(
        monkeypatch,
        {
            "action": "clarify",
            "category": "general",
            "standalone_query": "",
            "clarification": (
                "Veuillez préciser votre demande."
            ),
        },
    )

    result = route(
        "1",
        SARL_CLARIFICATION_HISTORY,
    )

    normalized_query = normaliser(
        result.standalone_query
    )

    assert result.action == "search"
    assert result.category == "entreprise"
    assert result.clarification == ""

    assert "maroc" in normalized_query

    assert (
        "responsabilite limitee"
        in normalized_query
    )

    assert (
        "associe unique"
        in normalized_query
    )


def test_second_choice_routes_to_multi_associate_sarl(
    monkeypatch,
) -> None:
    install_router_response(
        monkeypatch,
        {
            "action": "clarify",
            "category": "general",
            "standalone_query": "",
            "clarification": (
                "Veuillez préciser votre demande."
            ),
        },
    )

    result = route(
        "2",
        SARL_CLARIFICATION_HISTORY,
    )

    normalized_query = normaliser(
        result.standalone_query
    )

    assert result.action == "search"
    assert result.category == "entreprise"
    assert result.clarification == ""

    assert "maroc" in normalized_query

    assert (
        "responsabilite limitee"
        in normalized_query
    )

    assert (
        "plusieurs associes"
        in normalized_query
    )


def test_explicit_multi_associate_sarl_routes_to_search(
    monkeypatch,
) -> None:
    install_router_response(
        monkeypatch,
        {
            "action": "search",
            "category": "general",
            "standalone_query": (
                "Créer une entreprise en France."
            ),
            "clarification": "",
        },
    )

    result = route(
        "Créer une SARL avec plusieurs associés",
        [],
    )

    normalized_query = normaliser(
        result.standalone_query
    )

    assert result.action == "search"
    assert result.category == "entreprise"
    assert result.clarification == ""

    assert "maroc" in normalized_query

    assert (
        "responsabilite limitee"
        in normalized_query
    )

    assert (
        "plusieurs associes"
        in normalized_query
    )

    assert "france" not in normalized_query