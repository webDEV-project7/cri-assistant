from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Literal

import httpx


CategoryCode = Literal[
    "foncier",
    "urbanisme",
    "entreprise",
    "exploitation",
    "environnement",
    "incitations",
    "convention",
    "general",
]


@dataclass(frozen=True, slots=True)
class RoutageDemande:
    action: Literal["clarify", "search"]
    category: CategoryCode
    standalone_query: str
    clarification: str


ROUTER_SYSTEM_PROMPT = """
Tu es le routeur interne de CRI Assistant.

Analyse le dernier message avec l’historique et retourne uniquement
un objet JSON valide contenant exactement ces quatre champs :

{
  "action": "clarify" ou "search",
  "category": "foncier", "urbanisme", "entreprise",
              "exploitation", "environnement", "incitations",
              "convention" ou "general",
  "standalone_query": "requête autonome en français pour le RAG",
  "clarification": "question à afficher si action=clarify"
}

RÈGLES

1. Utilise "clarify" uniquement lorsqu’une information manquante
empêche réellement d’identifier la procédure correcte.

Une demande comme « toutes les informations liées au foncier »,
« tout sur l’urbanisme » ou « toutes les démarches » est trop large.
Elle doit obligatoirement produire "clarify", car une catégorie peut
contenir plusieurs procédures différentes. Ne mélange jamais plusieurs
procédures dans une seule réponse.

2. Utilise "search" pour :
   - une demande précise ;
   - une question générale mais compréhensible ;
   - une demande de définition ;
   - une demande complète grâce à l’historique.

3. Utilise toujours l’historique. Une réponse courte comme :
   "1", "à Guelmim", "le premier choix" ou "zone industrielle"
complète la question précédente.

Après une clarification, si l’investisseur fournit le choix demandé,
la localisation, le type de terrain ou la nature du projet, utilise
obligatoirement "search". Ne pose pas une deuxième clarification.

Exemple :
- demande initiale : "Bghit terrain bach ndir projet"
- précision : "1, f Guelmim. Bghit ndir unité industrielle"
- résultat obligatoire :
  action = "search"
  category = "foncier"
  standalone_query = "Procédure d’attribution d’un lot dans une zone
  industrielle à Guelmim pour créer une unité industrielle."

Les mots darija comme "bghit", "ndir", "bach", "wach", "ach",
"kifach" ou "f Guelmim" imposent une clarification en arabe clair,
même si le message contient aussi du français.

4. Pour "search", écris standalone_query en français.
Cette requête doit reprendre tous les faits utiles déjà établis.

5. Pour "clarify", pose une seule question courte et propose
entre deux et quatre choix numérotés.

6. Langue de la clarification :
   - darija, même mélangée au français : arabe clair ;
   - arabe : arabe clair ;
   - français : français ;
   - anglais : anglais.

7. Ne réponds pas à la question administrative dans la clarification.

8. N’invente aucune procédure, pièce, autorité, durée ou condition.

9. CONTEXTE JURIDIQUE MAROCAIN
Toutes les demandes concernent le Maroc et le Centre Régional
d’Investissement, sauf si l’utilisateur indique explicitement un
autre pays. Ne remplace jamais le Maroc par la France.

10. FORMES JURIDIQUES
SAS signifie « société par actions simplifiée ».
SASU signifie « société par actions simplifiée à associé unique ».
Ne développe jamais SASU comme une société à responsabilité limitée.
« SASU » et « SAS à associé unique » désignent le même choix et ne
doivent jamais être proposés comme deux options différentes.


RÈGLE PRIORITAIRE POUR LA LANGUE

Détermine la langue de la clarification uniquement à partir du
DERNIER MESSAGE. Ignore la langue de l’historique.

- Un dernier message entièrement en français impose une clarification
  entièrement en français, même après un échange en arabe.
- Un message en darija impose une clarification en arabe clair.
- Un message en arabe impose une clarification en arabe clair.
- Un message en anglais impose une clarification en anglais.
- Ne conserve jamais automatiquement la langue de la réponse
  précédente.
""".strip()


