from collections import defaultdict
from enum import Enum

from pydantic import BaseModel, Field

from app.investment_audit import (
    ChecklistRequirement,
    ProjectProfile,
    RequirementLevel,
    build_project_checklist,
)


class DocumentPresenceStatus(str, Enum):
    PRESENT_UNVERIFIED = "presente_non_verifiee"
    MISSING = "manquante"
    RECOMMENDED_ABSENT = "recommandee_absente"


class SubmittedDocument(BaseModel):
    filename: str = Field(
        min_length=1,
        max_length=255,
    )
    requirement_code: str | None = None
    content_sha256: str | None = None


class RequirementAuditResult(BaseModel):
    requirement: ChecklistRequirement
    status: DocumentPresenceStatus
    submitted_files: list[str] = Field(default_factory=list)


class DuplicateSubmission(BaseModel):
    requirement_code: str
    filenames: list[str]


class DossierAuditSummary(BaseModel):
    submitted_document_count: int
    applicable_requirement_count: int
    present_requirement_count: int
    missing_required_count: int
    missing_conditional_count: int
    recommended_absent_count: int
    unclassified_document_count: int
    unknown_requirement_code_count: int
    duplicate_requirement_count: int
    completeness_percentage: float


class DossierAuditReport(BaseModel):
    project_profile: ProjectProfile
    results: list[RequirementAuditResult]
    summary: DossierAuditSummary
    unclassified_documents: list[str] = Field(default_factory=list)
    unknown_requirement_codes: list[str] = Field(default_factory=list)
    duplicates: list[DuplicateSubmission] = Field(default_factory=list)
    warning: str = (
        "La présence d'un fichier ne signifie pas encore que la pièce "
        "est valide ou conforme. Le contenu devra être vérifié par OCR "
        "et par les règles de contrôle documentaire."
    )


def audit_dossier_presence(
    profile: ProjectProfile,
    documents: list[SubmittedDocument],
) -> DossierAuditReport:
    checklist = build_project_checklist(profile)

    requirements_by_code = {
        requirement.code: requirement
        for requirement in checklist.requirements
    }

    files_by_requirement: dict[str, list[str]] = defaultdict(list)
    unclassified_documents: list[str] = []
    unknown_requirement_codes: set[str] = set()

    for document in documents:
        requirement_code = (
            document.requirement_code or ""
        ).strip()

        if not requirement_code:
            unclassified_documents.append(document.filename)
            continue

        if requirement_code not in requirements_by_code:
            unknown_requirement_codes.add(requirement_code)
            continue

        files_by_requirement[requirement_code].append(
            document.filename
        )

    results: list[RequirementAuditResult] = []

    missing_required_count = 0
    missing_conditional_count = 0
    recommended_absent_count = 0
    present_requirement_count = 0

    scored_requirement_count = 0
    scored_present_count = 0

    for requirement in checklist.requirements:
        submitted_files = files_by_requirement.get(
            requirement.code,
            [],
        )

        is_scored = (
            requirement.level
            != RequirementLevel.RECOMMENDED
        )

        if is_scored:
            scored_requirement_count += 1

        if submitted_files:
            status = DocumentPresenceStatus.PRESENT_UNVERIFIED
            present_requirement_count += 1

            if is_scored:
                scored_present_count += 1

        elif requirement.level == RequirementLevel.REQUIRED:
            status = DocumentPresenceStatus.MISSING
            missing_required_count += 1

        elif requirement.level == RequirementLevel.CONDITIONAL:
            status = DocumentPresenceStatus.MISSING
            missing_conditional_count += 1

        else:
            status = DocumentPresenceStatus.RECOMMENDED_ABSENT
            recommended_absent_count += 1

        results.append(
            RequirementAuditResult(
                requirement=requirement,
                status=status,
                submitted_files=submitted_files,
            )
        )

    duplicates = [
        DuplicateSubmission(
            requirement_code=requirement_code,
            filenames=filenames,
        )
        for requirement_code, filenames
        in sorted(files_by_requirement.items())
        if len(filenames) > 1
    ]

    if scored_requirement_count:
        completeness_percentage = round(
            100
            * scored_present_count
            / scored_requirement_count,
            2,
        )
    else:
        completeness_percentage = 100.0

    summary = DossierAuditSummary(
        submitted_document_count=len(documents),
        applicable_requirement_count=len(
            checklist.requirements
        ),
        present_requirement_count=present_requirement_count,
        missing_required_count=missing_required_count,
        missing_conditional_count=missing_conditional_count,
        recommended_absent_count=recommended_absent_count,
        unclassified_document_count=len(
            unclassified_documents
        ),
        unknown_requirement_code_count=len(
            unknown_requirement_codes
        ),
        duplicate_requirement_count=len(duplicates),
        completeness_percentage=completeness_percentage,
    )

    return DossierAuditReport(
        project_profile=profile,
        results=results,
        summary=summary,
        unclassified_documents=unclassified_documents,
        unknown_requirement_codes=sorted(
            unknown_requirement_codes
        ),
        duplicates=duplicates,
    )
