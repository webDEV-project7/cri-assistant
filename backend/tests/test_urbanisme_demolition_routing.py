from app.request_router import (
    demande_est_trop_large,
    detecter_categorie_message,
    essayer_routage_local_rapide,
)


QUESTION_TERRAIN = (
    "Je veux d\u00e9molir un b\u00e2timent "
    "sur mon terrain."
)


def test_demolir_terrain_is_urbanisme():
    assert (
        detecter_categorie_message(
            QUESTION_TERRAIN
        )
        == "urbanisme"
    )


def test_demolir_terrain_is_not_too_large():
    assert (
        demande_est_trop_large(
            QUESTION_TERRAIN
        )
        is False
    )


def test_demolir_terrain_routes_to_search():
    routing = essayer_routage_local_rapide(
        QUESTION_TERRAIN,
        [],
    )

    assert routing is not None
    assert routing.action == "search"
    assert routing.category == "urbanisme"


def test_permis_demolition_routes_to_urbanisme():
    routing = essayer_routage_local_rapide(
        (
            "Comment obtenir un permis "
            "de d\u00e9molition ?"
        ),
        [],
    )

    assert routing is not None
    assert routing.action == "search"
    assert routing.category == "urbanisme"


def test_documents_demolition_routes_to_urbanisme():
    routing = essayer_routage_local_rapide(
        (
            "Quels documents faut-il pour "
            "un permis de d\u00e9molition ?"
        ),
        [],
    )

    assert routing is not None
    assert routing.action == "search"
    assert routing.category == "urbanisme"


def test_demolir_terrain_uses_canonical_query():
    question = (
        "Je veux d\u00e9molir un b\u00e2timent "
        "sur mon terrain."
    )

    routing = essayer_routage_local_rapide(
        question,
        [],
    )

    assert routing is not None
    assert routing.action == "search"
    assert routing.category == "urbanisme"

    assert routing.standalone_query.startswith(
        "Permis de d\u00e9molition. "
    )

    assert question in routing.standalone_query


def test_explicit_permis_demolition_keeps_original_query():
    question = (
        "Comment obtenir un permis "
        "de d\u00e9molition ?"
    )

    routing = essayer_routage_local_rapide(
        question,
        [],
    )

    assert routing is not None
    assert routing.action == "search"
    assert routing.category == "urbanisme"

    assert (
        routing.standalone_query
        == question
    )

