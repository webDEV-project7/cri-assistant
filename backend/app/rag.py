import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.embeddings import generate_embeddings
from app.vector_store import get_documents_collection


MetadataValue = str | int | float | bool


@lru_cache(maxsize=256)
def _cached_query_embeddings(
    query_key: tuple[str, ...],
) -> tuple[tuple[float, ...], ...]:
    """
    Cache uniquement les embeddings des requêtes de recherche.

    L'indexation documentaire continue à appeler generate_embeddings()
    directement et n'est donc pas affectée par ce cache.
    """
    embeddings = generate_embeddings(list(query_key))

    return tuple(
        tuple(float(value) for value in embedding)
        for embedding in embeddings
    )


def generate_query_embeddings(
    texts: list[str],
) -> list[list[float]]:
    """
    Retourne les embeddings de recherche avec cache mémoire.

    Une copie mutable est retournée afin qu'un appelant ne puisse pas
    modifier les vecteurs conservés dans le cache.
    """
    query_key = tuple(
        text.strip()
        for text in texts
    )

    cached_embeddings = _cached_query_embeddings(query_key)

    return [
        list(embedding)
        for embedding in cached_embeddings
    ]


def clear_query_embedding_cache() -> None:
    """Vide explicitement le cache des embeddings de recherche."""
    _cached_query_embeddings.cache_clear()

REQUIRED_METADATA_FIELDS = {
    "source_title",
    "source_url",
    "authority",
    "document_type",
    "publication_date",
    "language",
}

STOP_WORDS = {
    "a",
    "au",
    "aux",
    "avec",
    "ce",
    "ces",
    "cette",
    "d",
    "dans",
    "de",
    "des",
    "du",
    "elle",
    "en",
    "est",
    "et",
    "il",
    "ils",
    "la",
    "le",
    "les",
    "leur",
    "leurs",
    "ne",
    "ou",
    "par",
    "pas",
    "pour",
    "que",
    "quel",
    "quelle",
    "quelles",
    "quels",
    "qui",
    "sont",
    "sur",
    "un",
    "une",
    "apres",
    "selon",
    "principales",
    "principal",
    "principaux",
    "loi",
    "dahir",
    "numero",
}

REFERENCE_PATTERN = re.compile(
    r"\b\d{1,3}\s*[-.]\s*\d{1,3}\b"
)

TOKEN_PATTERN = re.compile(
    r"[a-z0-9\u0600-\u06ff]+"
)


@dataclass(frozen=True)
class SourceDocument:
    id: str
    content: str
    metadata: dict[str, MetadataValue]


def normalize_search_text(text: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        text.lower(),
    )

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def extract_search_tokens(text: str) -> set[str]:
    normalized = normalize_search_text(text)
    tokens = TOKEN_PATTERN.findall(normalized)

    return {
        token
        for token in tokens
        if len(token) >= 2
        and token not in STOP_WORDS
        and not token.isdigit()
    }


def build_focused_query(text: str) -> str:
    normalized = normalize_search_text(text)
    tokens = TOKEN_PATTERN.findall(normalized)

    focused_tokens = [
        token
        for token in tokens
        if len(token) >= 2
        and token not in STOP_WORDS
        and not token.isdigit()
    ]

    return " ".join(focused_tokens)


