import pytest

from app.services.prime_calculator import (
    PrimeCalculationError,
    calculate_investment_bonus,
)


def test_project_eligible_with_global_cap():
    result = calculate_investment_bonus(
        total_investment_mad=60_000_000,
        primable_investment_mad=50_000_000,
        stable_jobs=120,
        female_payroll_mad=4_000_000,
        total_payroll_mad=10_000_000,
        future_business=True,
        sustainable_project=True,
        province="Guelmim",
        sector="industrie",
    )

    assert result["eligible"] is True
    assert result["employment_ratio"] == 2.0
    assert result["raw_rate_percent"] == 36.0
    assert result["total_rate_percent"] == 30.0
    assert result["total_bonus_mad"] == 15_000_000.0


def test_project_not_eligible():
    result = calculate_investment_bonus(
        total_investment_mad=40_000_000,
        primable_investment_mad=30_000_000,
        stable_jobs=40,

        province="Guelmim",
    )

    assert result["eligible"] is False
    assert result["total_rate_percent"] == 0.0
    assert result["total_bonus_mad"] == 0.0


def test_exactly_50_million_not_eligible_with_only_50_jobs():
    result = calculate_investment_bonus(
        total_investment_mad=50_000_000,
        primable_investment_mad=40_000_000,
        stable_jobs=50,

        province="Guelmim",
    )

    assert result["eligible"] is False


def test_150_jobs_are_sufficient():
    result = calculate_investment_bonus(
        total_investment_mad=20_000_000,
        primable_investment_mad=15_000_000,
        stable_jobs=150,

        province="Guelmim",
    )

    assert result["eligible"] is True


def test_primable_amount_cannot_exceed_total():
    with pytest.raises(PrimeCalculationError):
        calculate_investment_bonus(
            total_investment_mad=60_000_000,
            primable_investment_mad=70_000_000,
            stable_jobs=100,
        )


def test_invalid_guelmim_oued_noun_province():
    with pytest.raises(PrimeCalculationError):
        calculate_investment_bonus(
            total_investment_mad=60_000_000,
            primable_investment_mad=50_000_000,
            stable_jobs=100,
            province="Laayoune",
        )


def test_renewable_energy_amount_cap():
    result = calculate_investment_bonus(
        total_investment_mad=200_000_000,
        primable_investment_mad=150_000_000,
        stable_jobs=700,
        future_business=True,
        sustainable_project=True,
        local_integration=True,
        province="Tan-Tan",
        sector="energies_renouvelables",
        renewable_energy_production=True,
    )

    assert result["eligible"] is True
    assert result["total_rate_percent"] == 30.0
    assert result["total_bonus_mad"] == 30_000_000.0

@pytest.mark.parametrize(
    "province",
    [
        "Guelmim",
        "Tan-Tan",
        "Sidi Ifni",
        "Assa-Zag",
    ],
)
def test_all_guelmim_oued_noun_provinces_receive_15_percent(
    province,
):
    result = calculate_investment_bonus(
        total_investment_mad=60_000_000,
        primable_investment_mad=50_000_000,
        stable_jobs=150,
        province=province,
    )

    territorial_detail = next(
        detail
        for detail in result["details"]
        if detail["code"] == "prime_territoriale_B"
    )

    assert territorial_detail["rate_percent"] == 15.0
    assert territorial_detail["province"] == province
    assert territorial_detail["territorial_category"] == "B"

@pytest.mark.parametrize(
    "sector",
    [
        "Technologies de l'information",
        "Technologies de l’information",
        "informatique",
        "digital",
        "numerique",
    ],
)
def test_digital_sector_aliases_receive_sector_bonus(sector):
    result = calculate_investment_bonus(
        total_investment_mad=60_000_000,
        primable_investment_mad=5_000_000,
        stable_jobs=150,
        province="Guelmim",
        sector=sector,
    )

    sector_detail = next(
        detail
        for detail in result["details"]
        if detail["code"] == "prime_sectorielle"
    )

    assert sector_detail["sector"] == "numerique"
    assert sector_detail["rate_percent"] == 5.0
