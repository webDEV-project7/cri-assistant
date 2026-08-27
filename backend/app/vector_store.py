import os
from functools import lru_cache

import chromadb


CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_COLLECTION = os.getenv(
    "CHROMA_COLLECTION",
    "cri_documents",
)


@lru_cache(maxsize=1)
def get_chroma_client():
    return chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
    )


def check_vector_store() -> int:
    client = get_chroma_client()
    return client.heartbeat()


def get_documents_collection():
    client = get_chroma_client()

    return client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=None,
        metadata={
            "description": (
                "Documents officiels marocains utilisés "
                "par le système RAG de CRI Assistant"
            )
        },
    )