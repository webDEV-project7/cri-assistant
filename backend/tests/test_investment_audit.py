from app.investment_audit import (
    InvestorType,
    LandStatus,
    ProjectProfile,
    WorkType,
    build_project_checklist,
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


def requirement_codes(profile: ProjectProfile) -> set[str]:
    checklist = build_project_checklist(profile)

    return {
        requirement.code
        for requirement in checklist.requirements
    }


def test_existing_company_requires_legal_documents():
    codes = requirement_codes(create_profile())

    assert "company_statutes" in codes
    assert "commercial_register" in codes
    assert "company_ice" in codes
    assert "legal_representative_identity" in codes
    assert "partners_identity" not in codes


def test_tenant_requires_lease_and_owner_authorization():
    codes = requirement_codes(
        create_profile(
            land_status=LandStatus.TENANT,
        )
    )

    assert "lease_agreement" in codes
    assert "owner_authorization" in codes
    assert "land_ownership" not in codes


def test_construction_generates_urbanism_requirements():
    codes = requirement_codes(
        create_profile(
            works=[WorkType.CONSTRUCTION],
        )
    )

    assert "topographic_plan" in codes
    assert "architectural_plans" in codes
    assert "construction_authorization" in codes


def test_no_works_does_not_request_construction_authorization():
    codes = requirement_codes(
        create_profile(
            works=[WorkType.NO_WORKS],
        )
    )

    assert "construction_authorization" not in codes
    assert "architectural_plans" not in codes


def test_environmental_impact_generates_environmental_documents():
    codes = requirement_codes(
        create_profile(
            potential_environmental_impact=True,
        )
    )

    assert "environmental_impact_study" in codes
    assert "environmental_acceptability" in codes


def test_incentives_generate_specific_requirements():
    codes = requirement_codes(
        create_profile(
            requests_incentives=True,
        )
    )

    assert "incentive_application" in codes
    assert "eligible_expenses" in codes
    assert "jobs_commitment" in codes
    assert "funding_evidence" in codes


def test_requirement_codes_are_unique():
    checklist = build_project_checklist(
        create_profile(
            works=[
                WorkType.CONSTRUCTION,
                WorkType.EXTENSION,
            ],
            requests_incentives=True,
            requests_bank_financing=True,
            potential_environmental_impact=True,
            regulated_activity=True,
        )
    )

    codes = [
        requirement.code
        for requirement in checklist.requirements
    ]

    assert len(codes) == len(set(codes))
