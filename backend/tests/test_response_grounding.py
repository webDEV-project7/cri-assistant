from app.response_grounding import (
    ground_creation_response,
)


DOCUMENTS = """
Pour la création d'une entreprise, les documents
généralement demandés sont :
- une copie de la CIN ;
- le certificat négatif du nom commercial ;
- un justificatif de l'adresse du siège ;
- les statuts de la société ;
- les autorisations requises lorsque l'activité
  est réglementée ;
- le formulaire de déclaration de création.

La composition exacte du dossier peut varier selon
la forme juridique et l'activité.
"""


PROCEDURE = """
La création d'entreprise peut être réalisée en ligne
au moyen de la plateforme nationale DirectEntreprise.
"""


def resultat(
    section: str,
    content: str,
) -> dict:
    return {
        "content": content,
        "metadata": {
            "source_kind": "cri_gon_web",
            "section": section,
            "source_title": (
                "CRI Guelmim-Oued Noun — "
                "Création d’entreprise"
            ),
            "source_url": (
                "https://guelmiminvest.ma/faq/"
            ),
        },
        "distance": 0.4,
    }


def test_sarl_au_reste_generale_et_sourcee():
    response = ground_creation_response(
        user_message="sarl au",
        standalone_query=(
            "création d'une SARL à associé unique"
        ),
        rag_results=[
            resultat(
                "required_documents",
                DOCUMENTS,
            ),
        ],
        language_code="fr",
    )

    assert response is not None
    assert "liste générale" in response
    assert "SARL à associé unique" in response
    assert "une copie de la CIN" in response
    assert "de l’associé unique" not in response
    assert "DirectEntreprise" not in response
    assert "http" not in response


def test_delai_absent_n_est_pas_invente():
    response = ground_creation_response(
        user_message=(
            "Quel est le délai exact pour "
            "créer une SARL AU ?"
        ),
        standalone_query=(
            "délai création SARL à associé unique"
        ),
        rag_results=[
            resultat(
                "required_documents",
                DOCUMENTS,
            ),
        ],
        language_code="fr",
    )

    assert response == (
        "Les sources disponibles ne "
        "précisent pas ce point."
    )


def test_directentreprise_seulement_si_sourcee():
    response = ground_creation_response(
        user_message=(
            "Puis-je créer mon entreprise en ligne ?"
        ),
        standalone_query=(
            "création d'entreprise en ligne"
        ),
        rag_results=[
            resultat(
                "procedure",
                PROCEDURE,
            ),
        ],
        language_code="fr",
    )

    assert response is not None
    assert "DirectEntreprise" in response
    assert "http" not in response


def test_question_non_liee_non_remplacee():
    response = ground_creation_response(
        user_message=(
            "Comment obtenir une AVNA ?"
        ),
        standalone_query="procédure AVNA",
        rag_results=[
            resultat(
                "procedure",
                PROCEDURE,
            ),
        ],
        language_code="fr",
    )

    assert response is None