import pytest

from app.services.tpme_prime_calculator import (
    TpmePrimeCalculationError,
    calculate_tpme_investment_bonus,
)


def test_tpme_project_eligible():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=30,
        equity_financing_mad=2_000_000,
        company_age_years=2,
        activity_eligible=True,
        territorial_category="B",
        priority_activity=True,
    )

    assert result["eligible"] is True
    assert result["employment_ratio"] == 3.0
    assert result["total_rate_percent"] == 30.0
    assert result["total_bonus_mad"] == 2_400_000.0


def test_tpme_minimum_investment_is_eligible():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=1_000_000,
        primable_investment_mad=1_000_000,
        stable_jobs=2,
        equity_financing_mad=100_000,
        company_age_years=1,
        activity_eligible=True,
    )

    assert result["eligible"] is True


def test_tpme_50_million_is_not_eligible():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=50_000_000,
        primable_investment_mad=40_000_000,
        stable_jobs=100,
        equity_financing_mad=5_000_000,
        company_age_years=1,
        activity_eligible=True,
    )

    assert result["eligible"] is False
    assert (
        result["eligibility_details"]["investment_amount"]
        is False
    )


def test_general_activity_requires_ratio_1_5():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=14,
        equity_financing_mad=1_000_000,
        company_age_years=1,
        activity_eligible=True,
    )

    assert result["employment_ratio"] == 1.4
    assert result["eligible"] is False


def test_tourism_activity_requires_ratio_1():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=10,
        equity_financing_mad=1_000_000,
        company_age_years=1,
        activity_eligible=True,
        tourism_activity=True,
    )

    assert result["employment_ratio"] == 1.0
    assert result["eligible"] is True


def test_equity_financing_must_be_at_least_10_percent():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=20,
        equity_financing_mad=999_999,
        company_age_years=1,
        activity_eligible=True,
    )

    assert result["eligible"] is False
    assert (
        result["eligibility_details"]["equity_financing"]
        is False
    )


def test_existing_company_requires_turnover():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=20,
        equity_financing_mad=1_000_000,
        company_age_years=5,
        annual_turnover_mad=None,
        activity_eligible=True,
    )

    assert result["eligible"] is False
    assert (
        result["eligibility_details"]["turnover_or_new_company"]
        is False
    )


@pytest.mark.parametrize(
    "turnover",
    [
        1_000_000,
        50_000_000,
        199_999_999,
    ],
)
def test_existing_company_valid_turnover(turnover):
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=20,
        equity_financing_mad=1_000_000,
        company_age_years=5,
        annual_turnover_mad=turnover,
        activity_eligible=True,
    )

    assert result["eligible"] is True


def test_turnover_200_million_is_not_tpme():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=20,
        equity_financing_mad=1_000_000,
        company_age_years=5,
        annual_turnover_mad=200_000_000,
        activity_eligible=True,
    )

    assert result["eligible"] is False


def test_large_company_ownership_is_not_eligible():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=20,
        equity_financing_mad=1_000_000,
        company_age_years=1,
        activity_eligible=True,
        owned_over_25_by_large_company=True,
    )

    assert result["eligible"] is False


def test_public_entity_shareholder_is_not_eligible():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=20,
        equity_financing_mad=1_000_000,
        company_age_years=1,
        activity_eligible=True,
        has_public_entity_shareholder=True,
    )

    assert result["eligible"] is False


def test_non_eligible_activity_is_rejected():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=20,
        equity_financing_mad=1_000_000,
        company_age_years=1,
        activity_eligible=False,
    )

    assert result["eligible"] is False


@pytest.mark.parametrize(
    ("stable_jobs", "expected_rate"),
    [
        (20, 5.0),
        (50, 5.0),
        (51, 7.0),
        (100, 7.0),
        (101, 10.0),
    ],
)
def test_employment_bonus_thresholds(
    stable_jobs,
    expected_rate,
):
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=stable_jobs,
        equity_financing_mad=1_000_000,
        company_age_years=1,
        activity_eligible=True,
    )

    detail = next(
        item
        for item in result["details"]
        if item["code"] == "prime_emplois_stables"
    )

    assert detail["rate_percent"] == expected_rate


def test_category_a_adds_10_percent():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=20,
        equity_financing_mad=1_000_000,
        company_age_years=1,
        activity_eligible=True,
        territorial_category="A",
    )

    assert result["total_rate_percent"] == 15.0


def test_category_b_adds_15_percent():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=20,
        equity_financing_mad=1_000_000,
        company_age_years=1,
        activity_eligible=True,
        territorial_category="B",
    )

    assert result["total_rate_percent"] == 20.0


def test_priority_activity_adds_10_percent():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=20,
        equity_financing_mad=1_000_000,
        company_age_years=1,
        activity_eligible=True,
        priority_activity=True,
    )

    assert result["total_rate_percent"] == 15.0


def test_global_cap_is_30_percent():
    result = calculate_tpme_investment_bonus(
        total_investment_mad=10_000_000,
        primable_investment_mad=8_000_000,
        stable_jobs=110,
        equity_financing_mad=1_000_000,
        company_age_years=1,
        activity_eligible=True,
        territorial_category="B",
        priority_activity=True,
    )

    assert result["raw_rate_percent"] == 35.0
    assert result["total_rate_percent"] == 30.0
    assert result["total_bonus_mad"] == 2_400_000.0


def test_primable_amount_cannot_exceed_total():
    with pytest.raises(TpmePrimeCalculationError):
        calculate_tpme_investment_bonus(
            total_investment_mad=10_000_000,
            primable_investment_mad=11_000_000,
            stable_jobs=20,
            equity_financing_mad=1_000_000,
            company_age_years=1,
            activity_eligible=True,
        )


def test_invalid_territorial_category():
    with pytest.raises(TpmePrimeCalculationError):
        calculate_tpme_investment_bonus(
            total_investment_mad=10_000_000,
            primable_investment_mad=8_000_000,
            stable_jobs=20,
            equity_financing_mad=1_000_000,
            company_age_years=1,
            activity_eligible=True,
            territorial_category="C",
        )