CATEGORY_TERMS: dict[str, tuple[str, ...]] = {
    "foncier": (
        "foncier",
        "foncie",
        "terrain",
        "lot industriel",
        "zone industrielle",
        "domaine prive de l etat",
        "occupation temporaire",
        "echange immobilier",
        "echange immobilier domaine forestier",
        "echange immobilier du domaine forestier",
        "echange de terrain forestier",
        "echange de terrains forestiers",
        "echange terrain forestier",
        "echange terrains forestiers",
        "echange forestier",
        "avna",
        "vocation non agricole",
        "lard",
        "ard",
        "العقار",
        "عقار",
        "الأرض",
        "ارض",
        "أرض",
    ),
    "urbanisme": (
        "urbanisme",
        "construction",
        "permis de construire",
        "permis d habiter",
        "certificat de conformite",
        "lotissement",
        "morcellement",
        "lotir",
        "autorisation de lotir",
        "morceler",
    ),
    "entreprise": (
        "creation d entreprise",
        "creation entreprise",
        "creer une entreprise",
        "creer entreprise",
        "constitution de societe",
        "personne morale",
        "registre de commerce",
    ),
    "exploitation": (
        "exploitation",
        "autorisation d exercer",
        "agrement",
        "licence",
        "mise en service",
        "zone d acceleration industrielle",
        "zone d'acceleration industrielle",
        "zone franche d exportation",
        "zone franche d'exportation",
        "restaurant touristique",
        "residence immobiliere adossee",
        "hebergement touristique",
        "classement d exploitation",
        "classement provisoire",
    ),
    "environnement": (
        "environnement",
        "environnementale",
        "acceptabilite",
        "etude d impact",
    ),
    "incitations": (
        "incitation",
        "incitations",
        "prime",
        "primes",
        "aide a l investissement",
        "aides a l investissement",
        "dispositif principal",
        "dispositif tpme",
        "charte de l investissement",
        "soutien a l investissement",
        "avantage a l investissement",
        "تحفيزات",
        "حوافز",
        "منح الاستثمار",
        "دعم الاستثمار",
    ),
    "convention": (
        "convention d investissement",
        "convention d'investissement",
        "convention investissement",
        "convention avec l etat",
        "convention avec l'etat",
        "avenant",
        "avenant modificatif",
        "avenant prorogatif",
    ),
}


def normaliser(value: str) -> str:
    value = unicodedata.normalize(
        "NFKD",
        value.casefold(),
    )

    return "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )


def extraire_objet_json(
    content: str,
) -> dict[str, Any]:
    content = content.strip()

    try:
        value = json.loads(content)

    except json.JSONDecodeError:
        match = re.search(
            r"\{.*\}",
            content,
            flags=re.DOTALL,
        )

        if match is None:
            raise ValueError(
                "Le routeur n’a pas retourné de JSON"
            )

        value = json.loads(match.group(0))

    if not isinstance(value, dict):
        raise ValueError(
            "La réponse du routeur n’est pas un objet"
        )

    return value


DARIJA_LATIN_WORDS = {
    "ana",
    "bghit",
    "bghina",
    "ndir",
    "ndiro",
    "bach",
    "wach",
    "chno",
    "ach",
    "kifach",
    "fin",
    "f",
    "dyal",
    "dial",
    "3ndi",
    "3andi",
    "ghadi",
    "ila",
    "hada",
    "hadi",
    "hadchi",
    "mn",
    "bzaf",
    "makayn",
}

ENGLISH_HINTS = {
    "what",
    "which",
    "how",
    "where",
    "when",
    "need",
    "land",
    "permit",
    "documents",
    "please",
    "everything",
    "about",
}

BROAD_REQUEST_MARKERS = (
    "toutes les informations",
    "tous les renseignements",
    "tout ce qui concerne",
    "tout sur",
    "informations liees",
    "ensemble des informations",
    "all information",
    "everything about",
    "جميع المعلومات",
    "كل المعلومات",
    "كل ما يتعلق",
)


DEFINITION_MARKERS = (
    "qu est ce que",
    "qu est ce qu",
    "c est quoi",
    "que signifie",
    "quelle est la definition",
    "definition de",
    "chno howa",
    "chno hiya",
    "chno homa",
    "chno",
    "achno",
    "chnou",
    "chnouwa",
    "ach kay3ni",
    "شنو هو",
    "شنو هي",
    "ما هو",
    "ما هي",
    "ما معنى",
    "ماذا يعني",
    "what is",
    "what are",
    "what does",
)


DEFINITION_QUERIES: dict[str, str] = {
    "foncier": (
        "Définition du foncier destiné à l’investissement "
        "au Maroc, catégories de terrains et rôle du CRI "
        "Guelmim-Oued Noun."
    ),
    "urbanisme": (
        "Définition des procédures et autorisations "
        "d’urbanisme applicables aux projets "
        "d’investissement au Maroc."
    ),
    "entreprise": (
        "Définition et principales démarches de création "
        "d’entreprise au Maroc auprès du CRI."
    ),
    "exploitation": (
        "Définition des autorisations d’exploitation et "
        "de mise en service d’un projet au Maroc."
    ),
    "environnement": (
        "Définition des procédures environnementales et "
        "de l’acceptabilité environnementale au Maroc."
    ),
    "incitations": (
        "Définition des incitations, primes et dispositifs "
        "de soutien à l’investissement prévus par la "
        "Charte de l’investissement au Maroc."
    ),
    "convention": (
        "Définition de la convention d’investissement et "
        "de son rôle dans les dispositifs de soutien au Maroc."
    ),
}


