from __future__ import annotations

import argparse
import os
import re
from datetime import date
from typing import Any

import httpx

from app.rag import (
    SourceDocument,
    extract_legal_references,
    index_documents,
)
from app.vector_store import get_documents_collection


PROCEDURES_API_URL = os.getenv(
    "CRI_PROCEDURES_API_URL",
    "https://www.cri-invest.ma/backend/api/procedures",
)

PROCEDURE_PUBLIC_URL = (
    "https://www.cri-invest.ma/procedures/{procedure_id}"
)

MAX_CHUNK_CHARACTERS = 3500
CHUNK_OVERLAP = 250

SECTION_LISTS = (
    (
        "required_documents",
        "Pièces obligatoires",
        "requiredDocuments",
    ),
    (
        "complementary_documents",
        "Pièces complémentaires",
        "requiredComplementaryDocuments",
    ),
    (
        "deprecated_documents",
        "Pièces anciennes ou obsolètes",
        "deprecatedDocuments",
    ),
    (
        "required_information",
        "Informations requises",
        "requiredInfos",
    ),
    (
        "procedure_milestones",
        "Étapes de la procédure",
        "procedureMilestones",
    ),
)

FIELD_LABELS = {
    "name": "Nom",
    "value": "Valeur",
    "description": "Description",
    "orientation": "Orientation",
    "required": "Obligatoire",
    "deliveredByAdministration": (
        "Fourni par l’administration"
    ),
    "relevantInvestorType": (
        "Type d’investisseur concerné"
    ),
    "documentCollectionFee": "Frais de collecte",
    "templateName": "Nom du modèle",
    "templateTitle": "Intitulé du modèle",
    "order": "Ordre",
    "duration": "Durée",
    "delay": "Délai",
    "administration": "Administration",
    "administrations": "Administrations",
    "maxSchedulingDelay": (
        "Délai maximal de programmation"
    ),
    "paymentDelay": "Délai de paiement",
    "administrationResponseDelay": (
        "Délai de réponse de l’administration"
    ),
}

IGNORED_FIELDS = {
    "id",
    "code",
    "templateFile",
    "timelineImageName",
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).replace("\r\n", "\n").replace(
        "\r",
        "\n",
    )

    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.split("\n")
    ]

    return "\n".join(
        line
        for line in lines
        if line
    ).strip()


def value_to_text(value: Any) -> str:
    if isinstance(value, bool):
        return "Oui" if value else "Non"

    if isinstance(value, dict):
        parts = []

        for key, nested_value in value.items():
            if (
                key in IGNORED_FIELDS
                or nested_value in (None, "", [], {})
            ):
                continue

            label = FIELD_LABELS.get(key, key)
            formatted = value_to_text(nested_value)

            if formatted:
                parts.append(f"{label} : {formatted}")

        return "; ".join(parts)

    if isinstance(value, list):
        return " | ".join(
            formatted
            for item in value
            if (formatted := value_to_text(item))
        )

    return clean_text(value)


