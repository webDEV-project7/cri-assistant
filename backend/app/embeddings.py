import os

import httpx


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://ollama:11434",
).rstrip("/")

OLLAMA_EMBEDDING_MODEL = os.getenv(
    "OLLAMA_EMBEDDING_MODEL",
    "bge-m3",
)

OLLAMA_EMBEDDING_KEEP_ALIVE = os.getenv(
    "OLLAMA_EMBEDDING_KEEP_ALIVE",
    "30m",
)

EMBEDDING_TIMEOUT_SECONDS = 300.0


class EmbeddingError(RuntimeError):
    """Erreur lors de la génération d'embeddings avec Ollama."""


def generate_embeddings(
    texts: list[str],
) -> list[list[float]]:
    if not texts:
        return []

    normalized_texts = [
        text.strip()
        for text in texts
    ]

    if any(not text for text in normalized_texts):
        raise ValueError(
            "Les textes à vectoriser ne doivent pas être vides"
        )

    timeout = httpx.Timeout(
        timeout=EMBEDDING_TIMEOUT_SECONDS,
        connect=10.0,
    )

    try:
        with httpx.Client(
            timeout=timeout,
            trust_env=False,
        ) as client:
            response = client.post(
                f"{OLLAMA_BASE_URL}/api/embed",
                json={
                    "model": OLLAMA_EMBEDDING_MODEL,
                    "input": normalized_texts,
                    "keep_alive": OLLAMA_EMBEDDING_KEEP_ALIVE,
                },
            )

            response.raise_for_status()

    except httpx.HTTPError as error:
        raise EmbeddingError(
            "Impossible de générer les embeddings avec Ollama"
        ) from error

    try:
        payload = response.json()

    except ValueError as error:
        raise EmbeddingError(
            "La réponse Ollama n'est pas un JSON valide"
        ) from error

    embeddings = payload.get("embeddings")

    if not isinstance(embeddings, list):
        raise EmbeddingError(
            "La réponse Ollama ne contient pas d'embeddings valides"
        )

    if len(embeddings) != len(normalized_texts):
        raise EmbeddingError(
            "Le nombre d'embeddings retourné est incorrect"
        )

    return embeddings


def generate_embedding(
    text: str,
) -> list[float]:
    embeddings = generate_embeddings([text])
    return embeddings[0]