def demande_est_definition(
    message: str,
) -> bool:
    normalized_message = normaliser(message)

    normalized_message = re.sub(
        r"[-‐-‒–—'’]+",
        " ",
        normalized_message,
    )

    normalized_message = " ".join(
        normalized_message.split()
    )

    return any(
        normalized_message.startswith(marker)
        for marker in DEFINITION_MARKERS
    )

def detecter_langue_message(
    message: str,
) -> Literal["fr", "ar", "en"]:
    if re.search(r"[\u0600-\u06ff]", message):
        return "ar"

    words = set(
        re.findall(
            r"[a-z0-9]+",
            normaliser(message),
        )
    )

    if words.intersection(DARIJA_LATIN_WORDS):
        return "ar"

    if len(words.intersection(ENGLISH_HINTS)) >= 2:
        return "en"

    return "fr"


def instruction_langue_reponse(
    message: str,
) -> str:
    language = detecter_langue_message(message)

    if language == "ar":
        return (
            "LANGUE IMPOSÉE POUR CETTE RÉPONSE : ARABE CLAIR. "
            "Le dernier message est en arabe ou en darija. "
            "N’utilise pas le français comme langue principale."
        )

    if language == "en":
        return (
            "MANDATORY RESPONSE LANGUAGE: ENGLISH. "
            "Do not reuse the language of previous messages."
        )

    return (
        "LANGUE IMPOSÉE POUR CETTE RÉPONSE : FRANÇAIS. "
        "Réponds exclusivement en français professionnel. "
        "Ignore la langue de l’historique et des documents."
    )


def demande_est_trop_large(
    message: str,
) -> bool:
    normalized_message = normaliser(message)

    if demande_est_definition(message):
        return False

    if any(
        marker in normalized_message
        for marker in BROAD_REQUEST_MARKERS
    ):
        return True

    generic_land_markers = (
        "terrain",
        "foncier",
        "land",
        "lard",
        "العقار",
        "ارض",
        "أرض",
    )

    specific_land_markers = (
        "zone industrielle",
        "zone d activites",
        "lot industriel",
        "attribution",
        "affectation",
        "domaine prive",
        "location",
        "cession",
        "occupation temporaire",
        "domaine public",
        "domaine forestier",
        "avna",
        "vocation non agricole",
        "morcellement",
        "morceler",
        "perimetre d irrigation",
        "note de renseignements urbanistiques",
        "note de renseignements urbanistique",
        "note de renseignement urbanistique",
        "permis de demolition",
        "demolition",
        "demolir",
        "industrial zone",
        "state private land",
        "temporary occupation",
        "منطقة صناعية",
        "الملك الخاص للدولة",
        "احتلال مؤقت",
        "الصبغة غير الفلاحية",
    )

    contains_generic_land_term = any(
        marker in normalized_message
        for marker in generic_land_markers
    )

    contains_specific_land_term = any(
        marker in normalized_message
        for marker in specific_land_markers
    )

    return (
        contains_generic_land_term
        and not contains_specific_land_term
    )


def detecter_categorie_message(
    message: str,
) -> CategoryCode:
    normalized_message = normaliser(message)

    # Certains termes fonciers tr?s g?n?riques, notamment
    # "terrain", peuvent masquer une intention urbanistique
    # explicitement exprim?e.
    urbanisme_priority_terms = (
        "morcellement",
        "morceler",
        "note de renseignements urbanistiques",
        "note de renseignements urbanistique",
        "note de renseignement urbanistique",
        "permis de demolition",
        "demolition",
        "demolir",
    )

    if any(
        normaliser(term) in normalized_message
        for term in urbanisme_priority_terms
    ):
        return "urbanisme"

    for category, terms in CATEGORY_TERMS.items():
        if any(
            normaliser(term) in normalized_message
            for term in terms
        ):
            return category  # type: ignore[return-value]

    return "general"


def adapter_historique_au_dernier_message(
    message: str,
    history: list[dict[str, str]],
) -> list[dict[str, str]]:
    current_category = detecter_categorie_message(
        message
    )

    if (
        demande_est_definition(message)
        and current_category != "general"
    ):
        return []

    previous_user_message = next(
        (
            str(item.get("content", ""))
            for item in reversed(history)
            if item.get("role") == "user"
        ),
        "",
    )

    previous_category = detecter_categorie_message(
        previous_user_message
    )

    if (
        current_category != "general"
        and previous_category != "general"
        and current_category != previous_category
    ):
        return []

    return history


