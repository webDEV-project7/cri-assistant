from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalize_token(value: str) -> str:
    value = value.replace("’", "'").replace("`", "'")

    normalized = unicodedata.normalize(
        "NFKD",
        value.casefold(),
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    return normalized.strip(
        " \t\r\n:;-–—"
    )


def find_labeled_line_value(
    text: str,
    labels: tuple[str, ...],
    *,
    min_length: int = 1,
) -> str | None:
    """
    Extrait une valeur associee a un libelle.

    Formats supportes :
        Commune Assa
        Commune: Assa
        Commune - Assa

    ainsi que :
        Commune
        Assa

    Les libelles les plus specifiques sont prioritaires.
    """

    def word_matches(value: str):
        return list(
            re.finditer(
                r"[^\W_]+",
                value,
                flags=re.UNICODE,
            )
        )

    def looks_like_section_heading(
        value: str,
    ) -> bool:
        stripped = value.strip()

        return bool(
            re.match(
                r"^\d+\s*[\.\)]\s*",
                stripped,
            )
        )

    field_prefixes = (
        "nom du projet",
        "intitule du projet",
        "designation du projet",
        "raison sociale",
        "porteur du projet",
        "promoteur",
        "cin",
        "passeport",
        "forme juridique",
        "statut juridique",
        "secteur",
        "activite principale",
        "branche d activite",
        "region",
        "province",
        "prefecture",
        "commune",
        "municipalite",
        "ville d implantation",
        "montant",
        "investissement total",
        "cout global",
        "cout total",
        "budget",
        "emplois",
        "nombre d emplois",
        "postes",
        "type d investisseur",
        "situation fonciere",
        "statut foncier",
        "nature des travaux",
        "type de travaux",
        "travaux prevus",
    )

    def looks_like_another_field(
        value: str,
    ) -> bool:
        normalized = normalize_token(
            value
        )

        normalized = re.sub(
            r"['?_-]+",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return any(
            normalized == prefix
            or normalized.startswith(
                prefix + " "
            )
            for prefix in field_prefixes
        )

    raw_lines = text.splitlines()

    prepared_lines = []

    for line_index, raw_line in enumerate(
        raw_lines
    ):
        line = raw_line.strip()

        if not line:
            continue

        matches = word_matches(line)

        tokens = [
            (
                match,
                normalize_token(
                    match.group(0)
                ),
            )
            for match in matches
        ]

        tokens = [
            item
            for item in tokens
            if item[1]
        ]

        if not tokens:
            continue

        starts = [0]

        if tokens[0][1].isdigit():
            starts.append(1)

        prepared_lines.append(
            (
                line_index,
                line,
                tokens,
                starts,
            )
        )

    prepared_labels = []

    for order, label in enumerate(labels):
        label_tokens = [
            normalize_token(
                match.group(0)
            )
            for match in word_matches(label)
        ]

        label_tokens = [
            token
            for token in label_tokens
            if token
        ]

        if label_tokens:
            prepared_labels.append(
                (
                    label_tokens,
                    order,
                )
            )

    prepared_labels.sort(
        key=lambda item: (
            -len(item[0]),
            item[1],
        )
    )

    for label_tokens, _ in prepared_labels:
        for (
            line_index,
            line,
            tokens,
            starts,
        ) in prepared_lines:

            for start_index in starts:
                end_index = (
                    start_index
                    + len(label_tokens)
                )

                if end_index > len(tokens):
                    continue

                current = [
                    item[1]
                    for item in tokens[
                        start_index:end_index
                    ]
                ]

                if current != label_tokens:
                    continue

                # ------------------------------------------
                # Cas 1 :
                # libelle + valeur sur la meme ligne
                # ------------------------------------------
                if end_index < len(tokens):
                    value_start = tokens[
                        end_index
                    ][0].start()

                    value = line[
                        value_start:
                    ].strip()

                    value = value.lstrip(
                        ":;-?? "
                    ).strip()

                    if len(value) >= min_length:
                        return value

                # ------------------------------------------
                # Cas 2 :
                # libelle seul puis valeur ligne suivante
                # ------------------------------------------
                for next_index in range(
                    line_index + 1,
                    len(raw_lines),
                ):
                    candidate = (
                        raw_lines[next_index]
                        .strip()
                    )

                    if not candidate:
                        continue

                    if looks_like_section_heading(
                        candidate
                    ):
                        break

                    if candidate.startswith(
                        ("-", "?")
                    ):
                        break

                    if looks_like_another_field(
                        candidate
                    ):
                        break

                    if (
                        len(candidate)
                        >= min_length
                    ):
                        return candidate

                    break

    return None


def parse_amount_mad(
    value: str | None,
) -> float | None:
    if not value:
        return None

    normalized = normalize_token(value)

    multiplier = 1.0

    if re.search(
        r"\b(?:mdh|million|millions)\b",
        normalized,
    ):
        multiplier = 1_000_000.0

    match = re.search(
        r"\d[\d\s\u00a0.,]*",
        value,
    )

    if not match:
        return None

    number = (
        match.group(0)
        .replace("\u00a0", "")
        .replace(" ", "")
        .strip(".,")
    )

    if not number:
        return None

    # 500.000 / 5,000,000 / 1.234.567
    if re.fullmatch(
        r"\d{1,3}(?:[.,]\d{3})+",
        number,
    ):
        number = re.sub(
            r"[.,]",
            "",
            number,
        )

    elif (
        number.count(",") == 1
        and number.count(".") == 0
    ):
        left, right = number.split(",")

        if multiplier == 1_000_000.0:
            number = left + "." + right
        elif len(right) == 3:
            number = left + right
        else:
            number = left + "." + right

    elif (
        number.count(".") == 1
        and number.count(",") == 0
    ):
        left, right = number.split(".")

        if (
            multiplier == 1.0
            and len(right) == 3
        ):
            number = left + right

    elif (
        "," in number
        and "." in number
    ):
        last_comma = number.rfind(",")
        last_dot = number.rfind(".")

        decimal_separator = (
            ","
            if last_comma > last_dot
            else "."
        )

        thousands_separator = (
            "."
            if decimal_separator == ","
            else ","
        )

        number = number.replace(
            thousands_separator,
            "",
        )

        if decimal_separator == ",":
            number = number.replace(
                ",",
                ".",
            )

    try:
        amount = float(number)
    except ValueError:
        return None

    amount *= multiplier

    return amount if amount > 0 else None


def parse_integer(
    value: str | None,
) -> int | None:
    if not value:
        return None

    match = re.search(
        r"\d{1,7}",
        value,
    )

    if not match:
        return None

    return int(match.group(0))


def normalize_land_status(
    value: str | None,
) -> str | None:
    if not value:
        return None

    normalized = normalize_token(value)

    if any(
        term in normalized
        for term in (
            "non identifie",
            "non determine",
            "a determiner",
            "aucun terrain",
        )
    ):
        return "non_identifie"

    if any(
        term in normalized
        for term in (
            "proprietaire",
            "propriete",
            "titre foncier",
        )
    ):
        return "proprietaire"

    if any(
        term in normalized
        for term in (
            "locataire",
            "location",
            "bail",
        )
    ):
        return "locataire"

    if any(
        term in normalized
        for term in (
            "demande attribution",
            "demande d'attribution",
            "attribution",
        )
    ):
        return "demande_attribution"

    return None


def normalize_works(
    value: str | None,
) -> list[str]:
    if not value:
        return []

    normalized = (
        normalize_token(value)
        .replace("_", " ")
    )

    if any(
        term in normalized
        for term in (
            "aucuns travaux",
            "aucun travaux",
            "aucun travail",
            "sans travaux",
            "pas de travaux",
            "pas de travail",
        )
    ):
        return ["aucuns_travaux"]

    works: list[str] = []

    rules = (
        (
            "construction",
            (
                "construction",
                "nouvelle unite",
            ),
        ),
        (
            "extension",
            (
                "extension",
                "agrandissement",
            ),
        ),
        (
            "modification",
            (
                "modification",
                "reamenagement",
                "amenagement",
            ),
        ),
        (
            "lotissement_morcellement",
            (
                "lotissement",
                "morcellement",
            ),
        ),
    )

    for work_type, terms in rules:
        if any(
            term in normalized
            for term in terms
        ):
            works.append(work_type)

    return list(dict.fromkeys(works))


def normalize_investor_type(
    value: str | None,
) -> str | None:
    if not value:
        return None

    normalized = normalize_token(value)

    if (
        "societe" in normalized
        and any(
            term in normalized
            for term in (
                "creation",
                "a creer",
                "nouvelle",
            )
        )
    ):
        return "societe_en_creation"

    if (
        "societe" in normalized
        or "entreprise" in normalized
    ):
        return "societe_existante"

    if (
        "personne physique"
        in normalized
    ):
        return "personne_physique"

    return None


def find_quoted_project_name(
    text: str,
) -> str | None:
    patterns = (
        r"\bprojet\s*[«\"]\s*([^»\"\n]{1,250})",
        r"\bprojet\s*[“]\s*([^”\n]{1,250})",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip()

            if value:
                return value

    return None


def extract_structured_fields(
    text: str,
) -> dict[str, Any]:
    """
    Extraction prioritaire des champs explicitement libellés.

    Cette fonction ne classe pas sémantiquement un document.
    Elle restitue d'abord ce qui est réellement écrit.
    """

    result: dict[str, Any] = {}

    project_name = find_labeled_line_value(
        text,
        (
            "Nom du projet",
            "Intitulé du projet",
            "Intitule du projet",
            "Désignation du projet",
            "Designation du projet",
        ),
    )

    if not project_name:
        project_name = (
            find_quoted_project_name(text)
        )

    promoter_name = find_labeled_line_value(
        text,
        (
            "Raison sociale",
            "Porteur du projet",
            "Promoteur",
            "Nom du promoteur",
            "Nom de l'investisseur",
            "Nom de l’investisseur",
        ),
        min_length=1,
    )

    identity_number = find_labeled_line_value(
        text,
        (
            "CIN / Passeport",
            "CIN/Passeport",
            "Numéro CIN",
            "Numero CIN",
            "CIN",
            "Passeport",
        ),
    )

    legal_form = find_labeled_line_value(
        text,
        (
            "Forme juridique",
            "Statut juridique",
        ),
    )

    sector = find_labeled_line_value(
        text,
        (
            "Secteur d'activité",
            "Secteur d’activité",
            "Secteur",
            "Activité principale",
            "Activite principale",
            "Branche d'activité",
            "Branche d’activité",
        ),
    )

    region = find_labeled_line_value(
        text,
        (
            "Région d'implantation",
            "Région d’implantation",
            "Region d'implantation",
            "Région",
            "Region",
        ),
    )

    province = find_labeled_line_value(
        text,
        (
            "Province / Préfecture",
            "Province / Prefecture",
            "Province",
            "Préfecture",
            "Prefecture",
        ),
    )

    commune = find_labeled_line_value(
        text,
        (
            "Commune",
            "Municipalité",
            "Municipalite",
            "Ville d'implantation",
            "Ville d’implantation",
        ),
    )

    # Les mentions comme "(categorie A)" ou
    # "(categorie B)" qualifient le territoire mais ne
    # font pas partie du nom de la region/province/commune.
    def clean_location(value: str | None):
        if not value:
            return value

        return re.sub(
            r"\s*\(\s*cat[e?]gorie\s+[A-Za-z0-9]+\s*\)\s*$",
            "",
            value,
            flags=re.IGNORECASE,
        ).strip()

    region = clean_location(region)
    province = clean_location(province)
    commune = clean_location(commune)

    amount_raw = find_labeled_line_value(
        text,
        (
            "Montant d'investissement",
            "Montant d’investissement",
            "Montant de l'investissement",
            "Montant de l’investissement",
            "Investissement total",
            "Montant total de l'investissement",
            "Montant total de l’investissement",
            "Montant du projet",
            "Coût global",
            "Cout global",
            "Coût total",
            "Cout total",
            "Budget d'investissement",
            "Budget d’investissement",
            "Budget du projet",
        ),
    )

    jobs_raw = find_labeled_line_value(
        text,
        (
            "Emplois prévus",
            "Emplois prevus",
            "Nombre d'emplois",
            "Nombre d’emplois",
            "Emplois créés",
            "Emplois crees",
            "Postes créés",
            "Postes crees",
            "Postes d'emploi",
            "Postes d’emploi",
        ),
    )

    investor_raw = find_labeled_line_value(
        text,
        (
            "Type d'investisseur",
            "Type d’investisseur",
            "Type investisseur",
        ),
    )

    land_raw = find_labeled_line_value(
        text,
        (
            "Situation foncière",
            "Situation fonciere",
            "Statut foncier",
        ),
    )

    works_raw = find_labeled_line_value(
        text,
        (
            "Nature des travaux",
            "Type de travaux",
            "Travaux prévus",
            "Travaux prevus",
        ),
    )

    values = {
        "project_name": project_name,
        "promoter_name": promoter_name,
        "identity_document_number": (
            identity_number.upper()
            if identity_number
            else None
        ),
        "legal_form": legal_form,
        "sector": sector,
        "region": region,
        "province": province,
        "commune": commune,
        "investment_amount_mad": (
            parse_amount_mad(amount_raw)
        ),
        "planned_jobs": (
            parse_integer(jobs_raw)
        ),
        "investor_type": (
            normalize_investor_type(
                investor_raw
            )
        ),
        "land_status": (
            normalize_land_status(
                land_raw
            )
        ),
        "works": normalize_works(
            works_raw
        ),
    }

    for field_name, value in values.items():
        if value is None:
            continue

        if isinstance(value, str):
            if not value.strip():
                continue

        if isinstance(value, list):
            if not value:
                continue

        result[field_name] = value

    return result