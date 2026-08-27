from enum import Enum

from pydantic import BaseModel, Field


class InvestorType(str, Enum):
    INDIVIDUAL = "personne_physique"
    EXISTING_COMPANY = "societe_existante"
    COMPANY_IN_CREATION = "societe_en_creation"


class LandStatus(str, Enum):
    OWNER = "proprietaire"
    TENANT = "locataire"
    ALLOCATION_REQUESTED = "demande_attribution"
    NOT_IDENTIFIED = "non_identifie"


class WorkType(str, Enum):
    NO_WORKS = "aucuns_travaux"
    CONSTRUCTION = "construction"
    EXTENSION = "extension"
    MODIFICATION = "modification"
    SUBDIVISION = "lotissement_morcellement"


class RequirementLevel(str, Enum):
    REQUIRED = "obligatoire"
    CONDITIONAL = "conditionnelle"
    RECOMMENDED = "recommandee"


class ProjectProfile(BaseModel):
    project_name: str | None = Field(
        default=None,
        max_length=250,
    )
    promoter_name: str | None = Field(
        default=None,
        max_length=250,
    )
    identity_document_number: str | None = Field(
        default=None,
        max_length=50,
    )
    legal_form: str | None = Field(
        default=None,
        max_length=100,
    )
    sector: str = Field(
        min_length=2,
        max_length=150,
    )
    region: str = Field(
        min_length=2,
        max_length=150,
    )
    province: str = Field(
        min_length=2,
        max_length=150,
    )
    commune: str = Field(
        min_length=2,
        max_length=150,
    )
    investor_type: InvestorType
    land_status: LandStatus
    investment_amount_mad: float = Field(gt=0)
    planned_jobs: int = Field(ge=0)
    works: list[WorkType] = Field(default_factory=list)
    requests_incentives: bool = False
    requests_bank_financing: bool = False
    potential_environmental_impact: bool = False
    regulated_activity: bool = False


class ChecklistRequirement(BaseModel):
    code: str
    label: str
    category: str
    level: RequirementLevel
    reason: str
    authority: str | None = None
    source_reference: str | None = None


class ProjectChecklist(BaseModel):
    project_profile: ProjectProfile
    requirements: list[ChecklistRequirement]
    warning: str = (
        "Cette checklist est une aide préparatoire. "
        "La validation administrative définitive reste humaine."
    )


