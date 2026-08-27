from __future__ import annotations

import re
import unicodedata
from typing import Any


def _normaliser(texte: Any) -> str:
    texte_decompose = unicodedata.normalize(
        "NFD",
        str(texte or ""),
    )

    texte_sans_accents = "".join(
        caractere
        for caractere in texte_decompose
        if unicodedata.category(caractere) != "Mn"
    )

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        texte_sans_accents.casefold(),
    ).strip()


def _est_source_creation(
    resultat: dict[str, Any],
) -> bool:
    metadata = resultat.get("metadata")

    if not isinstance(metadata, dict):
        return False

    source_kind = _normaliser(
        metadata.get("source_kind", "")
    )

    section = _normaliser(
        metadata.get("section", "")
    )

    return (
        source_kind == "cri gon web"
        and section
        in {
            "required documents",
            "procedure",
        }
    )


def _contenu_resultat(
    resultat: dict[str, Any],
) -> str:
    contenu = resultat.get("content")

    if not isinstance(contenu, str):
        return ""

    return contenu.strip()


def _detecter_forme_juridique(
    question: str,
) -> str | None:
    question_normalisee = _normaliser(question)

    if (
        re.search(
            r"\bsarl\s+(?:au|a associe unique|unipersonnelle)\b",
            question_normalisee,
        )
        or "sarlu" in question_normalisee
        or "sarlau" in question_normalisee
    ):
        return "SARL_AU"

    if (
        re.search(
            r"\bsas\s+(?:au|a associe unique|unipersonnelle)\b",
            question_normalisee,
        )
        or re.search(
            r"\bsasu\b",
            question_normalisee,
        )
    ):
        return "SASU"

    if re.search(
        r"\bsarl\b",
        question_normalisee,
    ):
        return "SARL"

    if re.search(
        r"\bsas\b",
        question_normalisee,
    ):
        return "SAS"

    return None


def _est_question_creation(
    question: str,
) -> bool:
    question_normalisee = _normaliser(question)

    termes_creation = (
        "creation d entreprise",
        "creer une entreprise",
        "creer mon entreprise",
        "creer une societe",
        "constitution d entreprise",
        "constitution de societe",
        "directentreprise",
        "sarl",
        "sarlu",
        "sarlau",
        "sasu",
        "sas",
    )

    return any(
        terme in question_normalisee
        for terme in termes_creation
    )


def _documents_sourcees(
    passages_normalises: str,
) -> list[str]:
    documents: list[str] = []

    if "copie de la cin" in passages_normalises:
        documents.append("cin")

    if "certificat negatif" in passages_normalises:
        documents.append("certificat_negatif")

    if "adresse du siege" in passages_normalises:
        documents.append("adresse_siege")

    if "statuts" in passages_normalises:
        documents.append("statuts")

    if (
        "autorisation" in passages_normalises
        and (
            "reglementee" in passages_normalises
            or "reglemente" in passages_normalises
        )
    ):
        documents.append("autorisations")

    if (
        "formulaire de declaration de creation"
        in passages_normalises
    ):
        documents.append("formulaire")

    return documents


FORMES_FR = {
    "SARL_AU": (
        "la SARL à associé unique "
        "(SARL AU)"
    ),
    "SASU": (
        "la SAS à associé unique "
        "(SASU)"
    ),
    "SARL": "la SARL",
    "SAS": "la SAS",
}


FORMES_EN = {
    "SARL_AU": (
        "the single-member SARL "
        "(SARL AU)"
    ),
    "SASU": (
        "the single-member SAS "
        "(SASU)"
    ),
    "SARL": "the SARL",
    "SAS": "the SAS",
}


FORMES_AR = {
    "SARL_AU": (
        "الشركة ذات المسؤولية المحدودة "
        "بشريك وحيد (SARL AU)"
    ),
    "SASU": (
        "شركة المساهمة المبسطة "
        "بمساهم وحيد (SASU)"
    ),
    "SARL": (
        "الشركة ذات المسؤولية المحدودة "
        "(SARL)"
    ),
    "SAS": (
        "شركة المساهمة المبسطة "
        "(SAS)"
    ),
}


