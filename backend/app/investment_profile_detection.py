from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from pydantic import BaseModel, Field

from app.investment_audit import ProjectProfile
from app.investment_document_pipeline import (
    process_investment_document,
)
from app.investment_dossier_pipeline import InvestmentPdfInput


class InspectedInvestmentDocument(BaseModel):
    filename: str
    page_count: int
    detected_type: str
    confidence: float
    text_excerpt: str


from app.structured_document_extraction import extract_structured_fields


class DetectedProjectProfile(BaseModel):
    project_name: str | None = None
    promoter_name: str | None = None
    legal_form: str | None = None
    sector: str | None = None
    region: str | None = None
    province: str | None = None
    commune: str | None = None
    investor_type: str | None = None
    land_status: str | None = None
    investment_amount_mad: float | None = None
    planned_jobs: int | None = None
    works: list[str] = Field(default_factory=list)


class ProvisionalDocumentRequirement(BaseModel):
    code: str
    label: str
    category: str
    reason: str


class InvestmentDocumentInspectionResponse(BaseModel):
    documents: list[InspectedInvestmentDocument]
    detected_documents: list[str] = Field(
        default_factory=list
    )
    provisional_missing_documents: list[
        ProvisionalDocumentRequirement
    ] = Field(
        default_factory=list
    )
    documents_to_determine: list[
        ProvisionalDocumentRequirement
    ] = Field(
        default_factory=list
    )
    detected_profile: DetectedProjectProfile
    field_sources: dict[str, list[str]] = Field(
        default_factory=dict
    )
    missing_fields: list[str] = Field(
        default_factory=list
    )
    warning: str = (
        "Les informations détectées par OCR doivent être "
        "vérifiées et confirmées par l'investisseur avant "
        "l'audit complet du dossier."
    )


DOCUMENT_TYPE_RULES = (
    (
        "Pièce d'identité",
        (
            "carte nationale",
            "carte d identite",
            "cin",
            "passeport",
            "royaume du maroc",
        ),
        0.93,
    ),
    (
        "Registre de commerce",
        (
            "registre de commerce",
            "extrait du registre",
            "numero du registre",
        ),
        0.95,
    ),
    (
        "Statuts de société",
        (
            "statuts de la societe",
            "statuts de société",
            "societe a responsabilite limitee",
            "société à responsabilité limitée",
        ),
        0.92,
    ),
    (
        "Certificat négatif",
        (
            "certificat negatif",
            "certificat négatif",
            "denomination commerciale",
        ),
        0.9,
    ),
    (
        "Plan de financement",
        (
            "plan de financement",
            "sources de financement",
            "fonds propres",
            "credit bancaire",
            "crédit bancaire",
        ),
        0.9,
    ),
    (
        "Justificatif foncier",
        (
            "titre foncier",
            "contrat de bail",
            "contrat de location",
            "attestation de propriete",
            "attestation de propriété",
            "acte de propriete",
            "acte de propriété",
        ),
        0.9,
    ),
    (
        "Plan ou document technique",
        (
            "plan de situation",
            "plan de masse",
            "plan topographique",
            "coordonnees",
            "coordonnées",
            "echelle",
            "échelle",
        ),
        0.84,
    ),
    (
        "Présentation du projet",
        (
            "fiche projet",
            "note de presentation",
            "note de présentation",
            "projet d investissement",
            "projet d'investissement",
            "montant de l investissement",
            "montant de l'investissement",
        ),
        0.82,
    ),
)


SECTOR_RULES = (
    (
        "Agroalimentaire",
        (
            "agroalimentaire",
            "agro-industrie",
            "industrie alimentaire",
            "transformation alimentaire",
        ),
    ),
    (
        "Tourisme",
        (
            "tourisme",
            "hotel",
            "hôtel",
            "hebergement touristique",
            "hébergement touristique",
        ),
    ),
    (
        "Énergies renouvelables",
        (
            "energie renouvelable",
            "énergie renouvelable",
            "solaire",
            "photovoltaique",
            "photovoltaïque",
            "eolien",
            "éolien",
            "hydrogene vert",
            "hydrogène vert",
        ),
    ),
    (
        "Industrie",
        (
            "industrie",
            "unite industrielle",
            "unité industrielle",
            "usine",
            "production industrielle",
        ),
    ),
    (
        "Pêche et valorisation des produits de la mer",
        (
            "produits de la mer",
            "poisson",
            "peche",
            "pêche",
            "halieutique",
            "aquaculture",
        ),
    ),
    (
        "Logistique",
        (
            "logistique",
            "transport",
            "entrepot",
            "entrepôt",
            "plateforme logistique",
        ),
    ),
    (
        "Numérique",
        (
            "numerique",
            "numérique",
            "informatique",
            "digital",
            "technologie",
        ),
    ),
    (
        "Commerce et services",
        (
            "commerce",
            "services",
            "prestation",
            "distribution",
        ),
    ),
)


