import re
import unicodedata
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from app.investment_audit import (
    ProjectProfile,
    build_project_checklist,
)


class ClassificationStatus(str, Enum):
    CLASSIFIED = "classe"
    AMBIGUOUS = "ambigu"
    UNCLASSIFIED = "non_classe"


class DocumentToClassify(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    extracted_text: str = ""


class ClassificationCandidate(BaseModel):
    requirement_code: str
    requirement_label: str
    score: int
    matched_terms: list[str] = Field(default_factory=list)


class DocumentClassificationResult(BaseModel):
    filename: str
    status: ClassificationStatus
    requirement_code: str | None = None
    confidence: float = Field(ge=0, le=1)
    candidates: list[ClassificationCandidate] = Field(
        default_factory=list
    )
    explanation: str


CLASSIFICATION_RULES: dict[str, tuple[str, ...]] = {
    "investor_identity": (
        "carte nationale d identite",
        "cin",
        "passeport",
    ),
    "company_statutes": (
        "statuts",
        "statuts de la societe",
        "societe a responsabilite limitee",
    ),
    "commercial_register": (
        "registre de commerce",
        "extrait du registre de commerce",
        "immatriculation au registre de commerce",
    ),
    "company_ice": (
        "identifiant commun de l entreprise",
        "certificat ice",
        "ice",
    ),
    "legal_representative_identity": (
        "carte nationale d identite",
        "cin",
        "passeport",
        "representant legal",
    ),
    "partners_identity": (
        "identite des associes",
        "cin des associes",
        "passeports des associes",
    ),
    "negative_certificate": (
        "certificat negatif",
        "ompic",
    ),
    "draft_statutes": (
        "projet de statuts",
        "statuts en cours de constitution",
    ),
    "planned_shareholding": (
        "repartition du capital",
        "actionnariat previsionnel",
        "parts sociales",
    ),
    "project_summary": (
        "fiche synthetique du projet",
        "fiche projet",
        "presentation du projet",
    ),
    "investment_program": (
        "programme d investissement",
        "detail des investissements",
    ),
    "project_schedule": (
        "calendrier previsionnel",
        "planning de realisation",
        "chronogramme",
    ),
    "land_ownership": (
        "certificat de propriete",
        "titre foncier",
        "conservation fonciere",
    ),
    "lease_agreement": (
        "contrat de bail",
        "bail commercial",
        "bail professionnel",
    ),
    "owner_authorization": (
        "autorisation du proprietaire",
        "accord du proprietaire",
    ),
    "land_allocation_request": (
        "demande d attribution",
        "attribution du terrain",
    ),
    "land_requirement_note": (
        "besoins fonciers",
        "recherche de terrain",
    ),
    "topographic_plan": (
        "plan topographique",
        "leve topographique",
    ),
    "architectural_plans": (
        "plan architectural",
        "plans architecturaux",
        "plan de masse",
    ),
    "construction_authorization": (
        "autorisation de construire",
        "permis de construire",
    ),
    "previous_authorization": (
        "ancienne autorisation",
        "plans approuves",
    ),
    "subdivision_authorization": (
        "autorisation de lotir",
        "autorisation de morceler",
        "dossier de lotissement",
    ),
    "environmental_screening": (
        "fiche de qualification environnementale",
        "screening environnemental",
    ),
    "environmental_impact_study": (
        "etude d impact sur l environnement",
        "eie",
    ),
    "environmental_acceptability": (
        "acceptabilite environnementale",
        "decision environnementale",
    ),
    "sector_authorization": (
        "autorisation sectorielle",
        "agrement sectoriel",
        "agrement sanitaire",
    ),
    "business_plan": (
        "business plan",
        "etude technico economique",
    ),
    "financing_plan": (
        "plan de financement",
        "schema de financement",
    ),
    "financial_statements": (
        "etats financiers",
        "bilan comptable",
        "compte de produits et charges",
    ),
    "proforma_invoices": (
        "facture pro forma",
        "facture proforma",
        "devis estimatif",
    ),
    "incentive_application": (
        "demande de prime",
        "demande d aide a l investissement",
    ),
    "eligible_expenses": (
        "depenses eligibles",
        "assiette primable",
    ),
    "jobs_commitment": (
        "engagement de creation d emplois",
        "emplois prevus",
    ),
    "funding_evidence": (
        "justificatif des fonds propres",
        "attestation de financement",
        "accord de financement",
    ),
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)

    without_accents = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        without_accents.lower(),
    ).strip()


