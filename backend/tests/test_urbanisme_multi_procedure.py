from app.main import (
    creer_contexte_documentaire,
    reranker_resultats_rag,
)


def make_result(
    procedure_id: str,
    procedure_name: str,
    section: str,
    distance: float,
    content: str,
) -> dict:
    return {
        "content": content,
        "distance": distance,
        "metadata": {
            "procedure_id": procedure_id,
            "procedure_name": procedure_name,
            "source_title": procedure_name,
            "authority": "CRI Invest",
            "section": section,
            "source_url": "",
        },
    }


def combined_results():
    return [
        make_result(
            "27",
            "Permis d'habiter",
            "presentation",
            0.64,
            "PASSAGE PERMIS HABITER PRESENTATION",
        ),
        make_result(
            "28",
            "Certificat de conformite",
            "presentation",
            0.62,
            "PASSAGE CERTIFICAT CONFORMITE PRESENTATION",
        ),
        make_result(
            "27",
            "Permis d'habiter",
            "required_documents",
            0.70,
            "PASSAGE PERMIS HABITER DOCUMENTS",
        ),
        make_result(
            "28",
            "Certificat de conformite",
            "required_documents",
            0.69,
            "PASSAGE CERTIFICAT CONFORMITE DOCUMENTS",
        ),
        make_result(
            "27",
            "Permis d'habiter",
            "procedure_milestones",
            0.73,
            "PASSAGE PERMIS HABITER ETAPES",
        ),
        make_result(
            "28",
            "Certificat de conformite",
            "procedure_milestones",
            0.72,
            "PASSAGE CERTIFICAT CONFORMITE ETAPES",
        ),
    ]


def procedure_ids(results):
    return {
        str(
            (
                result.get("metadata")
                or {}
            ).get("procedure_id")
        )
        for result in results
    }


def test_combined_question_keeps_27_and_28():
    results = reranker_resultats_rag(
        (
            "Comment obtenir le permis d'habiter "
            "ou le certificat de conformite "
            "apres les travaux ?"
        ),
        combined_results(),
    )

    assert procedure_ids(results) == {
        "27",
        "28",
    }


def test_combined_question_balances_first_results():
    results = reranker_resultats_rag(
        (
            "Comment obtenir le permis d'habiter "
            "ou le certificat de conformite "
            "apres les travaux ?"
        ),
        combined_results(),
    )

    first_two = [
        str(
            (
                result.get("metadata")
                or {}
            ).get("procedure_id")
        )
        for result in results[:2]
    ]

    assert set(first_two) == {
        "27",
        "28",
    }


def test_combined_context_contains_both_procedures():
    results = reranker_resultats_rag(
        (
            "Comment obtenir le permis d'habiter "
            "ou le certificat de conformite "
            "apres les travaux ?"
        ),
        combined_results(),
    )

    context, _ = creer_contexte_documentaire(
        results
    )

    assert (
        "PASSAGE PERMIS HABITER"
        in context
    )

    assert (
        "PASSAGE CERTIFICAT CONFORMITE"
        in context
    )


def test_single_permis_habiter_stays_single_procedure():
    results = reranker_resultats_rag(
        "Comment obtenir un permis d'habiter ?",
        combined_results(),
    )

    assert procedure_ids(results) == {
        "27",
    }


def test_single_certificat_stays_single_procedure():
    results = combined_results()

    # Pour une demande simple du certificat, la procedure 28
    # est volontairement la meilleure correspondance vectorielle.
    for result in results:
        pid = str(
            (
                result.get("metadata")
                or {}
            ).get("procedure_id")
        )

        if pid == "28":
            result["distance"] = (
                float(result["distance"])
                - 0.10
            )

        elif pid == "27":
            result["distance"] = (
                float(result["distance"])
                + 0.10
            )

    ranked = reranker_resultats_rag(
        "Comment obtenir le certificat de conformite ?",
        results,
    )

    assert procedure_ids(ranked) == {
        "28",
    }
