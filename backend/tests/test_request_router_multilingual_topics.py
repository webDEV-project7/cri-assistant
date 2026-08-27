import asyncio
import json

from app import request_router
from app.request_router import (
    adapter_historique_au_dernier_message,
    analyser_demande,
    demande_est_trop_large,
    detecter_categorie_message,
    detecter_langue_message,
)


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "action": "clarify",
                        "category": "general",
                        "standalone_query": "",
                        "clarification": (
                            "Veuillez préciser votre demande."
                        ),
                    },
                    ensure_ascii=False,
                )
            }
        }


class FakeAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False

    async def post(self, *args, **kwargs):
        return FakeResponse()


def run_router(
    message,
    history,
):
    return asyncio.run(
        analyser_demande(
            message=message,
            history=history,
            ollama_base_url="http://ollama:11434",
            ollama_model="qwen3:8b",
        )
    )


def test_french_land_definition_is_not_too_broad():
    assert not demande_est_trop_large(
        "Qu'est-ce que le foncier ?"
    )

    assert (
        detecter_categorie_message(
            "Qu'est-ce que le foncier ?"
        )
        == "foncier"
    )


def test_arabic_land_definition_goes_to_search(
    monkeypatch,
):
    monkeypatch.setattr(
        request_router.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(),
    )

    result = run_router(
        "ما هو العقار المخصص للاستثمار؟",
        [],
    )

    assert result.action == "search"
    assert result.category == "foncier"
    assert "foncier" in result.standalone_query.lower()


def test_darija_incitation_definition_goes_to_search(
    monkeypatch,
):
    monkeypatch.setattr(
        request_router.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(),
    )

    history = [
        {
            "role": "user",
            "content": "ما هو العقار المخصص للاستثمار؟",
        },
        {
            "role": "assistant",
            "content": "العقار هو الأرض المخصصة للمشروع.",
        },
    ]

    result = run_router(
        "chno howa incitations",
        history,
    )

    assert detecter_langue_message(
        "chno howa incitations"
    ) == "ar"

    assert result.action == "search"
    assert result.category == "incitations"
    assert "incitations" in result.standalone_query.lower()


def test_new_explicit_topic_ignores_old_history():
    history = [
        {
            "role": "user",
            "content": "Parlez-moi du foncier.",
        },
        {
            "role": "assistant",
            "content": "Quelle procédure foncière ?",
        },
    ]

    assert (
        adapter_historique_au_dernier_message(
            "chno howa incitations",
            history,
        )
        == []
    )

    assert (
        adapter_historique_au_dernier_message(
            "1",
            history,
        )
        == history
    )

def test_autonomous_tpme_question_uses_fast_router_with_history():
    message = (
        "Quelles sont les conditions pour beneficier "
        "du dispositif TPME ?"
    )

    history = [
        {
            "role": "user",
            "content": message,
        },
        {
            "role": "assistant",
            "content": "Reponse precedente sur le dispositif TPME.",
        },
    ]

    result = request_router.essayer_routage_local_rapide(
        message,
        history,
    )

    assert result is not None
    assert result.action == "search"
    assert result.category == "incitations"
    assert result.standalone_query == message