DOCUMENTS_FR = {
    "cin": "une copie de la CIN",
    "certificat_negatif": (
        "le certificat négatif du nom commercial"
    ),
    "adresse_siege": (
        "un justificatif de l’adresse du siège"
    ),
    "statuts": "les statuts de la société",
    "autorisations": (
        "les autorisations requises lorsque "
        "l’activité est réglementée"
    ),
    "formulaire": (
        "le formulaire de déclaration de création"
    ),
}


DOCUMENTS_EN = {
    "cin": "a copy of the CIN",
    "certificat_negatif": (
        "the negative certificate for the "
        "business name"
    ),
    "adresse_siege": (
        "proof of the registered-office address"
    ),
    "statuts": "the company statutes",
    "autorisations": (
        "the required authorizations when "
        "the activity is regulated"
    ),
    "formulaire": (
        "the business-creation declaration form"
    ),
}


DOCUMENTS_AR = {
    "cin": "نسخة من بطاقة التعريف الوطنية",
    "certificat_negatif": (
        "الشهادة السلبية للاسم التجاري"
    ),
    "adresse_siege": (
        "وثيقة تثبت عنوان المقر الاجتماعي"
    ),
    "statuts": "النظام الأساسي للشركة",
    "autorisations": (
        "التراخيص المطلوبة عندما يكون "
        "النشاط منظما"
    ),
    "formulaire": (
        "استمارة التصريح بإنشاء المقاولة"
    ),
}


def _liste_numerotee(
    documents: list[str],
    traductions: dict[str, str],
) -> str:
    lignes: list[str] = []

    for numero, document in enumerate(
        documents,
        start=1,
    ):
        ponctuation = (
            "."
            if numero == len(documents)
            else ";"
        )

        lignes.append(
            f"{numero}. "
            f"{traductions[document]}"
            f"{ponctuation}"
        )

    return "\n".join(lignes)


def _reponse_delai_absent(
    language_code: str,
) -> str:
    if language_code == "ar":
        return (
            "المصادر المتاحة لا تحدد هذه المعلومة."
        )

    if language_code == "en":
        return (
            "The available sources do not "
            "specify this point."
        )

    return (
        "Les sources disponibles ne "
        "précisent pas ce point."
    )


def _reponse_creation_en_ligne(
    language_code: str,
    directentreprise_presente: bool,
) -> str:
    if not directentreprise_presente:
        return _reponse_delai_absent(
            language_code
        )

    if language_code == "ar":
        return (
            "نعم. يشير المقطع الرسمي المسترجع "
            "إلى أن إنشاء المقاولة يمكن أن يتم "
            "عبر الإنترنت بواسطة منصة "
            "DirectEntreprise."
        )

    if language_code == "en":
        return (
            "Yes. The retrieved official passage "
            "states that a business can be created "
            "online through the DirectEntreprise "
            "platform."
        )

    return (
        "Oui. Le passage officiel récupéré "
        "indique que la création d’entreprise "
        "peut être réalisée en ligne au moyen "
        "de la plateforme DirectEntreprise."
    )


