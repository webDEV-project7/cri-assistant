import pytest

from app.rag import (
    _detecter_intention_incitation,
    rerank_results,
)


@pytest.mark.parametrize(
    "question",
    [
        (
            "Quels criteres faut-il remplir pour "
            "une convention d'investissement "
            "avec l'Etat ?"
        ),
        (
            "Comment obtenir une convention "
            "d investissement avec l Etat ?"
        ),
    ],
)
def test_convention_investissement_uses_general_incitation_intent(
    question,
):
    assert (
        _detecter_intention_incitation(question)
        == "general"
    )


def test_tpme_intent_is_not_changed():
    question = (
        "Quelles sont les conditions pour "
        "beneficier du dispositif TPME ?"
    )

    assert (
        _detecter_intention_incitation(question)
        == "tpme"
    )


def test_current_principal_source_beats_old_convention_presentation():
    question = (
        "Quels criteres faut-il remplir pour "
        "une convention d'investissement "
        "avec l'Etat ?"
    )

    stale = {
        "id": "cri-procedure-3-presentation-001",
        "content": (
            "Convention d'investissement avec l'Etat. "
            "Ancienne presentation de la procedure."
        ),
        "metadata": {
            "category": "Incitations",
            "source_kind": "cri_procedure",
            "section": "presentation",
            "source_title": (
                "Convention d'Investissement avec "
                "le Gouvernement du Royaume du Maroc"
            ),
            "legal_reference": "",
        },
        # Distance volontairement meilleure pour verifier
        # que la priorite metier reste dominante.
        "distance": 0.40,
    }

    current = {
        "id": "official-principal-current",
        "content": (
            "Dispositif principal de soutien "
            "a l'investissement. "
            "Criteres d'eligibilite actuels."
        ),
        "metadata": {
            "category": "Incitations",
            "source_kind": "official_procedure",
            "section": "dispositif_principal",
            "source_title": (
                "Convention d'investissement avec "
                "le Gouvernement du Royaume du Maroc "
                "— Dispositif principal"
            ),
            "legal_reference": (
                "Loi-cadre 03-22 ; Decret 2-23-1"
            ),
        },
        "distance": 0.80,
    }

    ranked = rerank_results(
        question,
        [
            stale,
            current,
        ],
    )

    assert ranked[0]["id"] == "official-principal-current"