def build_project_checklist(
    profile: ProjectProfile,
) -> ProjectChecklist:
    requirements: list[ChecklistRequirement] = []

    def add(
        code: str,
        label: str,
        category: str,
        level: RequirementLevel,
        reason: str,
        authority: str | None = None,
        source_reference: str | None = None,
    ) -> None:
        requirements.append(
            ChecklistRequirement(
                code=code,
                label=label,
                category=category,
                level=level,
                reason=reason,
                authority=authority,
                source_reference=source_reference,
            )
        )

    # Pièces d'identification
    if profile.investor_type == InvestorType.INDIVIDUAL:
        add(
            code="investor_identity",
            label="CIN ou passeport de l'investisseur",
            category="identite",
            level=RequirementLevel.REQUIRED,
            reason="Identifier le porteur du projet.",
        )

    elif profile.investor_type == InvestorType.EXISTING_COMPANY:
        company_documents = (
            (
                "company_statutes",
                "Statuts à jour de la société",
            ),
            (
                "commercial_register",
                "Extrait récent du registre de commerce",
            ),
            (
                "company_ice",
                "Certificat ICE de la société",
            ),
            (
                "legal_representative_identity",
                "CIN ou passeport du représentant légal",
            ),
        )

        for code, label in company_documents:
            add(
                code=code,
                label=label,
                category="identite",
                level=RequirementLevel.REQUIRED,
                reason=(
                    "Vérifier l'existence juridique de la société "
                    "et l'identité de son représentant."
                ),
            )

    elif profile.investor_type == InvestorType.COMPANY_IN_CREATION:
        creation_documents = (
            (
                "partners_identity",
                "CIN ou passeports des associés",
            ),
            (
                "negative_certificate",
                "Certificat négatif",
            ),
            (
                "draft_statutes",
                "Projet de statuts",
            ),
            (
                "planned_shareholding",
                "Répartition prévisionnelle du capital",
            ),
        )

        for code, label in creation_documents:
            add(
                code=code,
                label=label,
                category="creation_entreprise",
                level=RequirementLevel.CONDITIONAL,
                reason="Constituer et identifier la future société.",
                authority="OMPIC",
            )

    # Présentation générale du projet
    add(
        code="project_summary",
        label="Fiche synthétique du projet",
        category="projet",
        level=RequirementLevel.REQUIRED,
        reason=(
            "Décrire l'activité, la localisation, "
            "l'investissement et les emplois prévus."
        ),
    )

    add(
        code="investment_program",
        label="Programme détaillé d'investissement",
        category="projet",
        level=RequirementLevel.REQUIRED,
        reason="Identifier les dépenses et le calendrier du projet.",
    )

    add(
        code="project_schedule",
        label="Calendrier prévisionnel de réalisation",
        category="projet",
        level=RequirementLevel.RECOMMENDED,
        reason="Planifier les principales phases de réalisation.",
    )

    # Situation foncière
    if profile.land_status == LandStatus.OWNER:
        add(
            code="land_ownership",
            label="Certificat de propriété ou titre foncier récent",
            category="foncier",
            level=RequirementLevel.CONDITIONAL,
            reason="Justifier la maîtrise foncière du terrain.",
            authority="Conservation foncière",
        )

    elif profile.land_status == LandStatus.TENANT:
        add(
            code="lease_agreement",
            label="Contrat de bail",
            category="foncier",
            level=RequirementLevel.CONDITIONAL,
            reason="Justifier le droit d'utilisation du terrain.",
        )
        add(
            code="owner_authorization",
            label="Accord du propriétaire pour réaliser le projet",
            category="foncier",
            level=RequirementLevel.CONDITIONAL,
            reason=(
                "Vérifier que le propriétaire autorise "
                "l'activité et les travaux envisagés."
            ),
        )

    elif profile.land_status == LandStatus.ALLOCATION_REQUESTED:
        add(
            code="land_allocation_request",
            label="Demande d'attribution du terrain",
            category="foncier",
            level=RequirementLevel.CONDITIONAL,
            reason="Engager la procédure d'attribution foncière.",
            authority="CRI ou gestionnaire de la zone",
        )

    elif profile.land_status == LandStatus.NOT_IDENTIFIED:
        add(
            code="land_requirement_note",
            label="Note décrivant les besoins fonciers du projet",
            category="foncier",
            level=RequirementLevel.RECOMMENDED,
            reason=(
                "Rechercher un terrain compatible avec "
                "l'activité et les besoins du projet."
            ),
        )

    # Urbanisme et travaux
    active_works = set(profile.works)
    construction_works = {
        WorkType.CONSTRUCTION,
        WorkType.EXTENSION,
        WorkType.MODIFICATION,
    }

    if active_works.intersection(construction_works):
        add(
            code="topographic_plan",
            label="Plan topographique du terrain",
            category="urbanisme",
            level=RequirementLevel.CONDITIONAL,
            reason="Préparer et vérifier le dossier technique.",
        )
        add(
            code="architectural_plans",
            label="Plans architecturaux signés",
            category="urbanisme",
            level=RequirementLevel.CONDITIONAL,
            reason="Décrire les constructions projetées.",
        )
        add(
            code="construction_authorization",
            label="Dossier d'autorisation de construire",
            category="urbanisme",
            level=RequirementLevel.CONDITIONAL,
            reason="Obtenir l'autorisation correspondant aux travaux.",
            authority="Commune ou guichet compétent",
        )

    if (
        WorkType.EXTENSION in active_works
        or WorkType.MODIFICATION in active_works
    ):
        add(
            code="previous_authorization",
            label="Ancienne autorisation et plans approuvés",
            category="urbanisme",
            level=RequirementLevel.CONDITIONAL,
            reason=(
                "Comparer la situation autorisée "
                "avec l'extension ou la modification projetée."
            ),
        )

    if WorkType.SUBDIVISION in active_works:
        add(
            code="subdivision_authorization",
            label="Dossier d'autorisation de lotir ou de morceler",
            category="urbanisme",
            level=RequirementLevel.CONDITIONAL,
            reason="Contrôler la division ou l'aménagement foncier.",
        )

    # Environnement
    add(
        code="environmental_screening",
        label="Fiche de qualification environnementale",
        category="environnement",
        level=RequirementLevel.RECOMMENDED,
        reason=(
            "Déterminer si le projet est soumis à une procédure "
            "environnementale particulière."
        ),
    )

    if profile.potential_environmental_impact:
        add(
            code="environmental_impact_study",
            label="Étude d'impact sur l'environnement",
            category="environnement",
            level=RequirementLevel.CONDITIONAL,
            reason=(
                "Évaluer les impacts et les mesures "
                "d'atténuation du projet."
            ),
            authority="Autorité environnementale compétente",
        )
        add(
            code="environmental_acceptability",
            label="Décision d'acceptabilité environnementale",
            category="environnement",
            level=RequirementLevel.CONDITIONAL,
            reason=(
                "Justifier l'aboutissement de la procédure "
                "environnementale applicable."
            ),
        )

    # Activité réglementée
    if profile.regulated_activity:
        add(
            code="sector_authorization",
            label="Autorisation ou agrément sectoriel",
            category="autorisation_sectorielle",
            level=RequirementLevel.CONDITIONAL,
            reason=(
                "Vérifier les conditions particulières "
                "applicables au secteur d'activité."
            ),
            authority="Administration sectorielle compétente",
        )

    # Financement bancaire
    if profile.requests_bank_financing:
        bank_documents = (
            (
                "business_plan",
                "Étude technico-économique ou business plan",
            ),
            (
                "financing_plan",
                "Plan de financement",
            ),
            (
                "financial_statements",
                "États financiers disponibles",
            ),
            (
                "proforma_invoices",
                "Devis et factures pro forma",
            ),
        )

        for code, label in bank_documents:
            add(
                code=code,
                label=label,
                category="financement",
                level=RequirementLevel.CONDITIONAL,
                reason="Justifier la viabilité et le besoin de financement.",
            )

    # Primes et aides à l'investissement
    if profile.requests_incentives:
        incentive_documents = (
            (
                "incentive_application",
                "Demande de prime ou d'aide à l'investissement",
            ),
            (
                "eligible_expenses",
                "Détail des dépenses éligibles",
            ),
            (
                "jobs_commitment",
                "Prévisions et engagements en matière d'emplois",
            ),
            (
                "funding_evidence",
                "Justificatifs des fonds propres et du financement",
            ),
        )

        for code, label in incentive_documents:
            add(
                code=code,
                label=label,
                category="incitations",
                level=RequirementLevel.CONDITIONAL,
                reason=(
                    "Évaluer l'éligibilité du projet "
                    "au dispositif d'aide demandé."
                ),
                authority="CRI et administrations compétentes",
            )

    return ProjectChecklist(
        project_profile=profile,
        requirements=requirements,
    )