def format_items(items: Any) -> str:
    if not isinstance(items, list):
        return value_to_text(items)

    blocks: list[str] = []

    for position, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            text = value_to_text(item)

            if text:
                blocks.append(f"{position}. {text}")

            continue

        heading_key = next(
            (
                key
                for key in (
                    "name",
                    "value",
                    "title",
                    "description",
                )
                if clean_text(item.get(key))
            ),
            None,
        )

        heading = (
            clean_text(item.get(heading_key))
            if heading_key
            else f"Élément {position}"
        )

        lines = [f"{position}. {heading}"]

        for key, value in item.items():
            if (
                key in IGNORED_FIELDS
                or key == heading_key
                or value in (None, "", [], {})
            ):
                continue

            formatted = value_to_text(value)

            if not formatted or formatted == heading:
                continue

            label = FIELD_LABELS.get(key, key)
            lines.append(f"   - {label} : {formatted}")

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def split_text(
    text: str,
    max_characters: int = MAX_CHUNK_CHARACTERS,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    normalized = clean_text(text)

    if not normalized:
        return []

    if len(normalized) <= max_characters:
        return [normalized]

    chunks: list[str] = []
    start = 0
    text_length = len(normalized)

    while start < text_length:
        end = min(
            start + max_characters,
            text_length,
        )

        if end < text_length:
            search_start = start + max_characters // 2

            cut_positions = [
                normalized.rfind(
                    separator,
                    search_start,
                    end,
                )
                for separator in (
                    "\n",
                    ". ",
                    "; ",
                    " ",
                )
            ]

            cut_position = max(cut_positions)

            if cut_position > start:
                end = cut_position + 1

        chunk = normalized[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        next_start = max(
            end - overlap,
            start + 1,
        )

        while (
            next_start < text_length
            and normalized[next_start].isspace()
        ):
            next_start += 1

        start = next_start

    return chunks


def format_procedure_milestones(
    items: Any,
) -> str:
    if not isinstance(items, list):
        return value_to_text(items)

    milestones = [
        item
        for item in items
        if isinstance(item, dict)
    ]

    def milestone_order(
        milestone: dict[str, Any],
    ) -> int:
        try:
            return int(
                milestone.get("orderMilestone")
            )
        except (TypeError, ValueError):
            return 10**9

    milestones.sort(key=milestone_order)

    if not milestones:
        return ""

    names = {
        clean_text(milestone.get("name"))
        for milestone in milestones
        if clean_text(milestone.get("name"))
    }

    lines = [
        (
            "Nombre de jalons déclarés par "
            f"le portail : {len(milestones)}"
        )
    ]

    if len(names) == 1 and len(milestones) > 1:
        shared_name = next(iter(names))

        lines.append(
            "Remarque : les informations officielles "
            "attribuent le même intitulé aux différents "
            f"jalons : « {shared_name} »."
        )

    grouped: list[dict[str, Any]] = []

    for position, milestone in enumerate(
        milestones,
        start=1,
    ):
        order_value = milestone.get(
            "orderMilestone"
        )

        order = (
            order_value
            if order_value is not None
            else position
        )

        name = (
            clean_text(milestone.get("name"))
            or "Jalon sans intitulé"
        )

        day_number = milestone.get("dayNumber")

        key = (
            name,
            (
                str(day_number)
                if day_number is not None
                else None
            ),
        )

        if grouped and grouped[-1]["key"] == key:
            grouped[-1]["orders"].append(order)
            continue

        grouped.append(
            {
                "key": key,
                "orders": [order],
                "name": name,
                "day_number": day_number,
            }
        )

    lines.append("")

    for group in grouped:
        orders = group["orders"]
        name = group["name"]
        day_number = group["day_number"]
        occurrence_count = len(orders)

        if occurrence_count == 1:
            order_label = str(orders[0])
        else:
            order_label = (
                f"{orders[0]} à {orders[-1]}"
            )

        lines.append(
            f"{order_label}. {name}"
        )

        if occurrence_count > 1:
            lines.append(
                "   - Ce même intitulé couvre "
                f"{occurrence_count} jalons consécutifs."
            )

        if day_number is not None:
            delay_text = (
                "1 jour"
                if str(day_number).strip() == "1"
                else f"{day_number} jours"
            )

            if occurrence_count > 1:
                lines.append(
                    "   - Délai indicatif indiqué pour "
                    f"chacun de ces jalons : {delay_text}"
                )
            else:
                lines.append(
                    "   - Délai indicatif de l’étape : "
                    f"{delay_text}"
                )

    return "\n".join(lines)

def get_category(procedure: dict[str, Any]) -> str:
    category = procedure.get("category")

    if isinstance(category, dict):
        return (
            clean_text(category.get("value"))
            or "Non précisée"
        )

    return clean_text(category) or "Non précisée"


def build_sections(
    procedure: dict[str, Any],
) -> list[tuple[str, str, str]]:
    name = clean_text(procedure.get("name"))
    category = get_category(procedure)

    presentation = [
        f"Nom officiel : {name}",
        f"Catégorie : {category}",
    ]

    description = clean_text(
        procedure.get("description")
    )

    if description:
        presentation.append(
            f"Description : {description}"
        )

    if procedure.get("incitation") is not None:
        presentation.append(
            "Procédure liée à une incitation : "
            + value_to_text(
                procedure.get("incitation")
            )
        )

    delay_fields = (
        "maxSchedulingDelay",
        "paymentDelay",
        "administrationResponseDelay",
    )

    for field in delay_fields:
        value = procedure.get(field)

        if value is None:
            continue

        label = FIELD_LABELS[field]

        if (
            field in {
                "maxSchedulingDelay",
                "administrationResponseDelay",
            }
            and isinstance(value, int)
            and not isinstance(value, bool)
        ):
            delay_text = (
                f"{value} jour"
                if value == 1
                else f"{value} jours"
            )
        else:
            delay_text = value_to_text(value)

        presentation.append(
            f"{label} : {delay_text}"
        )

    region = procedure.get("region")

    if region not in (None, "", [], {}):
        presentation.append(
            f"Région : {value_to_text(region)}"
        )

    sections = [
        (
            "presentation",
            "Présentation générale",
            "\n".join(presentation),
        )
    ]

    legal_context = clean_text(
        procedure.get("legalContext")
    )

    if legal_context:
        sections.append(
            (
                "legal_context",
                "Contexte juridique",
                legal_context,
            )
        )

    for slug, title, api_field in SECTION_LISTS:
        value = procedure.get(api_field)

        if value in (None, "", [], {}):
            continue

        formatted = (
            format_procedure_milestones(value)
            if api_field == "procedureMilestones"
            else format_items(value)
        )

        if formatted:
            sections.append(
                (
                    slug,
                    title,
                    formatted,
                )
            )

    return sections


def build_documents(
    procedure: dict[str, Any],
) -> list[SourceDocument]:
    procedure_id = int(procedure["id"])
    name = clean_text(procedure.get("name"))

    if not name:
        raise ValueError(
            f"La procédure {procedure_id} n’a pas de nom"
        )

    category = get_category(procedure)
    public_url = PROCEDURE_PUBLIC_URL.format(
        procedure_id=procedure_id
    )

    legal_context = clean_text(
        procedure.get("legalContext")
    )

    legal_references = " ".join(
        sorted(
            extract_legal_references(
                legal_context
            )
        )
    ) or "Non précisée"

    documents: list[SourceDocument] = []

    for section_slug, section_title, section_text in (
        build_sections(procedure)
    ):
        chunks = split_text(section_text)
        chunk_count = len(chunks)

        for chunk_index, chunk in enumerate(
            chunks,
            start=1,
        ):
            document_id = (
                f"cri-procedure-{procedure_id}-"
                f"{section_slug}-{chunk_index:03d}"
            )

            content = (
                "Source officielle : Portail CRI Invest\n"
                f"Procédure : {name}\n"
                f"Catégorie : {category}\n"
                f"Section : {section_title}\n\n"
                f"{chunk}"
            )

            metadata = {
                "source_title": (
                    f"CRI Invest – {name}"
                ),
                "source_url": public_url,
                "authority": "CRI Invest Maroc",
                "document_type": (
                    "Procédure administrative officielle"
                ),
                "publication_date": (
                    "Non précisée par l’API"
                ),
                "language": "fr",
                "source_kind": "cri_procedure",
                "procedure_id": procedure_id,
                "procedure_name": name,
                "category": category,
                "section": section_slug,
                "section_title": section_title,
                "chunk_index": chunk_index,
                "chunk_count": chunk_count,
                "legal_reference": legal_references,
                "archived": False,
                "retrieval_date": date.today().isoformat(),
            }

            documents.append(
                SourceDocument(
                    id=document_id,
                    content=content,
                    metadata=metadata,
                )
            )

    return documents


def fetch_procedures() -> list[dict[str, Any]]:
    certificate_bundle = os.getenv(
        "CRI_INVEST_CA_BUNDLE"
    )

    if not certificate_bundle:
        raise RuntimeError(
            "CRI_INVEST_CA_BUNDLE n’est pas défini"
        )

    if not os.path.isfile(certificate_bundle):
        raise RuntimeError(
            "Le bundle SSL CRI Invest est introuvable : "
            f"{certificate_bundle}"
        )

    with httpx.Client(
        verify=certificate_bundle,
        follow_redirects=True,
        timeout=120,
        trust_env=False,
        headers={
            "Accept": "application/json",
            "Accept-Language": "fr",
            "User-Agent": "CRI-Assistant/1.0",
        },
    ) as client:
        response = client.get(PROCEDURES_API_URL)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, list):
        raise RuntimeError(
            "L’API CRI Invest n’a pas retourné une liste"
        )

    procedures = [
        procedure
        for procedure in payload
        if isinstance(procedure, dict)
        and procedure.get("id") is not None
    ]

    procedures.sort(
        key=lambda procedure: int(
            procedure["id"]
        )
    )

    return procedures


def remove_old_chunks(
    procedure_id: int,
    current_ids: set[str],
) -> int:
    collection = get_documents_collection()

    result = collection.get(
        where={"procedure_id": procedure_id},
        include=["metadatas"],
    )

    ids = result.get("ids") or []
    metadatas = result.get("metadatas") or []

    stale_ids = []

    for document_id, metadata in zip(
        ids,
        metadatas,
    ):
        metadata = metadata or {}

        if (
            metadata.get("source_kind")
            == "cri_procedure"
            and document_id not in current_ids
        ):
            stale_ids.append(document_id)

    if stale_ids:
        collection.delete(ids=stale_ids)

    return len(stale_ids)


def remove_inactive_procedures(
    active_procedure_ids: set[int],
) -> int:
    collection = get_documents_collection()

    result = collection.get(
        where={"source_kind": "cri_procedure"},
        include=["metadatas"],
    )

    ids = result.get("ids") or []
    metadatas = result.get("metadatas") or []

    stale_ids = []

    for document_id, metadata in zip(
        ids,
        metadatas,
    ):
        metadata = metadata or {}
        procedure_id = metadata.get("procedure_id")

        try:
            procedure_id = int(procedure_id)
        except (TypeError, ValueError):
            procedure_id = None

        if procedure_id not in active_procedure_ids:
            stale_ids.append(document_id)

    if stale_ids:
        collection.delete(ids=stale_ids)

    return len(stale_ids)


def batches(
    documents: list[SourceDocument],
    batch_size: int,
):
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
            "Importe les procédures officielles "
            "CRI Invest dans ChromaDB"
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Prépare les fragments sans les indexer"
        ),
    )

    parser.add_argument(
        "--procedure-id",
        type=int,
        help=(
            "Limite l’import à une procédure"
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help=(
            "Nombre de fragments vectorisés par lot"
        ),
    )

    args = parser.parse_args()

    if args.batch_size < 1 or args.batch_size > 32:
        raise ValueError(
            "--batch-size doit être compris entre 1 et 32"
        )

    procedures = fetch_procedures()

    if args.procedure_id is not None:
        procedures = [
            procedure
            for procedure in procedures
            if int(procedure["id"])
            == args.procedure_id
        ]

        if not procedures:
            raise ValueError(
                "Procédure introuvable : "
                f"{args.procedure_id}"
            )

    archived_count = sum(
        1
        for procedure in procedures
        if procedure.get("archived") is True
    )

    active_procedures = [
        procedure
        for procedure in procedures
        if procedure.get("archived") is not True
    ]

    prepared: list[
        tuple[
            dict[str, Any],
            list[SourceDocument],
        ]
    ] = []

    total_chunks = 0

    for procedure in active_procedures:
        documents = build_documents(procedure)
        prepared.append((procedure, documents))
        total_chunks += len(documents)

        print(
            f"[PRÉPARÉE] ID={procedure['id']} | "
            f"{procedure.get('name')} | "
            f"{len(documents)} fragments"
        )

    print()
    print("Procédures reçues :", len(procedures))
    print(
        "Procédures archivées exclues :",
        archived_count,
    )
    print(
        "Procédures actives préparées :",
        len(active_procedures),
    )
    print("Nombre total de fragments :", total_chunks)

    if args.dry_run:
        print()
        print(
            "Test à blanc terminé : "
            "ChromaDB n’a pas été modifiée."
        )
        return

    indexed_count = 0
    removed_count = 0
    active_ids: set[int] = set()

    for procedure, documents in prepared:
        procedure_id = int(procedure["id"])
        active_ids.add(procedure_id)

        for document_batch in batches(
            documents,
            args.batch_size,
        ):
            indexed_count += index_documents(
                document_batch
            )

        removed_count += remove_old_chunks(
            procedure_id,
            {
                document.id
                for document in documents
            },
        )

        print(
            f"[INDEXÉE] ID={procedure_id} | "
            f"{len(documents)} fragments"
        )

    if args.procedure_id is None:
        removed_count += remove_inactive_procedures(
            active_ids
        )

    print()
    print("Import terminé.")
    print("Fragments indexés :", indexed_count)
    print(
        "Anciens fragments supprimés :",
        removed_count,
    )
    print(
        "Documents présents dans ChromaDB :",
        get_documents_collection().count(),
    )


if __name__ == "__main__":
    main()
