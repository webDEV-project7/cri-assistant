from app.investment_audit import (
    InvestorType,
    LandStatus,
    ProjectProfile,
    RequirementLevel,
    WorkType,
)
from app.investment_dossier import (
    DocumentPresenceStatus,
    SubmittedDocument,
    audit_dossier_presence,
)


def create_profile(**overrides) -> ProjectProfile:
    values = {
        "sector": "Industrie agroalimentaire",
        "region": "Guelmim-Oued Noun",
        "province": "Guelmim",
        "commune": "Guelmim",
        "investor_type": InvestorType.EXISTING_COMPANY,
        "land_status": LandStatus.OWNER,
        "investment_amount_mad": 20_000_000,
        "planned_jobs": 80,
        "works": [],
        "requests_incentives": False,
        "requests_bank_financing": False,
        "potential_environmental_impact": False,
        "regulated_activity": False,
    }

    values.update(overrides)
    return ProjectProfile(**values)


def test_empty_dossier_detects_missing_documents():
    report = audit_dossier_presence(
        create_profile(),
        [],
    )

    assert report.summary.missing_required_count > 0
    assert report.summary.missing_conditional_count > 0
    assert report.summary.completeness_percentage == 0.0


def test_submitted_document_is_marked_present():
    report = audit_dossier_presence(
        create_profile(),
        [
            SubmittedDocument(
                filename="statuts.pdf",
                requirement_code="company_statutes",
            )
        ],
    )

    statutes_result = next(
        result
        for result in report.results
        if result.requirement.code == "company_statutes"
    )

    assert (
        statutes_result.status
        == DocumentPresenceStatus.PRESENT_UNVERIFIED
    )
    assert statutes_result.submitted_files == ["statuts.pdf"]


def test_all_scored_documents_produce_complete_dossier():
    empty_report = audit_dossier_presence(
        create_profile(),
        [],
    )

    documents = [
        SubmittedDocument(
            filename=f"{result.requirement.code}.pdf",
            requirement_code=result.requirement.code,
        )
        for result in empty_report.results
        if (
            result.requirement.level
            != RequirementLevel.RECOMMENDED
        )
    ]

    complete_report = audit_dossier_presence(
        create_profile(),
        documents,
    )

    assert (
        complete_report.summary.completeness_percentage
        == 100.0
    )
    assert complete_report.summary.missing_required_count == 0
    assert complete_report.summary.missing_conditional_count == 0


def test_recommended_document_does_not_reduce_score():
    report = audit_dossier_presence(
        create_profile(),
        [],
    )

    assert report.summary.recommended_absent_count > 0
    assert all(
        result.status
        == DocumentPresenceStatus.RECOMMENDED_ABSENT
        for result in report.results
        if (
            result.requirement.level
            == RequirementLevel.RECOMMENDED
        )
    )


def test_unclassified_document_is_reported():
    report = audit_dossier_presence(
        create_profile(),
        [
            SubmittedDocument(
                filename="document_inconnu.pdf",
            )
        ],
    )

    assert report.unclassified_documents == [
        "document_inconnu.pdf"
    ]
    assert report.summary.unclassified_document_count == 1


def test_unknown_requirement_code_is_reported():
    report = audit_dossier_presence(
        create_profile(),
        [
            SubmittedDocument(
                filename="piece.pdf",
                requirement_code="code_inexistant",
            )
        ],
    )

    assert report.unknown_requirement_codes == [
        "code_inexistant"
    ]
    assert (
        report.summary.unknown_requirement_code_count
        == 1
    )


def test_duplicate_documents_are_reported():
    report = audit_dossier_presence(
        create_profile(),
        [
            SubmittedDocument(
                filename="statuts_version_1.pdf",
                requirement_code="company_statutes",
            ),
            SubmittedDocument(
                filename="statuts_version_2.pdf",
                requirement_code="company_statutes",
            ),
        ],
    )

    assert report.summary.duplicate_requirement_count == 1
    assert (
        report.duplicates[0].requirement_code
        == "company_statutes"
    )
    assert report.duplicates[0].filenames == [
        "statuts_version_1.pdf",
        "statuts_version_2.pdf",
    ]


def test_tenant_dossier_uses_tenant_requirements():
    report = audit_dossier_presence(
        create_profile(
            land_status=LandStatus.TENANT,
            works=[WorkType.CONSTRUCTION],
        ),
        [],
    )

    result_codes = {
        result.requirement.code
        for result in report.results
    }

    assert "lease_agreement" in result_codes
    assert "owner_authorization" in result_codes
    assert "construction_authorization" in result_codes
    assert "land_ownership" not in result_codes
