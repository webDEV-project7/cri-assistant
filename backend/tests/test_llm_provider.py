import asyncio

from app import llm_provider
from app.llm_provider import LLMResult


MESSAGES = [
    {
        "role": "user",
        "content": "Bonjour",
    }
]


def run_provider():
    return asyncio.run(
        llm_provider.generate_chat_response(
            messages=MESSAGES,
            ollama_base_url="http://ollama:11434",
            ollama_model="qwen3:8b",
            ollama_context_size=8192,
            max_response_tokens=200,
            temperature=0.1,
        )
    )


def test_groq_is_used_as_primary_provider(
    monkeypatch,
):
    calls = []

    async def fake_groq(**kwargs):
        calls.append("groq")

        return LLMResult(
            content="Réponse Groq",
            model="groq-test-model",
            provider="groq",
        )

    async def fake_ollama(**kwargs):
        calls.append("ollama")

        return LLMResult(
            content="Réponse Ollama",
            model="ollama-test-model",
            provider="ollama",
        )

    monkeypatch.setenv(
        "LLM_PROVIDER",
        "groq",
    )

    monkeypatch.setenv(
        "LLM_FALLBACK_PROVIDER",
        "ollama",
    )

    monkeypatch.setattr(
        llm_provider,
        "_call_groq",
        fake_groq,
    )

    monkeypatch.setattr(
        llm_provider,
        "_call_ollama",
        fake_ollama,
    )

    result = run_provider()

    assert result.content == "Réponse Groq"
    assert result.provider == "groq"
    assert calls == ["groq"]


def test_ollama_is_used_when_groq_fails(
    monkeypatch,
):
    calls = []

    async def failing_groq(**kwargs):
        calls.append("groq")
        raise RuntimeError("Groq indisponible")

    async def fake_ollama(**kwargs):
        calls.append("ollama")

        return LLMResult(
            content="Réponse de secours",
            model="qwen3:8b",
            provider="ollama",
        )

    monkeypatch.setenv(
        "LLM_PROVIDER",
        "groq",
    )

    monkeypatch.setenv(
        "LLM_FALLBACK_PROVIDER",
        "ollama",
    )

    monkeypatch.setattr(
        llm_provider,
        "_call_groq",
        failing_groq,
    )

    monkeypatch.setattr(
        llm_provider,
        "_call_ollama",
        fake_ollama,
    )

    result = run_provider()

    assert result.content == "Réponse de secours"
    assert result.provider == "ollama"
    assert calls == ["groq", "ollama"]


def test_ollama_can_remain_primary(
    monkeypatch,
):
    calls = []

    async def fake_ollama(**kwargs):
        calls.append("ollama")

        return LLMResult(
            content="Réponse locale",
            model="qwen3:8b",
            provider="ollama",
        )

    monkeypatch.setenv(
        "LLM_PROVIDER",
        "ollama",
    )

    monkeypatch.setenv(
        "LLM_FALLBACK_PROVIDER",
        "ollama",
    )

    monkeypatch.setattr(
        llm_provider,
        "_call_ollama",
        fake_ollama,
    )

    result = run_provider()

    assert result.content == "Réponse locale"
    assert result.provider == "ollama"
    assert calls == ["ollama"]

def test_deepseek_is_used_as_primary_provider(
    monkeypatch,
):
    calls = []

    async def fake_deepseek(**kwargs):
        calls.append("deepseek")

        return LLMResult(
            content="Reponse DeepSeek",
            model="deepseek-v4-pro",
            provider="deepseek",
        )

    async def fake_ollama(**kwargs):
        calls.append("ollama")

        return LLMResult(
            content="Reponse Ollama",
            model="qwen3:8b",
            provider="ollama",
        )

    monkeypatch.setenv(
        "LLM_PROVIDER",
        "deepseek",
    )

    monkeypatch.setenv(
        "LLM_FALLBACK_PROVIDER",
        "ollama",
    )

    monkeypatch.setattr(
        llm_provider,
        "_call_deepseek",
        fake_deepseek,
        raising=False,
    )

    monkeypatch.setattr(
        llm_provider,
        "_call_ollama",
        fake_ollama,
    )

    result = run_provider()

    assert result.content == "Reponse DeepSeek"
    assert result.provider == "deepseek"
    assert result.model == "deepseek-v4-pro"
    assert calls == ["deepseek"]


def test_ollama_is_used_when_deepseek_fails(
    monkeypatch,
):
    calls = []

    async def failing_deepseek(**kwargs):
        calls.append("deepseek")
        raise RuntimeError("DeepSeek indisponible")

    async def fake_ollama(**kwargs):
        calls.append("ollama")

        return LLMResult(
            content="Reponse de secours",
            model="qwen3:8b",
            provider="ollama",
        )

    monkeypatch.setenv(
        "LLM_PROVIDER",
        "deepseek",
    )

    monkeypatch.setenv(
        "LLM_FALLBACK_PROVIDER",
        "ollama",
    )

    monkeypatch.setattr(
        llm_provider,
        "_call_deepseek",
        failing_deepseek,
        raising=False,
    )

    monkeypatch.setattr(
        llm_provider,
        "_call_ollama",
        fake_ollama,
    )

    result = run_provider()

    assert result.content == "Reponse de secours"
    assert result.provider == "ollama"
    assert calls == ["deepseek", "ollama"]

def test_deepseek_logs_response_usage(
    monkeypatch,
    caplog,
):
    class FakeResponse:
        is_error = False
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "model": "deepseek-v4-pro",
                "choices": [
                    {
                        "message": {
                            "content": "Reponse test",
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 2500,
                    "completion_tokens": 320,
                    "total_tokens": 2820,
                },
            }

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

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

    monkeypatch.setenv(
        "DEEPSEEK_API_KEY",
        "test-key",
    )
    monkeypatch.setenv(
        "DEEPSEEK_MODEL",
        "deepseek-v4-pro",
    )

    monkeypatch.setattr(
        llm_provider.httpx,
        "AsyncClient",
        FakeAsyncClient,
    )

    with caplog.at_level("WARNING"):
        result = asyncio.run(
            llm_provider._call_deepseek(
                messages=MESSAGES,
                max_tokens=200,
                temperature=0.1,
            )
        )

    assert result.provider == "deepseek"

    logs = caplog.text

    assert "DeepSeek diagnostic reponse" in logs
    assert "prompt_tokens=2500" in logs
    assert "completion_tokens=320" in logs
    assert "total_tokens=2820" in logs
    assert "duree=" in logs