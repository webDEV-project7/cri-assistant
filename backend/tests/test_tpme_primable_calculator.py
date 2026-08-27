import pytest

from app.services.tpme_primable_calculator import (
    TpmePrimableCalculationError,
    calculate_tpme_primable_investment,
)


def test_primable_equals_total_when_all_expenses_are_eligible():
    result = calculate_tpme_primable_investment(
        total_investment_mad=10_000_000,
    )

    assert result["primable_investment_mad"] == 10_000_000.0


def test_vehicles_are_excluded_from_primable_amount():
    result = calculate_tpme_primable_investment(
        total_investment_mad=10_000_000,
        vehicles_mad=1_000_000,
    )

    assert result["primable_investment_mad"] == 9_000_000.0
    assert result["excluded_vehicles_mad"] == 1_000_000.0


def test_related_party_investment_is_excluded():
    result = calculate_tpme_primable_investment(
        total_investment_mad=10_000_000,
        related_party_investment_mad=2_000_000,
    )

    assert result["primable_investment_mad"] == 8_000_000.0
    assert (
        result["excluded_related_party_investment_mad"]
        == 2_000_000.0
    )


def test_studies_are_limited_to_five_percent_of_primable_amount():
    result = calculate_tpme_primable_investment(
        total_investment_mad=10_000_000,
        studies_trademarks_processes_mad=1_000_000,
    )

    assert result["primable_investment_mad"] == pytest.approx(
        9_473_684.21,
        abs=0.02,
    )
    assert result["eligible_studies_mad"] == pytest.approx(
        473_684.21,
        abs=0.02,
    )


def test_studies_are_limited_to_absolute_cap_of_500000_mad():
    result = calculate_tpme_primable_investment(
        total_investment_mad=20_000_000,
        studies_trademarks_processes_mad=2_000_000,
    )

    assert result["primable_investment_mad"] == 18_500_000.0
    assert result["eligible_studies_mad"] == 500_000.0
    assert result["excluded_studies_mad"] == 1_500_000.0


def test_private_land_is_excluded_when_not_eligible():
    result = calculate_tpme_primable_investment(
        total_investment_mad=10_000_000,
        private_land_mad=2_000_000,
        private_land_eligible=False,
    )

    assert result["primable_investment_mad"] == 8_000_000.0
    assert result["eligible_private_land_mad"] == 0.0
    assert result["excluded_private_land_mad"] == 2_000_000.0


def test_private_land_is_limited_to_twenty_percent_of_primable_amount():
    result = calculate_tpme_primable_investment(
        total_investment_mad=10_000_000,
        private_land_mad=4_000_000,
        private_land_eligible=True,
    )

    assert result["primable_investment_mad"] == pytest.approx(
        7_500_000.0,
        abs=0.02,
    )
    assert result["eligible_private_land_mad"] == pytest.approx(
        1_500_000.0,
        abs=0.02,
    )


def test_private_land_is_limited_to_absolute_cap_of_5_million():
    result = calculate_tpme_primable_investment(
        total_investment_mad=40_000_000,
        private_land_mad=10_000_000,
        private_land_eligible=True,
    )

    assert result["primable_investment_mad"] == 35_000_000.0
    assert result["eligible_private_land_mad"] == 5_000_000.0
    assert result["excluded_private_land_mad"] == 5_000_000.0


def test_detailed_components_cannot_exceed_total_investment():
    with pytest.raises(TpmePrimableCalculationError):
        calculate_tpme_primable_investment(
            total_investment_mad=10_000_000,
            studies_trademarks_processes_mad=3_000_000,
            private_land_mad=4_000_000,
            vehicles_mad=2_000_000,
            related_party_investment_mad=2_000_000,
        )