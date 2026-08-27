from app.rag import rerank_results


def make_match(
    section: str,
    title: str,
    content: str,
    distance: float,
):
    return {
        "content": content,
        "distance": distance,
        "metadata": {
            "section": section,
            "source_title": title,
            "category": "Incitations",
        },
    }


def first_section(query, matches):
    ranked = rerank_results(
        query,
        matches,
    )

    return ranked[0]["metadata"]["section"]


def test_general_question_prioritizes_principal():
    tpme = make_match(
        "dispositif_tpme",
        "Convention d'investissement - Dispositif TPME",
        "Primes accordées aux TPME.",
        0.10,
    )

    principal = make_match(
        "dispositif_principal",
        (
            "Convention d'investissement avec le "
            "Gouvernement - Dispositif principal"
        ),
        "Primes communes, territoriale et sectorielle.",
        0.90,
    )

    assert first_section(
        "Quelles sont les primes à l'investissement ?",
        [tpme, principal],
    ) == "dispositif_principal"


def test_principal_beats_closer_avenant():
    avenant = make_match(
        "avenant_convention",
        (
            "Avenant à la Convention d'investissement "
            "avec le Gouvernement du Royaume du Maroc"
        ),
        "Décret n° 2-23-1.",
        0.10,
    )

    principal = make_match(
        "dispositif_principal",
        (
            "Convention d'investissement avec le "
            "Gouvernement - Dispositif principal"
        ),
        (
            "Dispositif de soutien principal "
            "du décret n° 2-23-1."
        ),
        1.00,
    )

    assert first_section(
        (
            "Dispositif principal de soutien à "
            "l'investissement décret 2-23-1"
        ),
        [avenant, principal],
    ) == "dispositif_principal"


def test_tpme_question_prioritizes_tpme():
    principal = make_match(
        "dispositif_principal",
        "Dispositif principal",
        "Décret n° 2-23-1.",
        0.10,
    )

    tpme = make_match(
        "dispositif_tpme",
        "Dispositif TPME",
        "Décret n° 2-25-342.",
        1.00,
    )

    assert first_section(
        (
            "Dispositif spécifique de soutien aux "
            "TPME décret 2-25-342"
        ),
        [principal, tpme],
    ) == "dispositif_tpme"


def test_sectorial_prime_prioritizes_principal():
    tpme = make_match(
        "dispositif_tpme",
        "Dispositif TPME",
        "Prime liée aux activités prioritaires.",
        0.10,
    )

    principal = make_match(
        "dispositif_principal",
        "Dispositif principal",
        "Prime sectorielle de cinq pour cent.",
        1.00,
    )

    assert first_section(
        "Comment fonctionne la prime sectorielle ?",
        [tpme, principal],
    ) == "dispositif_principal"

def test_tpme_conditions_prioritize_eligibility_passage():
    documents = make_match(
        "dispositif_tpme",
        "Dispositif TPME",
        (
            "Conditions du dispositif TPME. "
            "Pieces constitutives du dossier."
        ),
        0.20,
    )

    eligibility = make_match(
        "dispositif_tpme",
        "Dispositif TPME",
        (
            "Quels sont les projets eligibles ? "
            "Montant d'investissement inferieur a 50 millions "
            "de dirhams. Ratio emplois investissement superieur "
            "ou egal a 1.5. Fonds propres au moins 10 pour cent."
        ),
        1.10,
    )

    ranked = rerank_results(
        (
            "Quelles sont les conditions pour beneficier "
            "du dispositif TPME ?"
        ),
        [documents, eligibility],
    )

    assert "projets eligibles" in ranked[0]["content"].casefold()