def creer_clarification_large(
    category: str,
    language: str,
) -> str:
    if category == "foncier":
        if language == "ar":
            return (
                "طلبكم يشمل عدة مساطر عقارية. "
                "ما المسطرة التي تريدون الاطلاع عليها؟\n"
                "1. تخصيص بقعة داخل منطقة صناعية أو منطقة للأنشطة\n"
                "2. كراء أو تفويت عقار من الملك الخاص للدولة\n"
                "3. الاحتلال المؤقت للملك العمومي أو الغابوي\n"
                "4. شهادة الصبغة غير الفلاحية"
            )

        if language == "en":
            return (
                "Your request covers several land procedures. "
                "Which one do you need?\n"
                "1. Allocation of a lot in an industrial zone\n"
                "2. Lease or transfer of State private land\n"
                "3. Temporary occupation of public or forest land\n"
                "4. Non-agricultural vocation certificate (AVNA)"
            )

        return (
            "Votre demande couvre plusieurs procédures foncières. "
            "Laquelle souhaitez-vous consulter ?\n"
            "1. Attribution d’un lot en zone industrielle ou d’activités\n"
            "2. Location ou cession d’un terrain du domaine privé de l’État\n"
            "3. Occupation temporaire du domaine public ou forestier\n"
            "4. Attestation de vocation non agricole (AVNA)"
        )

    if language == "ar":
        return (
            "طلبكم يشمل عدة مساطر إدارية. "
            "يرجى تحديد العملية المطلوبة وموقع المشروع."
        )

    if language == "en":
        return (
            "Your request covers several administrative procedures. "
            "Please specify the required procedure and project location."
        )

    return (
        "Votre demande couvre plusieurs procédures administratives. "
        "Veuillez préciser l’opération recherchée ainsi que "
        "la localisation du projet."
    )

def essayer_routage_local_rapide(
    message: str,
    history: list[dict[str, str]],
) -> RoutageDemande | None:
    """
    Court-circuite le LLM uniquement lorsque le routage est
    suffisamment certain.

    Les demandes ambigues continuent vers le routeur LLM.
    """

    category = detecter_categorie_message(message)

    if category == "general":
        return None

    language_code = detecter_langue_message(message)

    if demande_est_trop_large(message):
        return RoutageDemande(
            action="clarify",
            category=category,
            standalone_query="",
            clarification=creer_clarification_large(
                category=category,
                language=language_code,
            ),
        )

    if demande_est_definition(message):
        return RoutageDemande(
            action="search",
            category=category,
            standalone_query=DEFINITION_QUERIES.get(
                category,
                message,
            ),
            clarification="",
        )

    normalized_message = normaliser(message)

    normalized_message = re.sub(
        r"[^a-z0-9 ]+",
        " ",
        normalized_message,
    )

    normalized_message = " ".join(
        normalized_message.split()
    )

    direct_markers = (
        "quelles sont",
        "quels sont",
        "quelle est",
        "quel est",
        "comment",
        "combien",
        "ou trouver",
        "puis je",
        "peut on",
        "pouvons nous",
        "est il possible",
        "je peux",
        "can i",
        "can we",
        "is it possible",
        "wach n9dar",
    )

    specific_markers = (
        "dispositif tpme",
        "prime",
        "primes",
        "permis de construire",
        "zone industrielle",
        "convention d investissement",
        "etude d impact",
        "occupation temporaire",
        "avna",
        "creation d entreprise",
        "creer une entreprise",
        "note de renseignements urbanistiques",
        "note de renseignements urbanistique",
        "note de renseignement urbanistique",
        "permis de demolition",
        "demolition",
        "demolir",
    )

    direct_request = any(
        normalized_message.startswith(marker)
        for marker in direct_markers
    )

    specific_request = any(
        marker in normalized_message
        for marker in specific_markers
    )

    if not direct_request and not specific_request:
        return None

    demolition_request = (
        category == "urbanisme"
        and any(
            marker in normalized_message
            for marker in (
                "permis de demolition",
                "demolition",
                "demolir",
            )
        )
    )

    explicit_demolition_permit = (
        "permis de demolition"
        in normalized_message
    )

    if (
        demolition_request
        and not explicit_demolition_permit
    ):
        standalone_query = (
            "Permis de d\u00e9molition. "
            + message
        )
    else:
        standalone_query = message

    autonomous_explicit_request = (
        direct_request
        and specific_request
    )

    if history and not autonomous_explicit_request:
        effective_history = (
            adapter_historique_au_dernier_message(
                message,
                history,
            )
        )

        if effective_history:
            return None

    return RoutageDemande(
        action="search",
        category=category,
        standalone_query=standalone_query,
        clarification="",
    )