def _reponse_documents(
    *,
    language_code: str,
    forme: str | None,
    documents: list[str],
) -> str:
    if language_code == "ar":
        if forme:
            introduction = (
                "توفر المقاطع الرسمية المسترجعة "
                "لائحة عامة لوثائق إنشاء المقاولة. "
                "ولا توفر لائحة خاصة وشاملة بـ"
                f"{FORMES_AR[forme]}."
            )
        else:
            introduction = (
                "توفر المقاطع الرسمية المسترجعة "
                "لائحة عامة لوثائق إنشاء المقاولة."
            )

        if not documents:
            return (
                introduction
                + "\n\nلا تحدد المقاطع المسترجعة "
                "تفاصيل الوثائق."
            )

        return (
            f"{introduction}\n\n"
            "الوثائق المذكورة بصفة عامة هي:\n"
            f"{_liste_numerotee(documents, DOCUMENTS_AR)}"
            "\n\nقد تختلف التركيبة الدقيقة للملف "
            "حسب الشكل القانوني والنشاط."
        )

    if language_code == "en":
        if forme:
            introduction = (
                "The retrieved official passages "
                "provide a general list of documents "
                "for business creation. They do not "
                "provide a specific and exhaustive "
                f"list for {FORMES_EN[forme]}."
            )
        else:
            introduction = (
                "The retrieved official passages "
                "provide a general list of documents "
                "for business creation."
            )

        if not documents:
            return (
                introduction
                + "\n\nThe retrieved passages do not "
                "specify the document details."
            )

        return (
            f"{introduction}\n\n"
            "The documents generally mentioned are:\n"
            f"{_liste_numerotee(documents, DOCUMENTS_EN)}"
            "\n\nThe exact composition of the file "
            "may vary according to the legal form "
            "and the activity."
        )

    if forme:
        introduction = (
            "Les passages officiels récupérés "
            "fournissent une liste générale de "
            "documents pour la création "
            "d’entreprise. Ils ne fournissent pas "
            "une liste spécifique et exhaustive "
            f"propre à {FORMES_FR[forme]}."
        )
    else:
        introduction = (
            "Les passages officiels récupérés "
            "fournissent une liste générale de "
            "documents pour la création "
            "d’entreprise."
        )

    if not documents:
        return (
            introduction
            + "\n\nLes passages récupérés ne "
            "précisent pas le détail des documents."
        )

    return (
        f"{introduction}\n\n"
        "Les documents généralement mentionnés sont :\n"
        f"{_liste_numerotee(documents, DOCUMENTS_FR)}"
        "\n\nLa composition exacte du dossier "
        "peut varier selon la forme juridique "
        "et l’activité."
    )


def ground_creation_response(
    *,
    user_message: str,
    standalone_query: str,
    rag_results: list[dict[str, Any]],
    language_code: str = "fr",
) -> str | None:
    question = (
        f"{user_message} {standalone_query}"
    )

    if not _est_question_creation(question):
        return None

    resultats_creation = [
        resultat
        for resultat in rag_results
        if _est_source_creation(resultat)
    ]

    if not resultats_creation:
        return None

    passages = "\n".join(
        _contenu_resultat(resultat)
        for resultat in resultats_creation
        if _contenu_resultat(resultat)
    )

    if not passages.strip():
        return None

    question_normalisee = _normaliser(question)
    passages_normalises = _normaliser(passages)

    demande_delai = any(
        terme in question_normalisee
        for terme in (
            "delai",
            "duree",
            "combien de temps",
            "nombre de jours",
            "how long",
            "duration",
            "كم يستغرق",
            "المدة",
        )
    )

    if demande_delai:
        passage_contient_delai = any(
            terme in passages_normalises
            for terme in (
                "delai",
                "duree",
                "jour ouvrable",
                "jours ouvrables",
            )
        )

        if not passage_contient_delai:
            return _reponse_delai_absent(
                language_code
            )

    demande_en_ligne = any(
        terme in question_normalisee
        for terme in (
            "en ligne",
            "internet",
            "directentreprise",
            "plateforme",
            "online",
            "عبر الانترنت",
            "المنصة",
        )
    )

    if demande_en_ligne:
        return _reponse_creation_en_ligne(
            language_code,
            (
                "directentreprise"
                in passages_normalises
            ),
        )

    forme = _detecter_forme_juridique(
        question
    )

    documents = _documents_sourcees(
        passages_normalises
    )

    return _reponse_documents(
        language_code=language_code,
        forme=forme,
        documents=documents,
    )