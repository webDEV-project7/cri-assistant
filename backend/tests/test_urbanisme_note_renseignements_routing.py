from app.request_router import (
    demande_est_trop_large,
    detecter_categorie_message,
    essayer_routage_local_rapide,
)


QUESTION_TERRAIN = (
    "Je souhaite obtenir une note de renseignements "
    "urbanistiques pour mon terrain."
)


def test_nru_with_terrain_is_urbanisme():
    assert (
        detecter_categorie_message(
            QUESTION_TERRAIN
        )
        == "urbanisme"
    )


def test_nru_with_terrain_is_not_too_large():
    assert (
        demande_est_trop_large(
            QUESTION_TERRAIN
        )
        is False
    )


def test_nru_with_terrain_fast_routes_to_search():
    routing = essayer_routage_local_rapide(
        QUESTION_TERRAIN,
        [],
    )

    assert routing is not None
    assert routing.action == "search"
    assert routing.category == "urbanisme"


def test_nru_documents_fast_routes_to_search():
    routing = essayer_routage_local_rapide(
        (
            "Quels documents faut-il pour obtenir "
            "une note de renseignements urbanistiques ?"
        ),
        [],
    )

    assert routing is not None
    assert routing.action == "search"
    assert routing.category == "urbanisme"


def test_nru_delay_fast_routes_to_search():
    routing = essayer_routage_local_rapide(
        (
            "Quel est le delai pour obtenir une note "
            "de renseignements urbanistiques ?"
        ),
        [],
    )

    assert routing is not None
    assert routing.action == "search"
    assert routing.category == "urbanisme"
