from app.source_visibility import (
    filter_visible_sources,
)


OFFICIAL_SOURCE = {
    "title": "Procédure officielle",
    "url": "https://www.cri-invest.ma/procedures/3",
}


def test_administrative_answer_keeps_official_source():
    result = filter_visible_sources(
        user_message=(
            "Quels sont les critères d’éligibilité "
            "au dispositif principal ?"
        ),
        assistant_response=(
            "Le projet doit répondre aux critères "
            "prévus par le dispositif principal."
        ),
        sources=[OFFICIAL_SOURCE],
    )

    assert result == [OFFICIAL_SOURCE]


def test_greeting_hides_sources():
    result = filter_visible_sources(
        user_message="Bonjour",
        assistant_response=(
            "Bonjour, comment puis-je vous aider ?"
        ),
        sources=[OFFICIAL_SOURCE],
    )

    assert result == []


def test_thanks_hide_sources():
    result = filter_visible_sources(
        user_message="Merci beaucoup",
        assistant_response="Avec plaisir.",
        sources=[OFFICIAL_SOURCE],
    )

    assert result == []


def test_translation_hides_sources():
    result = filter_visible_sources(
        user_message=(
            "Traduis cette phrase en arabe."
        ),
        assistant_response="النص المترجم",
        sources=[OFFICIAL_SOURCE],
    )

    assert result == []


def test_clarification_hides_sources():
    result = filter_visible_sources(
        user_message="Je cherche un terrain.",
        assistant_response=(
            "Quelle procédure souhaitez-vous consulter ?\n"
            "1. Attribution d’un lot\n"
            "2. Location d’un terrain"
        ),
        sources=[OFFICIAL_SOURCE],
    )

    assert result == []


def test_non_official_url_is_removed():
    result = filter_visible_sources(
        user_message="Quels documents sont requis ?",
        assistant_response=(
            "Les documents dépendent de la procédure."
        ),
        sources=[
            {
                "title": "Site non officiel",
                "url": "https://example.com/article",
            },
            OFFICIAL_SOURCE,
        ],
    )

    assert result == [OFFICIAL_SOURCE]


def test_duplicate_sources_are_removed():
    result = filter_visible_sources(
        user_message="Quels documents sont requis ?",
        assistant_response="Voici les documents requis.",
        sources=[
            OFFICIAL_SOURCE,
            OFFICIAL_SOURCE,
        ],
    )

    assert result == [OFFICIAL_SOURCE]