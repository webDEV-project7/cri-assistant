import asyncio

from app import main


def test_embedding_warmup_calls_embedding(monkeypatch):
    calls = []

    def fake_generate_embedding(text):
        calls.append(text)
        return [0.1, 0.2, 0.3]

    async def fake_run_in_threadpool(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(
        main,
        "generate_embedding",
        fake_generate_embedding,
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "run_in_threadpool",
        fake_run_in_threadpool,
    )

    asyncio.run(main.warmup_embedding_model())

    assert calls == [main.EMBEDDING_WARMUP_TEXT]


def test_embedding_warmup_failure_is_non_blocking(monkeypatch):
    def failing_generate_embedding(text):
        raise RuntimeError("Ollama indisponible")

    async def fake_run_in_threadpool(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(
        main,
        "generate_embedding",
        failing_generate_embedding,
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "run_in_threadpool",
        fake_run_in_threadpool,
    )

    asyncio.run(main.warmup_embedding_model())