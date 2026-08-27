from app import rag


def test_query_embedding_cache_reuses_same_vectors(monkeypatch):
    calls = []

    def fake_generate_embeddings(texts):
        calls.append(list(texts))
        return [
            [float(index), float(len(text))]
            for index, text in enumerate(texts)
        ]

    monkeypatch.setattr(
        rag,
        "generate_embeddings",
        fake_generate_embeddings,
    )

    rag.clear_query_embedding_cache()

    queries = [
        "conditions dispositif tpme",
        "tpme conditions",
    ]

    first = rag.generate_query_embeddings(queries)
    second = rag.generate_query_embeddings(queries)

    assert first == second
    assert len(calls) == 1


def test_query_embedding_cache_preserves_cached_values(monkeypatch):
    calls = []

    def fake_generate_embeddings(texts):
        calls.append(list(texts))
        return [[1.0, 2.0, 3.0] for _ in texts]

    monkeypatch.setattr(
        rag,
        "generate_embeddings",
        fake_generate_embeddings,
    )

    rag.clear_query_embedding_cache()

    first = rag.generate_query_embeddings(
        ["question tpme"]
    )

    first[0][0] = 999.0

    second = rag.generate_query_embeddings(
        ["question tpme"]
    )

    assert second == [[1.0, 2.0, 3.0]]
    assert len(calls) == 1


def test_query_embedding_cache_distinguishes_queries(monkeypatch):
    calls = []

    def fake_generate_embeddings(texts):
        calls.append(list(texts))
        return [[float(len(text))] for text in texts]

    monkeypatch.setattr(
        rag,
        "generate_embeddings",
        fake_generate_embeddings,
    )

    rag.clear_query_embedding_cache()

    rag.generate_query_embeddings(
        ["question tpme"]
    )

    rag.generate_query_embeddings(
        ["question foncier"]
    )

    assert len(calls) == 2


def test_direct_document_embedding_remains_uncached(monkeypatch):
    calls = []

    def fake_generate_embeddings(texts):
        calls.append(list(texts))
        return [[1.0] for _ in texts]

    monkeypatch.setattr(
        rag,
        "generate_embeddings",
        fake_generate_embeddings,
    )

    rag.clear_query_embedding_cache()

    rag.generate_query_embeddings(
        ["question tpme"]
    )

    rag.generate_embeddings(
        ["document officiel tpme"]
    )

    assert calls == [
        ["question tpme"],
        ["document officiel tpme"],
    ]