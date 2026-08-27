from app.request_router import (
    detecter_categorie_message,
)


def test_morcellement_terrain_is_urbanisme():
    assert (
        detecter_categorie_message(
            "Quelle est la procedure pour obtenir "
            "une autorisation de morcellement "
            "d'un terrain ?"
        )
        == "urbanisme"
    )


def test_morceler_terrain_is_urbanisme():
    assert (
        detecter_categorie_message(
            "Je souhaite morceler mon terrain."
        )
        == "urbanisme"
    )


def test_generic_terrain_remains_foncier():
    assert (
        detecter_categorie_message(
            "Je cherche un terrain pour "
            "mon projet d'investissement."
        )
        == "foncier"
    )


def test_avna_remains_foncier():
    assert (
        detecter_categorie_message(
            "Comment obtenir une AVNA "
            "pour mon terrain ?"
        )
        == "foncier"
    )


def test_permis_construire_remains_urbanisme():
    assert (
        detecter_categorie_message(
            "Comment obtenir un permis "
            "de construire ?"
        )
        == "urbanisme"
    )

from app.request_router import (
    demande_est_trop_large,
    essayer_routage_local_rapide,
)


def test_morcellement_is_not_too_large():
    question = (
        "Quelle est la procedure pour obtenir "
        "une autorisation de morcellement "
        "d'un terrain ?"
    )

    assert demande_est_trop_large(
        question
    ) is False


def test_morcellement_agricole_is_not_too_large():
    question = (
        "Comment obtenir l'autorisation de morceler "
        "un terrain situe a l'interieur d'un perimetre "
        "d'irrigation pour realiser un projet non agricole ?"
    )

    assert demande_est_trop_large(
        question
    ) is False


def test_fast_routing_morcellement_is_search():
    question = (
        "Quelle est la procedure pour obtenir "
        "une autorisation de morcellement "
        "d'un terrain ?"
    )

    result = essayer_routage_local_rapide(
        question,
        [],
    )

    assert result is not None
    assert result.action == "search"
    assert result.category == "urbanisme"


def test_lotir_is_urbanisme():
    assert (
        detecter_categorie_message(
            "Quelle est la procedure pour obtenir "
            "une autorisation de lotir ?"
        )
        == "urbanisme"
    )
