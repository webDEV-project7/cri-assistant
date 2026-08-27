from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.tpme_prime_calculator import (
    calculate_tpme_investment_bonus,
)
from app.services.tpme_primable_calculator import (
    calculate_tpme_primable_investment,
)


def calculate_tpme_simulation(
    *,
    total_investment_mad: Decimal | int | float | str,
    stable_jobs: int,
    equity_financing_mad: Decimal | int | float | str,
    company_age_years: Decimal | int | float | str,
    annual_turnover_mad: Decimal | int | float | str | None = None,

    studies_trademarks_processes_mad: Decimal | int | float | str = 0,
    private_land_mad: Decimal | int | float | str = 0,
    vehicles_mad: Decimal | int | float | str = 0,
    related_party_investment_mad: Decimal | int | float | str = 0,
    private_land_eligible: bool = False,

    owned_over_25_by_large_company: bool = False,
    has_public_entity_shareholder: bool = False,

    activity_eligible: bool,
    tourism_activity: bool = False,
    priority_activity: bool = False,
    territorial_category: str | None = None,
) -> dict[str, Any]:
    """
    Simulation complète du dispositif TPME.

    1. Calcul automatique du montant d'investissement primable.
    2. Utilisation de ce montant pour le calcul réglementaire
       des primes TPME.

    Le montant primable n'est jamais fourni directement par
    l'utilisateur.
    """

    primable_result = calculate_tpme_primable_investment(
        total_investment_mad=total_investment_mad,
        studies_trademarks_processes_mad=(
            studies_trademarks_processes_mad
        ),
        private_land_mad=private_land_mad,
        vehicles_mad=vehicles_mad,
        related_party_investment_mad=(
            related_party_investment_mad
        ),
        private_land_eligible=private_land_eligible,
    )

    bonus_result = calculate_tpme_investment_bonus(
        total_investment_mad=total_investment_mad,
        primable_investment_mad=(
            primable_result["primable_investment_mad"]
        ),
        stable_jobs=stable_jobs,
        equity_financing_mad=equity_financing_mad,
        company_age_years=company_age_years,
        annual_turnover_mad=annual_turnover_mad,
        owned_over_25_by_large_company=(
            owned_over_25_by_large_company
        ),
        has_public_entity_shareholder=(
            has_public_entity_shareholder
        ),
        activity_eligible=activity_eligible,
        tourism_activity=tourism_activity,
        priority_activity=priority_activity,
        territorial_category=territorial_category,
    )

    return {
        **bonus_result,
        "primable_breakdown": primable_result,
    }