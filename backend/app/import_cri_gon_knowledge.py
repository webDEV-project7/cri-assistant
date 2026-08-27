import argparse
import json
from pathlib import Path
from typing import Any, Iterator

from app.rag import (
    SourceDocument,
    index_documents,
    validate_document,
)


DEFAULT_SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "knowledge"
    / "cri_gon_creation_entreprise.json"
)


def load_snapshot(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Snapshot introuvable : {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        snapshot = json.load(handle)

    if not isinstance(snapshot, dict):
        raise ValueError(
            "Le snapshot doit etre un objet JSON."
        )

    documents = snapshot.get("documents")

    if not isinstance(documents, list):
        raise ValueError(
            "Le champ documents doit etre une liste."
        )

    if not documents:
        raise ValueError(
            "Le snapshot ne contient aucun document."
        )

    return snapshot


def build_documents(
    snapshot: dict[str, Any],
) -> list[SourceDocument]:
    raw_documents = snapshot["documents"]

    documents: list[SourceDocument] = []
    seen_ids: set[str] = set()

    for position, item in enumerate(
        raw_documents,
        start=1,
    ):
        if not isinstance(item, dict):
            raise ValueError(
                "Document invalide a la position "
                f"{position}."
            )

        document_id = str(
            item.get("id") or ""
        ).strip()

        content = str(
            item.get("content") or ""
        ).strip()

        metadata = item.get("metadata")

        if not document_id:
            raise ValueError(
                "Identifiant manquant a la position "
                f"{position}."
            )

        if not content:
            raise ValueError(
                f"Contenu vide : {document_id}"
            )

        if not isinstance(metadata, dict):
            raise ValueError(
                f"Metadonnees invalides : {document_id}"
            )

        if document_id in seen_ids:
            raise ValueError(
                f"Identifiant duplique : {document_id}"
            )

        seen_ids.add(document_id)

        if not document_id.startswith(
            "cri-gon-"
        ):
            raise ValueError(
                "Identifiant hors espace CRI GON : "
                f"{document_id}"
            )

        document = SourceDocument(
            id=document_id,
            content=content,
            metadata=metadata,
        )

        validate_document(document)

        documents.append(document)

    return documents


def batches(
    documents: list[SourceDocument],
    batch_size: int,
) -> Iterator[list[SourceDocument]]:
    for start in range(
        0,
        len(documents),
        batch_size,
    ):
        yield documents[
            start:start + batch_size
        ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Importe un snapshot de connaissances "
            "officielles CRI Guelmim-Oued Noun."
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Valide le snapshot sans modifier ChromaDB."
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help=(
            "Nombre de fragments indexes par lot."
        ),
    )

    parser.add_argument(
        "--snapshot",
        type=Path,
        default=DEFAULT_SNAPSHOT_PATH,
        help=(
            "Chemin du snapshot JSON."
        ),
    )

    args = parser.parse_args()

    if (
        args.batch_size < 1
        or args.batch_size > 32
    ):
        raise ValueError(
            "--batch-size doit etre compris "
            "entre 1 et 32."
        )

    snapshot = load_snapshot(
        args.snapshot
    )

    documents = build_documents(
        snapshot
    )

    print(
        "DATASET =",
        snapshot.get("dataset_id"),
    )

    print(
        "SNAPSHOT =",
        args.snapshot,
    )

    print(
        "DOCUMENTS PREPARES =",
        len(documents),
    )

    for document in documents:
        metadata = document.metadata

        print(
            "[PREPARE]",
            document.id,
            "| category =",
            metadata.get("category"),
            "| section =",
            metadata.get("section"),
        )

    if args.dry_run:
        print()
        print(
            "DRY_RUN=OK"
        )

        print(
            "ChromaDB n'a pas ete modifiee."
        )

        return

    indexed_count = 0

    for document_batch in batches(
        documents,
        args.batch_size,
    ):
        indexed_count += index_documents(
            document_batch
        )

    print()
    print(
        "DOCUMENTS INDEXES =",
        indexed_count,
    )

    print(
        "IMPORT_CRI_GON=OK"
    )


if __name__ == "__main__":
    main()