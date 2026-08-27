from app.main import reranker_resultats_rag


def test_preserves_specialized_incitation_ranking():
    principal = {
        "content": (
            "Le dispositif principal prévoit des primes "
            "communes, territoriale et sectorielle."
        ),
        "distance": 0.85,
        "metadata": {
            "source_kind": "official_procedure",
            "section": "dispositif_principal",
            "source_title": "Dispositif principal",
        },
    }

    legal_context = {
        "content": "Décret n° 2-23-1.",
        "distance": 0.70,
        "metadata": {
            "source_kind": "cri_procedure",
            "section": "legal_context",
            "procedure_id": 3,
            "source_title": "Contexte juridique",
        },
    }

    results = [
        principal,
        legal_context,
    ]

    ranked = reranker_resultats_rag(
        "Quelles sont les primes à l'investissement ?",
        results,
    )

    assert ranked == results
    assert (
        ranked[0]["metadata"]["section"]
        == "dispositif_principal"
    )


def test_preserves_tpme_specialized_ranking():
    tpme = {
        "content": (
            "Le dispositif TPME prévoit une prime à "
            "l'emploi, une prime territoriale et une "
            "prime liée aux activités prioritaires."
        ),
        "distance": 0.65,
        "metadata": {
            "source_kind": "official_procedure",
            "section": "dispositif_tpme",
            "source_title": "Dispositif TPME",
        },
    }

    other = {
        "content": "Contexte juridique TPME.",
        "distance": 0.50,
        "metadata": {
            "source_kind": "cri_procedure",
            "section": "legal_context",
            "procedure_id": 1029,
        },
    }

    results = [
        tpme,
        other,
    ]

    ranked = reranker_resultats_rag(
        "Quelles sont les aides destinées aux TPME ?",
        results,
    )

    assert ranked == results
    assert (
        ranked[0]["metadata"]["section"]
        == "dispositif_tpme"
    )