KNOWN_LOCATIONS = (
    ("Guelmim-Oued Noun", "region"),
    ("Guelmim", "province"),
    ("Tan-Tan", "province"),
    ("Sidi Ifni", "province"),
    ("Assa-Zag", "province"),
    ("El Ouatia", "commune"),
    ("Bouizakarne", "commune"),
    ("Lqsabi", "commune"),
    ("Tata", "commune"),
    ("Assa", "commune"),
    ("Zag", "commune"),
)


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value.casefold(),
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    return re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()


def safe_excerpt(text: str) -> str:
    excerpt = re.sub(
        r"\b[A-Z]{1,3}\d{5,10}\b",
        "[identifiant masqué]",
        text,
        flags=re.IGNORECASE,
    )

    excerpt = re.sub(
        r"\b\d{8,}\b",
        "[numéro masqué]",
        excerpt,
    )

    excerpt = re.sub(
        r"\s+",
        " ",
        excerpt,
    ).strip()

    return excerpt[:320]


def detect_document_type(
    filename: str,
    text: str,
) -> tuple[str, float]:
    searchable = normalize_text(
        f"{Path(filename).stem} {text}"
    )

    for label, terms, confidence in DOCUMENT_TYPE_RULES:
        if any(
            normalize_text(term) in searchable
            for term in terms
        ):
            return label, confidence

    return "Document non identifié", 0.25


def clean_detected_value(value: str) -> str:
    cleaned = value.strip(" \t\r\n:;-–—")

    cleaned = re.split(
        r"\s{2,}|\||•",
        cleaned,
        maxsplit=1,
    )[0]

    return cleaned[:250].strip()


def find_labeled_value(
    text: str,
    patterns: tuple[str, ...],
) -> str | None:
    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            value = clean_detected_value(
                match.group(1)
            )

            if len(value) >= 2:
                return value

    return None


def parse_number(value: str) -> float | None:
    cleaned = value.replace(
        "\u00a0",
        " ",
    ).strip()

    million_match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(?:million|millions|mdh)",
        cleaned,
        flags=re.IGNORECASE,
    )

    if million_match:
        number = float(
            million_match.group(1).replace(",", ".")
        )

        return number * 1_000_000

    digits = re.sub(
        r"[^\d]",
        "",
        cleaned,
    )

    if not digits:
        return None

    return float(digits)