def build_cri_legal_queries(
    text: str,
) -> list[str]:
    """
    Construit quelques variantes de recherche propres au domaine CRI.

    L'objectif n'est pas de produire une réponse juridique ici,
    mais d'améliorer le rappel documentaire en développant les
    abréviations et formulations courantes utilisées par les
    investisseurs.
    """

    normalized = normalize_search_text(text)
    tokens = set(TOKEN_PATTERN.findall(normalized))

    queries: list[str] = []

    def add(value: str) -> None:
        normalized_value = normalize_search_text(value)

        if (
            normalized_value
            and normalized_value
            != normalize_search_text(text)
            and all(
                normalize_search_text(existing)
                != normalized_value
                for existing in queries
            )
        ):
            queries.append(value)

    # CRUI : développer l'abréviation vers la terminologie
    # utilisée dans les textes officiels.
    if (
        "crui" in tokens
        or (
            "commission" in tokens
            and "regionale" in tokens
        )
    ):
        add(
            "commission regionale unifiee "
            "investissement commission regionale"
        )

    # AVNA.
    if (
        "avna" in tokens
        or (
            "vocation" in tokens
            and "agricole" in tokens
        )
    ):
        add(
            "attestation de vocation non agricole "
            "commission regionale investissement"
        )

    # Recours / refus de la Commission régionale.
    if (
        "recours" in tokens
        or "refus" in tokens
    ) and (
        "crui" in tokens
        or "commission" in tokens
        or "regionale" in tokens
    ):
        add(
            "decision refus investisseur recours "
            "commission regionale commission ministerielle"
        )

    # Délais de traitement / décision de la CRUI.
    if (
        "delai" in tokens
        or "delais" in tokens
    ) and (
        "crui" in tokens
        or "commission" in tokens
        or "regionale" in tokens
    ):
        add(
            "commission regionale decision "
            "delai maximum dossier investissement"
        )

    # Missions / rôle du CRI.
    if (
        "cri" in tokens
        or (
            "centre" in tokens
            and "regional" in tokens
        )
        or (
            "centres" in tokens
            and "regionaux" in tokens
        )
    ) and (
        "role" in tokens
        or "mission" in tokens
        or "missions" in tokens
        or "accompagnement" in tokens
        or "accompagner" in tokens
    ):
        add(
            "missions centres regionaux investissement "
            "accompagnement investisseurs entreprises"
        )

    # Dérogations en urbanisme.
    if (
        "derogation" in tokens
        or "derogations" in tokens
    ) and (
        "urbanisme" in tokens
        or "urbanistique" in tokens
    ):
        add(
            "commission regionale derogation urbanisme "
            "projet investissement"
        )

    # Acceptabilité / étude d'impact environnemental.
    if (
        "environnement" in tokens
        or "environnemental" in tokens
        or "environnementale" in tokens
        or "impact" in tokens
    ) and (
        "crui" in tokens
        or "commission" in tokens
        or "acceptabilite" in tokens
    ):
        add(
            "commission regionale etude impact environnement "
            "acceptabilite environnementale projet investissement"
        )

    # On limite volontairement les expansions pour conserver
    # un coût de recherche maîtrisé.
    return queries[:4]

def extract_legal_references(text: str) -> set[str]:
    normalized = normalize_search_text(text)

    references = REFERENCE_PATTERN.findall(normalized)

    return {
        re.sub(r"\s+", "", reference).replace(".", "-")
        for reference in references
    }


def validate_document(document: SourceDocument) -> None:
    if not document.id.strip():
        raise ValueError(
            "L'identifiant du document est obligatoire"
        )

    if not document.content.strip():
        raise ValueError(
            "Le contenu du document est obligatoire"
        )

    missing_fields = REQUIRED_METADATA_FIELDS.difference(
        document.metadata
    )

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))

        raise ValueError(
            f"Métadonnées obligatoires absentes : {missing}"
        )

    for field in REQUIRED_METADATA_FIELDS:
        value = document.metadata[field]

        if isinstance(value, str) and not value.strip():
            raise ValueError(
                f"La métadonnée '{field}' ne doit pas être vide"
            )


