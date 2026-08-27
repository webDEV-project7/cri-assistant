import pytest

from app.services.tpme_simulation_service import (
    calculate_tpme_simulation,
)


def test_simulation_calculates_primable_automatically():
    result = calculate_tpme_simulation(
        total_investment_mad=10_000_000,
        vehicles_mad=1_000_000,
        stable_jobs=30,
        equity_financing_mad=2_000_000,
        company_age_years=2,
        activity_eligible=True,
        territorial_category="B",
        priority_activity=True,
    )

    assert result["eligible"] is True

    assert result["primable_investment_mad"] == 9_000_000.0

    assert (
        result["primable_breakdown"]["excluded_vehicles_mad"]
        == 1_000_000.0
    )

    assert result["total_rate_percent"] == 30.0
    assert result["total_bonus_mad"] == 2_700_000.0


def test_simulation_applies_studies_cap_before_bonus():
    result = calculate_tpme_simulation(
        total_investment_mad=10_000_000,
        studies_trademarks_processes_mad=1_000_000,
        stable_jobs=30,
        equity_financing_mad=2_000_000,
        company_age_years=2,
        activity_eligible=True,
        territorial_category="B",
        priority_activity=True,
    )

    assert result["primable_investment_mad"] == pytest.approx(
        9_473_684.21,
        abs=0.02,
    )

    assert result["primable_breakdown"][
        "eligible_studies_mad"
    ] == pytest.approx(
        473_684.21,
        abs=0.02,
    )

    assert result["total_rate_percent"] == 30.0

    assert result["total_bonus_mad"] == pytest.approx(
        2_842_105.26,
        abs=0.02,
    )


def test_simulation_excludes_related_party_expenses():
    result = calculate_tpme_simulation(
        total_investment_mad=10_000_000,
        related_party_investment_mad=2_000_000,
        stable_jobs=30,
        equity_financing_mad=2_000_000,
        company_age_years=2,
        activity_eligible=True,
        territorial_category="B",
        priority_activity=True,
    )

    assert result["primable_investment_mad"] == 8_000_000.0

    assert result["primable_breakdown"][
        "excluded_related_party_investment_mad"
    ] == 2_000_000.0

    assert result["total_rate_percent"] == 30.0
    assert result["total_bonus_mad"] == 2_400_000.0