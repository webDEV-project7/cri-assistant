from app.import_environment_knowledge import (
    DEFAULT_SNAPSHOT_PATH,
    build_documents,
    load_snapshot,
)
from app.request_router import (
    filtrer_resultats_par_categorie,
)


EXPECTED_IDS = {
    "env-maroc-evaluation-environnementale-001",
    "env-maroc-eie-cadre-documents-cout-001",
    "env-maroc-nie-presentation-001",
    "env-maroc-nie-documents-cout-001",
    "env-maroc-audit-presentation-001",
    "env-maroc-audit-documents-cout-001",
}


EXPECTED_SECTIONS = {
    "evaluation_environmentale",
    "eie_complement",
    "nie_presentation",
    "nie_documents_cost",
    "audit_presentation",
    "audit_documents_cost",
}


def _documents():
    snapshot = load_snapshot(
        DEFAULT_SNAPSHOT_PATH
    )

    return build_documents(
        snapshot
    )


def test_environment_snapshot_has_6_documents():
    documents = _documents()

    assert len(documents) == 6


def test_environment_expected_ids():
    documents = _documents()

    ids = {
        document.id
        for document in documents
    }

    assert ids == EXPECTED_IDS


def test_environment_expected_sections():
    documents = _documents()

    sections = {
        document.metadata.get("section")
        for document in documents
    }

    assert sections == EXPECTED_SECTIONS


def test_environment_metadata():
    documents = _documents()

    expected_category = (
        "Acceptabilit\u00e9 des projets"
    )

    for document in documents:
        metadata = document.metadata

        assert (
            metadata.get("category")
            == expected_category
        )

        assert (
            metadata.get("source_kind")
            == "environment_official_web"
        )

        assert (
            metadata.get("official_source")
            is True
        )

        assert (
            metadata.get("language")
            == "fr"
        )


def test_environment_key_topics_present():
    documents = _documents()

    by_section = {
        document.metadata.get("section"):
        document.content
        for document in documents
    }

    assert "49-17" in by_section[
        "evaluation_environmentale"
    ]

    assert "Notice" in by_section[
        "nie_presentation"
    ]

    assert "Audit" in by_section[
        "audit_presentation"
    ]

    assert "Certificat" in by_section[
        "audit_documents_cost"
    ]

    assert "aucun frais" in by_section[
        "nie_documents_cost"
    ]

    assert "enquete publique" in (
        by_section["eie_complement"]
        .casefold()
        .replace("\u2019", "'")
    )


def test_environment_category_filter():
    documents = _documents()

    results = [
        {
            "id": document.id,
            "content": document.content,
            "metadata": document.metadata,
            "distance": 0.50,
        }
        for document in documents
    ]

    filtered = filtrer_resultats_par_categorie(
        results,
        "environnement",
    )

    assert len(filtered) == 6

    assert {
        result["id"]
        for result in filtered
    } == EXPECTED_IDS