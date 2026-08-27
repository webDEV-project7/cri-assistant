from app.import_cri_gon_knowledge import (
    DEFAULT_SNAPSHOT_PATH,
    build_documents,
    load_snapshot,
)
from app.request_router import (
    filtrer_resultats_par_categorie,
)


EXPECTED_IDS = {
    "cri-gon-creation-entreprise-demarches-001",
    "cri-gon-creation-entreprise-documents-001",
    "cri-gon-creation-entreprise-presentation-001",
    "cri-gon-creation-entreprise-individuelle-001",
    "cri-gon-creation-entreprise-auto-entrepreneur-001",
    "cri-gon-creation-entreprise-sarl-001",
    "cri-gon-creation-entreprise-sa-001",
    "cri-gon-creation-entreprise-sas-sasu-001",
    "cri-gon-creation-entreprise-autres-formes-001",
    "cri-gon-creation-entreprise-directentreprise-001",
}


EXPECTED_SECTIONS = {
    "procedure",
    "required_documents",
    "presentation",
    "entreprise_individuelle",
    "auto_entrepreneur",
    "sarl",
    "sa",
    "sas_sasu",
    "autres_formes_juridiques",
    "directentreprise",
}


def _documents():
    snapshot = load_snapshot(
        DEFAULT_SNAPSHOT_PATH
    )

    return build_documents(
        snapshot
    )


def test_creation_entreprise_snapshot_has_10_documents():
    documents = _documents()

    assert len(documents) == 10


def test_creation_entreprise_expected_ids():
    documents = _documents()

    ids = {
        document.id
        for document in documents
    }

    assert ids == EXPECTED_IDS


def test_creation_entreprise_expected_sections():
    documents = _documents()

    sections = {
        document.metadata.get("section")
        for document in documents
    }

    assert sections == EXPECTED_SECTIONS


def test_creation_entreprise_metadata():
    documents = _documents()

    expected_category = (
        "Cr\u00e9ation d\u2019entreprise"
    )

    for document in documents:
        metadata = document.metadata

        assert (
            metadata.get("category")
            == expected_category
        )

        assert (
            metadata.get("source_kind")
            == "cri_gon_web"
        )

        assert (
            metadata.get("language")
            == "fr"
        )


def test_creation_entreprise_key_topics_present():
    documents = _documents()

    by_section = {
        document.metadata.get("section"):
        document.content
        for document in documents
    }

    assert "SARL" in by_section["sarl"]

    assert "SASU" in by_section[
        "sas_sasu"
    ]

    assert "DirectEntreprise" in by_section[
        "directentreprise"
    ]

    assert "auto-entrepreneur" in by_section[
        "auto_entrepreneur"
    ]


def test_creation_entreprise_category_filter():
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
        "creation_entreprise",
    )

    assert len(filtered) == 10

    assert {
        result["id"]
        for result in filtered
    } == EXPECTED_IDS