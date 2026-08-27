from app.request_router import (
    detecter_categorie_message,
)


def test_echange_immobilier_domaine_forestier_is_foncier():
    assert (
        detecter_categorie_message(
            "Quelle est la procedure pour realiser "
            "un echange immobilier portant sur le "
            "domaine forestier ?"
        )
        == "foncier"
    )


def test_echange_immobilier_accented_is_foncier():
    assert (
        detecter_categorie_message(
            "Je souhaite r\u00e9aliser un \u00e9change immobilier "
            "portant sur le domaine forestier."
        )
        == "foncier"
    )


def test_echange_terrain_forestier_is_foncier():
    assert (
        detecter_categorie_message(
            "Comment faire un echange de terrain "
            "forestier pour mon projet ?"
        )
        == "foncier"
    )


def test_echange_terrains_forestiers_is_foncier():
    assert (
        detecter_categorie_message(
            "Quelle procedure pour un echange de "
            "terrains forestiers ?"
        )
        == "foncier"
    )


def test_environmental_impact_remains_environment():
    assert (
        detecter_categorie_message(
            "Quelle est la procedure pour une etude "
            "d'impact environnemental ?"
        )
        == "environnement"
    )


def test_environmental_acceptability_remains_environment():
    assert (
        detecter_categorie_message(
            "Comment obtenir l'acceptabilite "
            "environnementale de mon projet ?"
        )
        == "environnement"
    )


def test_occupation_forestiere_remains_foncier():
    assert (
        detecter_categorie_message(
            "Quelle demarche pour une occupation "
            "temporaire du domaine forestier ?"
        )
        == "foncier"
    )