async def analyser_demande(
    message: str,
    history: list[dict[str, str]],
    ollama_base_url: str,
    ollama_model: str,
) -> RoutageDemande:
    fast_routing = essayer_routage_local_rapide(
        message,
        history,
    )

    if fast_routing is not None:
        return fast_routing

    effective_history = (
        adapter_historique_au_dernier_message(
            message,
            history,
        )
    )

    history_text = "\n".join(
        (
            f"{item.get('role', 'unknown')}: "
            f"{item.get('content', '')}"
        )
        for item in effective_history
    ) or "Aucun historique"

    language_code = detecter_langue_message(message)

    language_name = {
        "fr": "français",
        "ar": "arabe clair",
        "en": "anglais",
    }[language_code]

    payload = {
        "model": ollama_model,
        "messages": [
            {
                "role": "system",
                "content": ROUTER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "LANGUE OBLIGATOIRE DE LA CLARIFICATION : "
                    f"{language_name}.\n"
                    "Cette langue dépend uniquement du dernier message.\n\n"
                    f"HISTORIQUE\n{history_text}\n\n"
                    f"DERNIER MESSAGE\n{message}"
                ),
            },
        ],
        "stream": False,
        "think": False,
        "format": "json",
        "keep_alive": "30m",
        "options": {
            "temperature": 0,
            "num_ctx": 4096,
            "num_predict": 260,
        },
    }

    timeout = httpx.Timeout(
        timeout=120.0,
        connect=10.0,
    )

    async with httpx.AsyncClient(
        timeout=timeout,
        trust_env=False,
    ) as client:
        response = await client.post(
            f"{ollama_base_url}/api/chat",
            json=payload,
        )

        response.raise_for_status()

    data = response.json()
    content = data["message"]["content"]
    parsed = extraire_objet_json(content)

    action = str(
        parsed.get("action", "")
    ).strip().lower()

    category = str(
        parsed.get("category", "general")
    ).strip().lower()

    standalone_query = str(
        parsed.get("standalone_query", "")
    ).strip()

    clarification = str(
        parsed.get("clarification", "")
    ).strip()

    if action not in {"clarify", "search"}:
        raise ValueError(
            "Action de routage invalide"
        )

    valid_categories = {
        "foncier",
        "urbanisme",
        "entreprise",
        "exploitation",
        "environnement",
        "incitations",
        "convention",
        "general",
    }

    if category not in valid_categories:
        category = "general"

    detected_current_category = (
        detecter_categorie_message(message)
    )

    if detected_current_category != "general":
        category = detected_current_category

    last_assistant_content = next(
        (
            str(item.get("content", ""))
            for item in reversed(history)
            if item.get("role") == "assistant"
        ),
        "",
    )

    previous_user_content = next(
        (
            str(item.get("content", ""))
            for item in reversed(history)
            if item.get("role") == "user"
        ),
        "",
    )

    answered_numbered_choice = bool(
        re.search(
            r"(?<!\d)[1-4](?!\d)",
            message,
        )
    )

    previous_message_was_question = (
        "?" in last_assistant_content
        or "؟" in last_assistant_content
    )

    # Une réponse à un choix précédent doit continuer vers le RAG,
    # sans provoquer une deuxième clarification.
    if (
        action == "clarify"
        and previous_message_was_question
        and answered_numbered_choice
    ):
        action = "search"

        conversation_text = normaliser(
            " ".join(
                str(item.get("content", ""))
                for item in history
            )
        )

        if category == "general" and any(
            marker in conversation_text
            for marker in (
                "terrain",
                "foncier",
                "zone industrielle",
                "عقار",
                "ارض",
                "أرض",
                "منطقة صناعية",
            )
        ):
            category = "foncier"

        if not standalone_query:
            standalone_query = (
                f"Catégorie administrative : {category}. "
                f"Demande initiale : {previous_user_content}. "
                f"Précision de l’investisseur : {message}."
            )

        clarification = ""

    if demande_est_trop_large(message):
        detected_category = detecter_categorie_message(
            message
        )

        if detected_category != "general":
            category = detected_category

        action = "clarify"
        standalone_query = ""
        clarification = creer_clarification_large(
            category=category,
            language=language_code,
        )

    if demande_est_definition(message):
        definition_category = (
            detecter_categorie_message(message)
        )

        if definition_category != "general":
            action = "search"
            category = definition_category
            standalone_query = DEFINITION_QUERIES.get(
                definition_category,
                message,
            )
            clarification = ""
    # QUESTIONS FERMEES SUFFISAMMENT PRECISES
    # Une demande de faisabilite rattachee a une categorie reconnue
    # doit atteindre le RAG, meme si le modele propose une clarification.
    message_normalise = normaliser(message)
    message_routage = re.sub(
        r"[-‐‑‒–—'’]+",
        " ",
        message_normalise,
    )
    message_routage = " ".join(message_routage.split())

    marqueurs_reponse_directe = (
        "quelles sont",
        "quels sont",
        "quelle est",
        "quel est",
        "comment",
        "combien",
        "ou trouver",
        "puis je",
        "peut on",
        "pouvons nous",
        "est il possible",
        "je peux",
        "can i",
        "can we",
        "is it possible",
        "wach n9dar",
        "واش نقدر",
        "هل يمكن",
    )

    demande_reponse_directe = any(
        message_routage.startswith(marker)
        for marker in marqueurs_reponse_directe
    )

    if (
        action == "clarify"
        and category != "general"
        and not demande_est_trop_large(message)
        and demande_reponse_directe
    ):
        action = "search"
        standalone_query = standalone_query or message
        clarification = ""

    # ROUTAGE DOCUMENTAIRE DETERMINISTE
    # Une demande documentaire suffisamment precise doit interroger
    # la base, meme lorsque son objet n'est pas reconnu par le routeur.
    message_normalise = normaliser(message)

    demande_documentaire_explicite = any(
        terme in message_normalise
        for terme in (
            "document",
            "piece",
            "dossier",
            "procedure",
            "demarche",
            "formalite",
        )
    ) or any(
        terme in message
        for terme in (
            "\u0648\u062b\u0627\u0626\u0642",
            "\u0645\u0633\u062a\u0646\u062f\u0627\u062a",
            "\u0625\u062c\u0631\u0627\u0621\u0627\u062a",
            "\u0645\u0633\u0637\u0631\u0629",
        )
    )

    if (
        action == "clarify"
        and demande_documentaire_explicite
        and standalone_query
    ):
        action = "search"
        clarification = ""

    # RÈGLES DÉTERMINISTES — FORMES JURIDIQUES
    # Ces règles empêchent les confusions entre SAS, SASU,
    # SARL et SARL à associé unique.
    message_forme_juridique = re.sub(
        r"[^a-z0-9]+",
        " ",
        normaliser(message),
    )

    message_forme_juridique = " ".join(
        message_forme_juridique.split()
    )

    tokens_forme_juridique = set(
        message_forme_juridique.split()
    )

    historique_forme_juridique = " ".join(
        str(item.get("content", ""))
        for item in history
    )

    historique_forme_juridique = re.sub(
        r"[^a-z0-9]+",
        " ",
        normaliser(
            historique_forme_juridique
        ),
    )

    historique_forme_juridique = " ".join(
        historique_forme_juridique.split()
    )

    derniere_reponse_assistant = next(
        (
            str(item.get("content", ""))
            for item in reversed(history)
            if item.get("role") == "assistant"
        ),
        "",
    )

    derniere_clarification_forme = re.sub(
        r"[^a-z0-9]+",
        " ",
        normaliser(
            derniere_reponse_assistant
        ),
    )

    derniere_clarification_forme = " ".join(
        derniere_clarification_forme.split()
    )

    reponses_premier_choix = {
        "1",
        "premier",
        "premier choix",
        "le premier choix",
    }

    reponses_second_choix = {
        "2",
        "deuxieme",
        "deuxieme choix",
        "le deuxieme choix",
    }

    reponse_premier_choix = (
        message_forme_juridique
        in reponses_premier_choix
    )

    reponse_second_choix = (
        message_forme_juridique
        in reponses_second_choix
    )

    # --------------------------------------------------------
    # SAS À ASSOCIÉ UNIQUE — SASU
    # --------------------------------------------------------

    aliases_sasu = {
        "sasu",
        "sas u",
        "sas a associe unique",
        "societe par actions simplifiee unipersonnelle",
        "societe par actions simplifiee a associe unique",
    }

    premier_choix_est_sasu = (
        reponse_premier_choix
        and (
            "1 une sas a associe unique"
            in derniere_clarification_forme
            or (
                "1 sas a associe unique"
                in derniere_clarification_forme
            )
            or (
                "1 sasu"
                in derniere_clarification_forme
            )
        )
    )

    selection_sasu = (
        message_forme_juridique
        in aliases_sasu
        or "sasu" in tokens_forme_juridique
        or (
            "sas a associe unique"
            in message_forme_juridique
        )
        or premier_choix_est_sasu
    )

    # --------------------------------------------------------
    # SAS AVEC PLUSIEURS ASSOCIÉS
    # --------------------------------------------------------

    aliases_sas_multi = {
        "sas avec plusieurs associes",
        "sas a plusieurs associes",
        "sas plusieurs associes",
        "societe par actions simplifiee pluripersonnelle",
        "societe par actions simplifiee avec plusieurs associes",
    }

    deuxieme_choix_est_sas_multi = (
        reponse_second_choix
        and (
            "2 une sas avec plusieurs associes"
            in derniere_clarification_forme
            or (
                "2 sas avec plusieurs associes"
                in derniere_clarification_forme
            )
            or (
                "2 une sas a plusieurs associes"
                in derniere_clarification_forme
            )
        )
    )

    selection_sas_multi = (
        message_forme_juridique
        in aliases_sas_multi
        or (
            "sas avec plusieurs associes"
            in message_forme_juridique
        )
        or (
            "sas a plusieurs associes"
            in message_forme_juridique
        )
        or deuxieme_choix_est_sas_multi
    )

    demande_sas_generale = (
        (
            "sas" in tokens_forme_juridique
            or (
                "societe par actions simplifiee"
                in message_forme_juridique
            )
        )
        and not selection_sasu
        and not selection_sas_multi
    )

    # --------------------------------------------------------
    # SARL À ASSOCIÉ UNIQUE
    # --------------------------------------------------------

    aliases_sarl_unique = {
        "sarl au",
        "sarlau",
        "sarlu",
        "sarl a associe unique",
        "sarl associe unique",
        "sarl unipersonnelle",
        "societe a responsabilite limitee unipersonnelle",
        "societe a responsabilite limitee a associe unique",
    }

    premier_choix_est_sarl_unique = (
        reponse_premier_choix
        and (
            "1 une sarl a associe unique"
            in derniere_clarification_forme
            or (
                "1 sarl a associe unique"
                in derniere_clarification_forme
            )
            or (
                "1 une sarl au"
                in derniere_clarification_forme
            )
        )
    )

    selection_sarl_unique = (
        message_forme_juridique
        in aliases_sarl_unique
        or "sarlau" in tokens_forme_juridique
        or "sarlu" in tokens_forme_juridique
        or message_forme_juridique.endswith(
            "sarl au"
        )
        or message_forme_juridique.endswith(
            "sarl a u"
        )
        or (
            "sarl a associe unique"
            in message_forme_juridique
        )
        or (
            "sarl associe unique"
            in message_forme_juridique
        )
        or (
            "sarl unipersonnelle"
            in message_forme_juridique
        )
        or (
            "societe a responsabilite limitee "
            "a associe unique"
            in message_forme_juridique
        )
        or (
            "societe a responsabilite limitee "
            "unipersonnelle"
            in message_forme_juridique
        )
        or premier_choix_est_sarl_unique
    )

    # --------------------------------------------------------
    # SARL AVEC PLUSIEURS ASSOCIÉS
    # --------------------------------------------------------

    aliases_sarl_multi = {
        "sarl avec plusieurs associes",
        "sarl a plusieurs associes",
        "sarl plusieurs associes",
        "societe a responsabilite limitee avec plusieurs associes",
        "societe a responsabilite limitee pluripersonnelle",
    }

    deuxieme_choix_est_sarl_multi = (
        reponse_second_choix
        and (
            "2 une sarl avec plusieurs associes"
            in derniere_clarification_forme
            or (
                "2 sarl avec plusieurs associes"
                in derniere_clarification_forme
            )
            or (
                "2 une sarl a plusieurs associes"
                in derniere_clarification_forme
            )
        )
    )

    selection_sarl_multi = (
        message_forme_juridique
        in aliases_sarl_multi
        or (
            "sarl avec plusieurs associes"
            in message_forme_juridique
        )
        or (
            "sarl a plusieurs associes"
            in message_forme_juridique
        )
        or deuxieme_choix_est_sarl_multi
    )

    demande_sarl_generale = (
        (
            "sarl" in tokens_forme_juridique
            or (
                "societe a responsabilite limitee"
                in message_forme_juridique
            )
        )
        and not selection_sarl_unique
        and not selection_sarl_multi
    )

    # --------------------------------------------------------
    # APPLICATION DES RÈGLES
    # --------------------------------------------------------

    if selection_sasu:
        action = "search"
        category = "entreprise"

        standalone_query = (
            "Création d’entreprise au Maroc auprès du CRI "
            "Guelmim-Oued Noun sous la forme d’une société "
            "par actions simplifiée à associé unique (SASU) : "
            "procédure, formalités et documents officiels."
        )

        clarification = ""

    elif selection_sas_multi:
        action = "search"
        category = "entreprise"

        standalone_query = (
            "Création d’entreprise au Maroc auprès du CRI "
            "Guelmim-Oued Noun sous la forme d’une société "
            "par actions simplifiée avec plusieurs associés "
            "(SAS) : procédure, formalités et documents "
            "officiels."
        )

        clarification = ""

    elif selection_sarl_unique:
        action = "search"
        category = "entreprise"

        standalone_query = (
            "Création d’entreprise au Maroc auprès du CRI "
            "Guelmim-Oued Noun sous la forme d’une société "
            "à responsabilité limitée à associé unique "
            "(SARL AU) : procédure, formalités et documents "
            "officiels."
        )

        clarification = ""

    elif selection_sarl_multi:
        action = "search"
        category = "entreprise"

        standalone_query = (
            "Création d’entreprise au Maroc auprès du CRI "
            "Guelmim-Oued Noun sous la forme d’une société "
            "à responsabilité limitée avec plusieurs associés "
            "(SARL) : procédure, formalités et documents "
            "officiels."
        )

        clarification = ""

    elif demande_sas_generale:
        action = "clarify"
        category = "entreprise"
        standalone_query = ""

        clarification = (
            "Souhaitez-vous créer :\n"
            "1. une SAS à associé unique (SASU) ;\n"
            "2. une SAS avec plusieurs associés ?"
        )

    elif demande_sarl_generale:
        action = "clarify"
        category = "entreprise"
        standalone_query = ""

        clarification = (
            "Souhaitez-vous créer :\n"
            "1. une SARL à associé unique (SARL AU) ;\n"
            "2. une SARL avec plusieurs associés ?"
        )

    # Protection générale contre une requête inventée sur la France.
    contexte_utilisateur = normaliser(
        " ".join(
            [
                message,
                historique_forme_juridique,
            ]
        )
    )

    requete_normalisee = normaliser(
        standalone_query
    )

    if (
        action == "search"
        and category == "entreprise"
        and "france" in requete_normalisee
        and "france" not in contexte_utilisateur
    ):
        standalone_query = (
            "Création d’entreprise au Maroc auprès du CRI "
            "Guelmim-Oued Noun. "
            f"Demande de l’investisseur : {message}."
        )

    if action == "clarify" and not clarification:
        raise ValueError(
            "Question de clarification absente"
        )

    if action == "search" and not standalone_query:
        standalone_query = message

    return RoutageDemande(
        action=action,
        category=category,
        standalone_query=standalone_query,
        clarification=clarification,
    )