def index_documents(
    documents: list[SourceDocument],
) -> int:
    if not documents:
        return 0

    for document in documents:
        validate_document(document)

    ids = [document.id for document in documents]
    contents = [
        document.content.strip()
        for document in documents
    ]
    metadatas = [
        document.metadata
        for document in documents
    ]

    if len(ids) != len(set(ids)):
        raise ValueError(
            "Les identifiants des documents doivent être uniques"
        )

    embeddings = generate_embeddings(contents)
    collection = get_documents_collection()

    collection.upsert(
        ids=ids,
        documents=contents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(documents)


def _normaliser_reference_juridique(
    value: str,
) -> str:
    return (
        value.casefold()
        .replace("–", "-")
        .replace("—", "-")
        .replace(".", "-")
        .replace(" ", "")
    )


def _detecter_intention_incitation(
    query: str,
) -> str:
    normalized_query = normalize_search_text(query)

    # Une convention d'investissement avec l'Etat, lorsqu'aucun
    # dispositif specifique n'est mentionne, releve du contexte
    # general du dispositif principal. Cette priorite evite qu'une
    # ancienne presentation de la procedure prenne le dessus sur
    # les fragments officiels actualises du dispositif principal.
    if (
        (
            "convention d investissement" in normalized_query
            or "convention d'investissement" in normalized_query
        )
        and "tpme" not in normalized_query
        and "avenant" not in normalized_query
    ):
        return "general"

    query_tokens = set(
        extract_search_tokens(query)
    )

    normalized_reference = (
        _normaliser_reference_juridique(query)
    )

    support_terms = {
        "prime",
        "primes",
        "incitation",
        "incitations",
        "aide",
        "aides",
        "soutien",
        "subvention",
        "subventions",
    }

    has_support_context = bool(
        query_tokens.intersection(
            support_terms
        )
    )

    explicit_tpme = (
        bool(
            query_tokens.intersection(
                {
                    "tpme",
                    "pme",
                    "tpe",
                }
            )
        )
        or "2-25-342" in normalized_reference
    )

    explicit_principal = (
        "2-23-1" in normalized_reference
        or "principal" in query_tokens
        or bool(
            query_tokens.intersection(
                {
                    "commune",
                    "communes",
                    "sectorielle",
                    "sectorielles",
                }
            )
        )
    )

    comparison_terms = {
        "comparer",
        "comparaison",
        "difference",
        "differences",
        "distinction",
        "distinguer",
    }

    normalized_query = query.casefold()

    comparison_requested = (
        bool(
            query_tokens.intersection(
                comparison_terms
            )
        )
        or "les deux" in normalized_query
        or (
            explicit_tpme
            and explicit_principal
        )
    )

    if comparison_requested:
        return "comparison"

    if explicit_tpme:
        return "tpme"

    if explicit_principal:
        return "principal"

    if has_support_context:
        return "general"

    return "none"


def _classifier_dispositif_incitation(
    content: str,
    metadata: dict[str, Any],
) -> str:
    section = str(
        metadata.get("section", "")
    ).casefold().strip()

    title = str(
        metadata.get("source_title")
        or metadata.get("title")
        or metadata.get("procedure_name")
        or ""
    ).casefold()

    category = str(
        metadata.get("category", "")
    ).casefold()

    legal_reference = (
        _normaliser_reference_juridique(
            str(
                metadata.get(
                    "legal_reference",
                    "",
                )
            )
        )
    )

    normalized_content = (
        content[:2200].casefold()
    )

    normalized_content_reference = (
        _normaliser_reference_juridique(
            content[:2200]
        )
    )

    # L'avenant utilise aussi le décret 2-23-1, mais il ne
    # constitue pas le dispositif principal lui-même.
    if (
        section == "avenant_convention"
        or "avenant" in title
    ):
        return "avenant"

    if section == "dispositif_tpme":
        return "tpme"

    if section == "dispositif_principal":
        return "principal"

    if (
        "tpme" in title
        or "très petites" in title
        or "tres petites" in title
    ):
        return "tpme"

    if (
        "dispositif principal" in title
        or (
            "convention d'investissement" in title
            and "gouvernement du royaume" in title
            and "avenant" not in title
        )
    ):
        return "principal"

    is_incitation_source = (
        category == "incitations"
        or "convention d'investissement" in title
        or section in {
            "dispositif_principal",
            "dispositif_tpme",
            "avenant_convention",
        }
    )

    if (
        is_incitation_source
        and "2-25-342" in legal_reference
    ):
        return "tpme"

    if (
        is_incitation_source
        and "2-23-1" in legal_reference
    ):
        return "principal"

    if (
        "2-25-342"
        in normalized_content_reference
        or (
            "dispositif de soutien spécifique"
            in normalized_content
            and "tpme" in normalized_content
        )
        or (
            "dispositif de soutien specifique"
            in normalized_content
            and "tpme" in normalized_content
        )
    ):
        return "tpme"

    if (
        "2-23-1"
        in normalized_content_reference
        and (
            "dispositif de soutien principal"
            in normalized_content
            or "primes communes"
            in normalized_content
        )
    ):
        return "principal"

    return "other"


def _priorite_section_incitation(
    intent: str,
    dispositif: str,
    section: str,
) -> int:
    section = section.casefold().strip()

    if intent == "principal":
        if section == "dispositif_principal":
            return 5

        if dispositif == "principal":
            if section == "legal_context":
                return 3

            if section == "presentation":
                return 2

            return 1

        if dispositif == "avenant":
            return -3

        if dispositif == "tpme":
            return -2

    elif intent == "tpme":
        if section == "dispositif_tpme":
            return 5

        if dispositif == "tpme":
            if section == "legal_context":
                return 3

            if section == "presentation":
                return 2

            return 1

        if dispositif in {
            "principal",
            "avenant",
        }:
            return -2

    elif intent == "general":
        if section == "dispositif_principal":
            return 5

        if dispositif == "principal":
            return 3

        if section == "dispositif_tpme":
            return 1

        if dispositif == "tpme":
            return 0

        if dispositif == "avenant":
            return -2

    elif intent == "comparison":
        if section in {
            "dispositif_principal",
            "dispositif_tpme",
        }:
            return 4

        if dispositif in {
            "principal",
            "tpme",
        }:
            return 2

        if dispositif == "avenant":
            return -2

    return 0


def rerank_results(
    query: str,
    matches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    query_tokens = set(
        extract_search_tokens(query)
    )

    query_references = (
        extract_legal_references(query)
    )

    incitation_intent = (
        _detecter_intention_incitation(
            query
        )
    )

    tpme_eligibility_requested = (
        incitation_intent == "tpme"
        and bool(
            query_tokens.intersection(
                {
                    "condition",
                    "conditions",
                    "eligible",
                    "eligibles",
                    "eligibilite",
                    "beneficier",
                }
            )
        )
    )

    scored_matches: list[
        tuple[
            int,
            int,
            int,
            int,
            float,
            dict[str, Any],
        ]
    ] = []

    for match in matches:
        content = match.get(
            "content",
            "",
        )

        metadata = match.get(
            "metadata",
            {},
        )

        if not isinstance(content, str):
            content = ""

        if not isinstance(metadata, dict):
            metadata = {}

        title = str(
            metadata.get("source_title")
            or metadata.get("title")
            or metadata.get("procedure_name")
            or ""
        )

        section = str(
            metadata.get("section", "")
        )

        legal_reference = str(
            metadata.get(
                "legal_reference",
                "",
            )
        )

        searchable_text = " ".join(
            (
                content,
                title,
                section,
                legal_reference,
            )
        )

        content_tokens = set(
            extract_search_tokens(
                searchable_text
            )
        )

        token_overlap = len(
            query_tokens.intersection(
                content_tokens
            )
        )

        result_references = (
            extract_legal_references(
                searchable_text
            )
        )

        reference_matches = len(
            query_references.intersection(
                result_references
            )
        )

        dispositif = (
            _classifier_dispositif_incitation(
                content,
                metadata,
            )
        )

        intent_priority = 0

        if incitation_intent == "principal":
            if dispositif == "principal":
                intent_priority = 3
            elif dispositif == "avenant":
                intent_priority = -2
            elif dispositif == "tpme":
                intent_priority = -3

        elif incitation_intent == "tpme":
            if dispositif == "tpme":
                intent_priority = 3
            elif dispositif in {
                "principal",
                "avenant",
            }:
                intent_priority = -2

        elif incitation_intent == "general":
            if dispositif == "principal":
                intent_priority = 2
            elif dispositif == "tpme":
                intent_priority = 1
            elif dispositif == "avenant":
                intent_priority = -1

        elif incitation_intent == "comparison":
            if dispositif in {
                "principal",
                "tpme",
            }:
                intent_priority = 2
            elif dispositif == "avenant":
                intent_priority = -1

        section_priority = (
            _priorite_section_incitation(
                incitation_intent,
                dispositif,
                section,
            )
        )

        if (
            tpme_eligibility_requested
            and dispositif == "tpme"
        ):
            normalized_content = normalize_search_text(content)

            eligibility_markers = (
                "criteres d eligibilite",
                "qu est ce qu une tpme",
                "projets eligibles",
                "montant d investissement",
                "ratio emplois investissement",
                "fonds propres",
                "branches d activite eligibles",
                "capital detenu",
                "personne morale de droit public",
            )

            section_priority += sum(
                marker in normalized_content
                for marker in eligibility_markers
            )

        distance_value = match.get(
            "distance"
        )

        distance = (
            float(distance_value)
            if isinstance(
                distance_value,
                (int, float),
            )
            else float("inf")
        )

        scored_matches.append(
            (
                intent_priority,
                section_priority,
                reference_matches,
                token_overlap,
                distance,
                match,
            )
        )

    scored_matches.sort(
        key=lambda item: (
            -item[0],
            -item[1],
            -item[2],
            -item[3],
            item[4],
        )
    )

    return [
        item[5]
        for item in scored_matches
    ]

def merge_query_results(
    results: dict[str, Any],
) -> list[dict[str, Any]]:
    merged_matches: dict[str, dict[str, Any]] = {}

    result_ids = results.get("ids", [])
    result_documents = results.get("documents", [])
    result_metadatas = results.get("metadatas", [])
    result_distances = results.get("distances", [])

    for ids, documents, metadatas, distances in zip(
        result_ids,
        result_documents,
        result_metadatas,
        result_distances,
    ):
        for document_id, content, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
        ):
            match = {
                "id": document_id,
                "content": content,
                "metadata": metadata or {},
                "distance": distance,
            }

            existing_match = merged_matches.get(document_id)

            if existing_match is None:
                merged_matches[document_id] = match
                continue

            existing_distance = existing_match.get(
                "distance",
                float("inf"),
            )

            if distance < existing_distance:
                merged_matches[document_id] = match

    return list(merged_matches.values())


def search_documents(
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    normalized_query = query.strip()

    if not normalized_query:
        raise ValueError(
            "La requête de recherche ne doit pas être vide"
        )

    if limit < 1 or limit > 20:
        raise ValueError(
            "La limite doit être comprise entre 1 et 20"
        )

    collection = get_documents_collection()
    document_count = collection.count()

    if document_count == 0:
        return []

    focused_query = build_focused_query(normalized_query)

    retrieval_queries = [normalized_query]

    if (
        focused_query
        and normalize_search_text(focused_query)
        != normalize_search_text(normalized_query)
    ):
        retrieval_queries.append(focused_query)

    for expanded_query in build_cri_legal_queries(
        normalized_query
    ):
        if all(
            normalize_search_text(existing_query)
            != normalize_search_text(expanded_query)
            for existing_query in retrieval_queries
        ):
            retrieval_queries.append(
                expanded_query
            )

    query_embeddings = generate_query_embeddings(
        retrieval_queries
    )

    candidate_count = min(
        max(limit * 4, 10),
        document_count,
    )

    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=candidate_count,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    merged_matches = merge_query_results(results)

    ranked_matches = rerank_results(
        normalized_query,
        merged_matches,
    )

    return ranked_matches[:limit]


def delete_documents(document_ids: list[str]) -> int:
    normalized_ids = [
        document_id.strip()
        for document_id in document_ids
        if document_id.strip()
    ]

    if not normalized_ids:
        return 0

    collection = get_documents_collection()
    collection.delete(ids=normalized_ids)

    return len(normalized_ids)