def contains_term(text: str, term: str) -> bool:
    normalized_term = normalize_text(term)

    return (
        f" {normalized_term} "
        in f" {text} "
    )


def classify_document(
    profile: ProjectProfile,
    document: DocumentToClassify,
) -> DocumentClassificationResult:
    checklist = build_project_checklist(profile)

    applicable_requirements = {
        requirement.code: requirement
        for requirement in checklist.requirements
    }

    filename_text = normalize_text(
        Path(document.filename).stem
    )
    content_text = normalize_text(
        document.extracted_text
    )

    candidates: list[ClassificationCandidate] = []

    for requirement_code, terms in CLASSIFICATION_RULES.items():
        requirement = applicable_requirements.get(
            requirement_code
        )

        if requirement is None:
            continue

        score = 0
        matched_terms: list[str] = []

        for term in terms:
            if contains_term(filename_text, term):
                score += 4
                matched_terms.append(
                    f"nom du fichier : {term}"
                )

            if contains_term(content_text, term):
                score += 2
                matched_terms.append(
                    f"texte : {term}"
                )

        if score > 0:
            candidates.append(
                ClassificationCandidate(
                    requirement_code=requirement_code,
                    requirement_label=requirement.label,
                    score=score,
                    matched_terms=matched_terms,
                )
            )

    candidates.sort(
        key=lambda candidate: (
            -candidate.score,
            candidate.requirement_code,
        )
    )

    if not candidates:
        return DocumentClassificationResult(
            filename=document.filename,
            status=ClassificationStatus.UNCLASSIFIED,
            confidence=0.0,
            candidates=[],
            explanation=(
                "Aucun indice suffisamment pertinent n'a été "
                "trouvé dans le nom du fichier ou le texte."
            ),
        )

    best_candidate = candidates[0]

    second_score = (
        candidates[1].score
        if len(candidates) > 1
        else 0
    )

    top_candidates = [
        candidate
        for candidate in candidates
        if candidate.score == best_candidate.score
    ]

    if len(top_candidates) > 1:
        confidence = min(
            0.69,
            round(
                0.40 + best_candidate.score * 0.05,
                2,
            ),
        )

        return DocumentClassificationResult(
            filename=document.filename,
            status=ClassificationStatus.AMBIGUOUS,
            confidence=confidence,
            candidates=candidates[:3],
            explanation=(
                "Plusieurs types de documents obtiennent "
                "le même score. Une vérification est nécessaire."
            ),
        )

    score_margin = best_candidate.score - second_score

    confidence = min(
        0.99,
        round(
            0.60
            + min(best_candidate.score, 6) * 0.05
            + min(score_margin, 4) * 0.03,
            2,
        ),
    )

    return DocumentClassificationResult(
        filename=document.filename,
        status=ClassificationStatus.CLASSIFIED,
        requirement_code=best_candidate.requirement_code,
        confidence=confidence,
        candidates=candidates[:3],
        explanation=(
            "Le classement est fondé sur les indices trouvés "
            "dans le nom du fichier et le texte extrait."
        ),
    )


def classify_documents(
    profile: ProjectProfile,
    documents: list[DocumentToClassify],
) -> list[DocumentClassificationResult]:
    return [
        classify_document(profile, document)
        for document in documents
    ]