CATEGORY_METADATA_ALIASES = {
    "foncier": {
        "foncier",
    },
    "urbanisme": {
        "urbanisme",
        "autorisations urbanistiques",
    },
    "entreprise": {
        "entreprise",
        "creation d entreprise",
        "cr ation d entreprise",
    },
    "exploitation": {
        "exploitation",
        "autorisation d exploitation",
    },
    "environnement": {
        "environnement",
        "acceptabilite des projets",
    },
    "incitations": {
        "incitations",
        "aides et incitations",
        "primes",
    },
    "convention": {
        "convention",
        "conventions d investissement",
        "incitations",
    },
}


def normaliser_etiquette(
    value: str,
) -> str:
    value = normaliser(value)

    value = re.sub(
        r"[^a-z0-9\u0600-\u06ff]+",
        " ",
        value,
    )

    return " ".join(value.split())


def est_document_juridique_transversal(
    metadata: dict,
) -> bool:
    """
    Identifie un texte juridique officiel transversal du CRI.

    La loi n° 47-18 concerne plusieurs catégories à la fois
    (foncier, urbanisme, environnement, incitations, etc.)
    et ne doit donc pas être éliminée uniquement parce qu'elle
    n'a pas de catégorie administrative unique.
    """

    if not isinstance(metadata, dict):
        return False

    metadata_category = normaliser_etiquette(
        str(metadata.get("category", ""))
    )

    # Un document déjà catégorisé reste soumis au filtre normal.
    if metadata_category:
        return False

    official_value = metadata.get("official_source")

    official_source = (
        official_value is True
        or str(official_value).strip().casefold()
        in {
            "1",
            "true",
            "yes",
            "oui",
        }
    )

    if not official_source:
        return False

    legal_reference = normaliser_etiquette(
        str(metadata.get("legal_reference", ""))
    )

    source_title = normaliser_etiquette(
        str(metadata.get("source_title", ""))
    )

    return (
        "47 18" in legal_reference
        or (
            "47 18" in source_title
            and "centre" in source_title
            and "investissement" in source_title
        )
    )