def detect_amount(text: str) -> float | None:
    patterns = (
        (
            r"(?:montant\s+(?:total\s+)?de\s+l['’]?"
            r"investissement|investissement\s+total|"
            r"co[uû]t\s+(?:global|total)|"
            r"montant\s+du\s+projet)"
            r"[^0-9]{0,50}"
            r"([0-9][0-9\s.,]*(?:\s*millions?|\s*mdh)?)"
            r"\s*(?:mad|dh|dhs|dirhams)?"
        ),
        (
            r"([0-9]+(?:[.,][0-9]+)?)\s*"
            r"(?:million|millions|mdh)\s*"
            r"(?:mad|dh|dhs|dirhams)?"
        ),
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            amount = parse_number(
                match.group(1)
            )

            if amount and amount > 0:
                return amount

    return None


def detect_jobs(text: str) -> int | None:
    patterns = (
        (
            r"(?:emplois?\s+(?:directs?\s+)?"
            r"(?:pr[eé]vus?|cr[eé][eé]s?)|"
            r"nombre\s+d['’]emplois?|"
            r"postes?\s+d['’]emploi)"
            r"[^0-9]{0,30}(\d{1,6})"
        ),
        (
            r"(\d{1,6})\s+"
            r"(?:emplois?|postes?\s+d['’]emploi)"
        ),
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

    return None


def detect_legal_form(text: str) -> str | None:
    normalized = normalize_text(text)

    forms = (
        ("SARL AU", ("sarl au", "sarl a associe unique")),
        ("SARL", ("sarl", "responsabilite limitee")),
        ("SAS", ("sas", "societe par actions simplifiee")),
        ("SA", ("societe anonyme",)),
        ("SNC", ("societe en nom collectif", "snc")),
        ("Coopérative", ("cooperative",)),
        ("Auto-entrepreneur", ("auto entrepreneur",)),
        ("Personne physique", ("personne physique",)),
    )

    for label, terms in forms:
        if any(
            term in normalized
            for term in terms
        ):
            return label

    return None


def detect_sector(text: str) -> str | None:
    normalized = normalize_text(text)

    for label, terms in SECTOR_RULES:
        if any(
            normalize_text(term) in normalized
            for term in terms
        ):
            return label

    return None


def detect_investor_type(
    text: str,
    document_types: list[str],
) -> str | None:
    normalized = normalize_text(text)

    if "personne physique" in normalized:
        return "personne_physique"

    if "Registre de commerce" in document_types:
        return "societe_existante"

    if detect_legal_form(text):
        return "societe_en_creation"

    return None


def detect_land_status(text: str) -> str | None:
    normalized = normalize_text(text)

    if any(
        term in normalized
        for term in (
            "titre foncier",
            "proprietaire",
            "acte de propriete",
        )
    ):
        return "proprietaire"

    if any(
        term in normalized
        for term in (
            "contrat de bail",
            "contrat de location",
            "locataire",
        )
    ):
        return "locataire"

    if any(
        term in normalized
        for term in (
            "demande d attribution",
            "demande de terrain",
            "attribution fonciere",
        )
    ):
        return "demande_attribution"

    return None


def detect_works(text: str) -> list[str]:
    normalized = normalize_text(text)
    works: list[str] = []

    work_rules = (
        (
            "construction",
            ("construction", "nouvelle unite", "nouvelle unité"),
        ),
        (
            "extension",
            ("extension", "agrandissement"),
        ),
        (
            "modification",
            (
                "modification",
                "reamenagement",
                "réaménagement",
                "changement de nature",
            ),
        ),
        (
            "lotissement_morcellement",
            ("lotissement", "morcellement"),
        ),
    )

    for value, terms in work_rules:
        if any(
            normalize_text(term) in normalized
            for term in terms
        ):
            works.append(value)

    return works



def build_provisional_document_assessment(
    document_types: list[str],
    detected_profile: DetectedProjectProfile,
) -> tuple[
    list[ProvisionalDocumentRequirement],
    list[ProvisionalDocumentRequirement],
]:
    """
    Évalue les pièces probablement manquantes avant que
    l'investisseur complète les informations du projet.

    Le résultat est provisoire. La checklist définitive est
    recalculée après confirmation du profil.
    """
    detected = {
        document_type
        for document_type in document_types
        if document_type
        and document_type != "Document non identifié"
    }

    missing: list[
        ProvisionalDocumentRequirement
    ] = []

    to_determine: list[
        ProvisionalDocumentRequirement
    ] = []

    def has_type(*labels: str) -> bool:
        return any(label in detected for label in labels)

    def add_missing(
        code: str,
        label: str,
        category: str,
        reason: str,
    ) -> None:
        if any(item.code == code for item in missing):
            return

        missing.append(
            ProvisionalDocumentRequirement(
                code=code,
                label=label,
                category=category,
                reason=reason,
            )
        )

    def add_to_determine(
        code: str,
        label: str,
        category: str,
        reason: str,
    ) -> None:
        if any(
            item.code == code
            for item in to_determine
        ):
            return

        to_determine.append(
            ProvisionalDocumentRequirement(
                code=code,
                label=label,
                category=category,
                reason=reason,
            )
        )

    # Pièces générales nécessaires à l'étude du projet.
    if not has_type("Présentation du projet"):
        add_missing(
            code="project_summary",
            label="Fiche synthétique ou présentation du projet",
            category="projet",
            reason=(
                "Présenter l'activité, la localisation, "
                "l'investissement et les emplois prévus."
            ),
        )

    if not has_type(
        "Présentation du projet",
        "Plan de financement",
    ):
        add_missing(
            code="investment_program",
            label="Programme détaillé d'investissement",
            category="projet",
            reason=(
                "Détailler les dépenses, les équipements "
                "et le calendrier prévisionnel."
            ),
        )

    if not has_type(
        "Justificatif foncier",
        "Plan ou document technique",
    ):
        add_missing(
            code="land_or_location_document",
            label=(
                "Justificatif foncier ou document "
                "de localisation"
            ),
            category="foncier",
            reason=(
                "Identifier le terrain ou le lieu "
                "prévu pour le projet."
            ),
        )

    investor_type = detected_profile.investor_type

    if investor_type == "personne_physique":
        if not has_type("Pièce d'identité"):
            add_missing(
                code="investor_identity",
                label="CIN ou passeport de l'investisseur",
                category="identite",
                reason="Identifier le porteur du projet.",
            )

    elif investor_type == "societe_existante":
        if not has_type("Statuts de société"):
            add_missing(
                code="company_statutes",
                label="Statuts à jour de la société",
                category="identite",
                reason=(
                    "Vérifier la forme juridique "
                    "et l'organisation de la société."
                ),
            )

        if not has_type("Registre de commerce"):
            add_missing(
                code="commercial_register",
                label="Extrait récent du registre de commerce",
                category="identite",
                reason=(
                    "Vérifier l'existence juridique "
                    "de la société."
                ),
            )

        if not has_type("Pièce d'identité"):
            add_missing(
                code="legal_representative_identity",
                label=(
                    "CIN ou passeport "
                    "du représentant légal"
                ),
                category="identite",
                reason="Identifier le représentant légal.",
            )

        add_to_determine(
            code="company_ice",
            label="Certificat ICE de la société",
            category="identite",
            reason=(
                "Vérifier si l'ICE a été transmis "
                "dans un document non encore identifié."
            ),
        )

    elif investor_type == "societe_en_creation":
        if not has_type("Pièce d'identité"):
            add_missing(
                code="partners_identity",
                label="CIN ou passeports des associés",
                category="creation_entreprise",
                reason="Identifier les futurs associés.",
            )

        if not has_type("Certificat négatif"):
            add_missing(
                code="negative_certificate",
                label="Certificat négatif",
                category="creation_entreprise",
                reason=(
                    "Justifier la dénomination "
                    "de la future société."
                ),
            )

        if not has_type("Statuts de société"):
            add_missing(
                code="draft_statutes",
                label="Projet de statuts",
                category="creation_entreprise",
                reason=(
                    "Définir la forme juridique "
                    "et l'organisation de la société."
                ),
            )

    else:
        add_to_determine(
            code="investor_legal_documents",
            label=(
                "Pièces juridiques et d'identité "
                "du porteur"
            ),
            category="identite",
            reason=(
                "Les pièces dépendent du type "
                "d'investisseur qui reste à confirmer."
            ),
        )

    land_status = detected_profile.land_status

    if land_status == "proprietaire":
        if not has_type("Justificatif foncier"):
            add_missing(
                code="land_ownership",
                label="Certificat de propriété ou titre foncier",
                category="foncier",
                reason="Justifier la propriété du terrain.",
            )

    elif land_status == "locataire":
        if not has_type("Justificatif foncier"):
            add_missing(
                code="lease_agreement",
                label="Contrat de bail",
                category="foncier",
                reason=(
                    "Justifier le droit d'utilisation "
                    "du terrain."
                ),
            )

            add_missing(
                code="owner_authorization",
                label="Autorisation du propriétaire",
                category="foncier",
                reason=(
                    "Confirmer que le propriétaire "
                    "autorise l'activité et les travaux."
                ),
            )

    elif land_status == "demande_attribution":
        if not has_type("Justificatif foncier"):
            add_missing(
                code="land_allocation_request",
                label="Demande d'attribution du terrain",
                category="foncier",
                reason=(
                    "Justifier la démarche engagée "
                    "pour obtenir le terrain."
                ),
            )

    else:
        add_to_determine(
            code="specific_land_document",
            label=(
                "Pièce foncière adaptée "
                "à la situation du terrain"
            ),
            category="foncier",
            reason=(
                "Le document dépend du statut foncier "
                "qui reste à confirmer."
            ),
        )

    works = set(detected_profile.works)

    if works.intersection(
        {"construction", "extension", "modification"}
    ):
        if not has_type("Plan ou document technique"):
            add_missing(
                code="technical_plans",
                label=(
                    "Plans topographiques "
                    "et architecturaux"
                ),
                category="urbanisme",
                reason=(
                    "Préparer le dossier technique "
                    "correspondant aux travaux."
                ),
            )

            add_missing(
                code="construction_authorization",
                label="Dossier d'autorisation de construire",
                category="urbanisme",
                reason=(
                    "Obtenir l'autorisation "
                    "correspondant aux travaux."
                ),
            )

    elif "lotissement_morcellement" in works:
        if not has_type("Plan ou document technique"):
            add_missing(
                code="subdivision_authorization",
                label=(
                    "Dossier d'autorisation "
                    "de lotir ou de morceler"
                ),
                category="urbanisme",
                reason=(
                    "Contrôler la division "
                    "ou l'aménagement foncier."
                ),
            )

    else:
        add_to_determine(
            code="works_documents",
            label="Plans et autorisations liés aux travaux",
            category="urbanisme",
            reason=(
                "La nécessité dépend de la nature "
                "des travaux qui reste à confirmer."
            ),
        )

    if not has_type("Plan de financement"):
        add_to_determine(
            code="financing_documents",
            label="Plan de financement et pièces bancaires",
            category="financement",
            reason=(
                "Ces pièces deviennent nécessaires "
                "si un financement bancaire est demandé."
            ),
        )

    add_to_determine(
        code="incentive_documents",
        label=(
            "Pièces relatives aux primes "
            "et aides à l'investissement"
        ),
        category="incitations",
        reason=(
            "La nécessité dépend des aides "
            "demandées par l'investisseur."
        ),
    )

    add_to_determine(
        code="environmental_documents",
        label="Documents environnementaux",
        category="environnement",
        reason=(
            "La nécessité dépend de l'activité, "
            "du site et des impacts potentiels."
        ),
    )

    add_to_determine(
        code="sector_authorization",
        label="Autorisation ou agrément sectoriel",
        category="autorisation_sectorielle",
        reason=(
            "La nécessité dépend du caractère "
            "réglementé de l'activité."
        ),
    )

    return missing, to_determine


def inspect_investment_documents(
    documents: list[InvestmentPdfInput],
) -> InvestmentDocumentInspectionResponse:
    if not documents:
        raise ValueError(
            "Au moins un document est obligatoire."
        )

    neutral_profile = ProjectProfile(
        sector="Non détecté",
        region="Guelmim-Oued Noun",
        province="Guelmim",
        commune="Guelmim",
        investor_type="societe_en_creation",
        land_status="non_identifie",
        investment_amount_mad=1,
        planned_jobs=0,
        works=[],
    )

    inspected_documents: list[
        InspectedInvestmentDocument
    ] = []

    document_texts: list[
        tuple[str, str, str]
    ] = []

    for document_input in documents:
        processed = process_investment_document(
            profile=neutral_profile,
            filename=document_input.filename,
            document_content=document_input.pdf_content,
        )

        detected_type, confidence = (
            detect_document_type(
                processed.filename,
                processed.extracted_text,
            )
        )

        inspected_documents.append(
            InspectedInvestmentDocument(
                filename=processed.filename,
                page_count=processed.page_count,
                detected_type=detected_type,
                confidence=confidence,
                text_excerpt=safe_excerpt(
                    processed.extracted_text
                ),
            )
        )

        document_texts.append(
            (
                processed.filename,
                processed.extracted_text,
                detected_type,
            )
        )

    combined_text = "\n\n".join(
        text
        for _, text, _ in document_texts
    )

    document_types = [
        detected_type
        for _, _, detected_type in document_texts
    ]

    detected_profile = DetectedProjectProfile()
    field_sources: dict[str, list[str]] = {}

    def assign(
        field_name: str,
        value,
        source_filename: str,
    ) -> None:
        if value is None:
            return

        if isinstance(value, str) and not value.strip():
            return

        if isinstance(value, list) and not value:
            return

        if getattr(detected_profile, field_name) not in (
            None,
            [],
        ):
            return

        setattr(
            detected_profile,
            field_name,
            value,
        )

        field_sources.setdefault(
            field_name,
            [],
        ).append(source_filename)

    for filename, text, _ in document_texts:
        # Extraction structur?e prioritaire.
        # Les champs explicitement libell?s dans le document
        # sont prioritaires sur les heuristiques globales.
        structured = extract_structured_fields(text)

        # Si le secteur est explicitement indiqu?,
        # conserver cette valeur comme source prioritaire,
        # tout en appliquant la classification m?tier
        # lorsqu'une cat?gorie connue peut ?tre reconnue.
        structured_sector = structured.get("sector")

        if structured_sector:
            structured["sector"] = (
                detect_sector(str(structured_sector))
                or structured_sector
            )

        for field_name in (
            "project_name",
            "promoter_name",
            "sector",
            "investment_amount_mad",
            "planned_jobs",
            "land_status",
            "region",
            "province",
            "commune",
            "investor_type",
        ):
            assign(
                field_name,
                structured.get(field_name),
                filename,
            )

        structured_works = (
            structured.get("works") or []
        )

        if structured_works:
            detected_profile.works = list(
                dict.fromkeys(
                    [
                        *detected_profile.works,
                        *structured_works,
                    ]
                )
            )

            sources = field_sources.setdefault(
                "works",
                [],
            )

            if filename not in sources:
                sources.append(filename)

        project_name = find_labeled_value(
            text,
            (
                r"(?:nom|intitul[eé]|d[eé]signation)\s+"
                r"(?:du\s+)?projet\s*[:\-]\s*([^\n]{2,250})",
                r"projet\s*[:\-]\s*([^\n]{3,250})",
            ),
        )

        promoter_name = find_labeled_value(
            text,
            (
                r"(?:raison\s+sociale|porteur\s+du\s+projet|"
                r"promoteur|investisseur)\s*[:\-]\s*"
                r"([^\n]{2,250})",
            ),
        )

        assign(
            "project_name",
            project_name,
            filename,
        )

        assign(
            "promoter_name",
            promoter_name,
            filename,
        )

        assign(
            "legal_form",
            detect_legal_form(text),
            filename,
        )

        assign(
            "sector",
            detect_sector(text),
            filename,
        )

        assign(
            "investment_amount_mad",
            detect_amount(text),
            filename,
        )

        assign(
            "planned_jobs",
            detect_jobs(text),
            filename,
        )

        assign(
            "land_status",
            detect_land_status(text),
            filename,
        )

        works = detect_works(text)

        if works:
            detected_profile.works = list(
                dict.fromkeys(
                    [
                        *detected_profile.works,
                        *works,
                    ]
                )
            )

            field_sources.setdefault(
                "works",
                [],
            ).append(filename)

        normalized_text = normalize_text(text)

        for location, location_level in KNOWN_LOCATIONS:
            if normalize_text(location) not in normalized_text:
                continue

            if location_level == "region":
                assign(
                    "region",
                    location,
                    filename,
                )

            elif location_level == "province":
                assign(
                    "province",
                    location,
                    filename,
                )

            elif location_level == "commune":
                assign(
                    "commune",
                    location,
                    filename,
                )

    assign(
        "investor_type",
        detect_investor_type(
            combined_text,
            document_types,
        ),
        document_texts[0][0],
    )

    required_fields = (
        "project_name",
        "promoter_name",
        "sector",
        "investment_amount_mad",
        "planned_jobs",
        "investor_type",
        "land_status",
        "works",
        "province",
        "commune",
    )

    missing_fields = [
        field_name
        for field_name in required_fields
        if getattr(
            detected_profile,
            field_name,
        ) in (
            None,
            "",
            [],
        )
    ]

    detected_document_types = list(
        dict.fromkeys(
            detected_type
            for _, _, detected_type in document_texts
        )
    )

    (
        provisional_missing_documents,
        documents_to_determine,
    ) = build_provisional_document_assessment(
        document_types=detected_document_types,
        detected_profile=detected_profile,
    )

    return InvestmentDocumentInspectionResponse(
        documents=inspected_documents,
        detected_documents=detected_document_types,
        provisional_missing_documents=(
            provisional_missing_documents
        ),
        documents_to_determine=documents_to_determine,
        detected_profile=detected_profile,
        field_sources=field_sources,
        missing_fields=missing_fields,
    )
