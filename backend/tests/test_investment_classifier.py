from app.investment_audit import (
    InvestorType,
    LandStatus,
    ProjectProfile,
    WorkType,
)
from app.investment_classifier import (
    ClassificationStatus,
    DocumentToClassify,
    classify_document,
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


def test_classifies_company_statutes_from_text():
    result = classify_document(
        create_profile(),
        DocumentToClassify(
            filename="document.pdf",
            extracted_text=(
                "STATUTS DE LA SOCIETE ALPHA SARL"
            ),
        ),
    )

    assert result.status == ClassificationStatus.CLASSIFIED
    assert result.requirement_code == "company_statutes"
    assert result.confidence >= 0.70


def test_classifies_commercial_register():
    result = classify_document(
        create_profile(),
        DocumentToClassify(
            filename="extrait_registre_commerce.pdf",
            extracted_text=(
                "Extrait du registre de commerce de Guelmim"
            ),
        ),
    )

    assert result.status == ClassificationStatus.CLASSIFIED
    assert result.requirement_code == "commercial_register"


def test_classifies_land_ownership_document():
    result = classify_document(
        create_profile(),
        DocumentToClassify(
            filename="titre_foncier.pdf",
            extracted_text=(
                "Certificat de propriété délivré par "
                "la conservation foncière"
            ),
        ),
    )

    assert result.status == ClassificationStatus.CLASSIFIED
    assert result.requirement_code == "land_ownership"


def test_ignores_requirement_not_applicable_to_profile():
    result = classify_document(
        create_profile(
            land_status=LandStatus.TENANT,
        ),
        DocumentToClassify(
            filename="titre_foncier.pdf",
            extracted_text="Certificat de propriété",
        ),
    )

    assert result.status == ClassificationStatus.UNCLASSIFIED
    assert result.requirement_code is None


def test_detects_ambiguous_document():
    result = classify_document(
        create_profile(
            requests_bank_financing=True,
        ),
        DocumentToClassify(
            filename="dossier_financier.pdf",
            extracted_text=(
                "Business plan et plan de financement"
            ),
        ),
    )

    assert result.status == ClassificationStatus.AMBIGUOUS
    assert result.requirement_code is None
    assert len(result.candidates) >= 2


def test_unrelated_document_remains_unclassified():
    result = classify_document(
        create_profile(),
        DocumentToClassify(
            filename="photo_diverse.jpg",
            extracted_text="Image sans information exploitable",
        ),
    )

    assert result.status == ClassificationStatus.UNCLASSIFIED
    assert result.confidence == 0.0


def test_classifies_topographic_plan_from_filename():
    result = classify_document(
        create_profile(
            works=[WorkType.CONSTRUCTION],
        ),
        DocumentToClassify(
            filename="plan_topographique.pdf",
            extracted_text="",
        ),
    )

    assert result.status == ClassificationStatus.CLASSIFIED
    assert result.requirement_code == "topographic_plan"