def filtrer_resultats_par_categorie(
    results: list[dict[str, Any]],
    category: str,
) -> list[dict[str, Any]]:
    if category == "general":
        return results

    if category == "creation_entreprise":
        category = "entreprise"

    allowed_categories = (
        CATEGORY_METADATA_ALIASES.get(category)
    )

    if not allowed_categories:
        return []

    normalized_allowed = {
        normaliser_etiquette(value)
        for value in allowed_categories
    }

    categories_by_source: dict[str, set[str]] = {}

    for result in results:
        metadata = result.get("metadata") or {}

        metadata_category = normaliser_etiquette(
            str(metadata.get("category", ""))
        )
        source_url = str(
            metadata.get("source_url", "")
        ).strip()

        if metadata_category and source_url:
            categories_by_source.setdefault(
                source_url,
                set(),
            ).add(metadata_category)

    filtered: list[dict[str, Any]] = []

    for result in results:
        metadata = result.get("metadata") or {}

        metadata_category = normaliser_etiquette(
            str(metadata.get("category", ""))
        )
        source_url = str(
            metadata.get("source_url", "")
        ).strip()

        if metadata_category in normalized_allowed:
            filtered.append(result)
            continue

        # La loi 47-18 est transversale à plusieurs domaines CRI.
        # Elle peut compléter une procédure spécialisée lorsque
        # la recherche vectorielle l'a jugée pertinente.
        if est_document_juridique_transversal(metadata):
            filtered.append(result)
            continue

        if not metadata_category and source_url:
            inferred_categories = categories_by_source.get(
                source_url,
                set(),
            )

            if inferred_categories & normalized_allowed:
                filtered.append(result)

    # Filtrage strict : les anciens chunks sans catégorie
    # sont acceptés uniquement si leur source est classée.
    return filtered