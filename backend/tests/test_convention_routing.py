import pytest

from app.request_router import (
    detecter_categorie_message,
    filtrer_resultats_par_categorie,
)


@pytest.mark.parametrize(
    "question",
    [
        (
            "Quels sont les types d'avenant "
            "a une convention d'investissement ?"
        ),
        (
            "Comment obtenir une convention "
            "d'investissement avec l'Etat ?"
        ),
        (
            "Qu'est-ce qu'un avenant modificatif "
            "a une convention d'investissement ?"
        ),
        (
            "Comment fonctionne un avenant "
            "prorogatif ?"
        ),
    ],
)
def test_convention_queries_are_routed_to_convention(
    question,
):
    assert (
        detecter_categorie_message(question)
        == "convention"
    )


def test_convention_filter_accepts_incitations_metadata():
    result = {
        "id": "test-convention",
        "content": "Convention d'investissement",
        "metadata": {
            "category": "Incitations",
        },
        "distance": 0.5,
    }

    filtered = filtrer_resultats_par_categorie(
        [result],
        "convention",
    )

    assert len(filtered) == 1
    assert filtered[0]["id"] == "test-convention"