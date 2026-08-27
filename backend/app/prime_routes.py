from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.prime_calculator import (
    PrimeCalculationError,
    calculate_investment_bonus,
)

from app.services.tpme_prime_calculator import (
    TpmePrimeCalculationError,
    calculate_tpme_investment_bonus,
)


router = APIRouter(
    prefix="/primes",
    tags=["Primes ÃƒÂ  l'investissement"],
)


class PrimeCalculationRequest(BaseModel):
    total_investment_mad: float = Field(
        ...,
        gt=0,
        description="Montant total d'investissement hors taxes en MAD",
    )
    primable_investment_mad: float = Field(
        ...,
        gt=0,
        description="Montant d'investissement primable en MAD",
    )
    stable_jobs: int = Field(
        ...,
        ge=0,
        description="Nombre d'emplois stables crÃƒÂ©ÃƒÂ©s",
    )
    female_payroll_mad: float = Field(
        default=0,
        ge=0,
        description="Masse salariale rÃƒÂ©servÃƒÂ©e aux femmes",
    )
    total_payroll_mad: float = Field(
        default=0,
        ge=0,
        description="Masse salariale totale",
    )
    future_business: bool = False
    sustainable_project: bool = False
    local_integration: bool = False
    province: Literal[
        "Guelmim",
        "Tan-Tan",
        "Sidi Ifni",
        "Assa-Zag",
    ] = Field(
        ...,
        description=(
            "Province d'implantation dans la region "
            "Guelmim-Oued Noun"
        ),
    )
    sector: str | None = None
    renewable_energy_production: bool = False


class PrimeCalculationResponse(BaseModel):
    eligible: bool
    eligibility_details: dict[str, bool]
    total_rate: float
    total_rate_percent: float
    total_bonus_mad: float
    details: list[dict[str, Any]]
    warnings: list[str]
    legal_references: list[dict[str, Any]]

    total_investment_mad: float | None = None
    primable_investment_mad: float | None = None
    stable_jobs: int | None = None
    employment_ratio: float | None = None
    gender_ratio: float | None = None
    raw_rate: float | None = None
    raw_rate_percent: float | None = None
    reason: str | None = None


@router.post(
    "/calculate",
    response_model=PrimeCalculationResponse,
    summary="Calculer les primes ÃƒÂ  l'investissement",
)
def calculate_primes(
    payload: PrimeCalculationRequest,
) -> PrimeCalculationResponse:
    try:
        result = calculate_investment_bonus(
            total_investment_mad=payload.total_investment_mad,
            primable_investment_mad=payload.primable_investment_mad,
            stable_jobs=payload.stable_jobs,
            female_payroll_mad=payload.female_payroll_mad,
            total_payroll_mad=payload.total_payroll_mad,
            future_business=payload.future_business,
            sustainable_project=payload.sustainable_project,
            local_integration=payload.local_integration,
            province=payload.province,
            sector=payload.sector,
            renewable_energy_production=(
                payload.renewable_energy_production
            ),
        )

        return PrimeCalculationResponse(**result)

    except PrimeCalculationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Configuration rÃƒÂ©glementaire introuvable.",
        ) from exc


class TpmePrimeCalculationRequest(BaseModel):
    total_investment_mad: float = Field(
        ...,
        gt=0,
        description="Montant total d'investissement hors taxes en MAD",
    )
    primable_investment_mad: float = Field(
        ...,
        gt=0,
        description="Montant d'investissement primable en MAD",
    )
    stable_jobs: int = Field(
        ...,
        ge=0,
        description="Nombre d'emplois stables crÃ©Ã©s",
    )
    equity_financing_mad: float = Field(
        ...,
        ge=0,
        description="Montant du financement par fonds propres",
    )
    company_age_years: float = Field(
        ...,
        ge=0,
        description="Ã‚ge de l'entreprise en annÃ©es",
    )
    annual_turnover_mad: float | None = Field(
        default=None,
        ge=0,
        description="Chiffre d'affaires annuel hors taxes",
    )
    owned_over_25_by_large_company: bool = False
    has_public_entity_shareholder: bool = False
    activity_eligible: bool = Field(..., description="Activité éligible au dispositif TPME")
    tourism_activity: bool = False
    priority_activity: bool = False
    territorial_category: Literal["A", "B"] | None = None


class TpmePrimeCalculationResponse(BaseModel):
    eligible: bool
    eligibility_details: dict[str, bool]

    total_investment_mad: float
    primable_investment_mad: float
    stable_jobs: int

    employment_ratio: float
    required_employment_ratio: float

    equity_financing_mad: float
    equity_ratio: float

    new_company: bool
    territorial_category: str | None = None

    raw_rate: float
    raw_rate_percent: float
    total_rate: float
    total_rate_percent: float
    total_bonus_mad: float

    details: list[dict[str, Any]]
    warnings: list[str]
    legal_references: list[dict[str, Any]]

    failed_conditions: list[str] = []
    reason: str | None = None


@router.post(
    "/tpme",
    response_model=TpmePrimeCalculationResponse,
    summary="Calculer les primes du dispositif TPME",
)
def calculate_tpme_primes(
    payload: TpmePrimeCalculationRequest,
) -> TpmePrimeCalculationResponse:
    try:
        result = calculate_tpme_investment_bonus(
            total_investment_mad=payload.total_investment_mad,
            primable_investment_mad=payload.primable_investment_mad,
            stable_jobs=payload.stable_jobs,
            equity_financing_mad=payload.equity_financing_mad,
            company_age_years=payload.company_age_years,
            annual_turnover_mad=payload.annual_turnover_mad,
            owned_over_25_by_large_company=(
                payload.owned_over_25_by_large_company
            ),
            has_public_entity_shareholder=(
                payload.has_public_entity_shareholder
            ),
            activity_eligible=payload.activity_eligible,
            tourism_activity=payload.tourism_activity,
            priority_activity=payload.priority_activity,
            territorial_category=payload.territorial_category,
        )

        return TpmePrimeCalculationResponse(**result)

    except TpmePrimeCalculationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Configuration rÃ©glementaire TPME introuvable.",
        ) from exc

@router.get(
    "/tpme/catalog",
    summary="Récupérer le catalogue réglementaire TPME",
)
def get_tpme_catalog() -> dict[str, Any]:
    import json
    from pathlib import Path

    catalog_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "rules"
        / "tpme_activity_catalog.json"
    )

    try:
        return json.loads(catalog_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Catalogue réglementaire TPME introuvable.",
        ) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail="Catalogue réglementaire TPME invalide.",
        ) from exc


from app.services.tpme_primable_calculator import (
    TpmePrimableCalculationError,
)
from app.services.tpme_simulation_service import (
    calculate_tpme_simulation,
)


class TpmeSimulationRequest(BaseModel):
    total_investment_mad: float = Field(
        ...,
        gt=0,
        description="Montant total d'investissement hors taxes en MAD",
    )

    stable_jobs: int = Field(
        ...,
        ge=0,
        description="Nombre d'emplois stables créés",
    )

    equity_financing_mad: float = Field(
        ...,
        ge=0,
        description="Montant du financement par fonds propres",
    )

    company_age_years: float = Field(
        ...,
        ge=0,
        description="Âge de l'entreprise en années",
    )

    annual_turnover_mad: float | None = Field(
        default=None,
        ge=0,
        description="Chiffre d'affaires annuel hors taxes",
    )

    studies_trademarks_processes_mad: float = Field(
        default=0,
        ge=0,
        description=(
            "Frais d'études, enregistrement de marques "
            "et mise au point des procédés"
        ),
    )

    private_land_mad: float = Field(
        default=0,
        ge=0,
        description="Prix du foncier privé",
    )

    vehicles_mad: float = Field(
        default=0,
        ge=0,
        description="Coût des véhicules",
    )

    related_party_investment_mad: float = Field(
        default=0,
        ge=0,
        description=(
            "Dépenses d'investissement réalisées "
            "entre entreprises liées"
        ),
    )

    private_land_eligible: bool = False

    owned_over_25_by_large_company: bool = False
    has_public_entity_shareholder: bool = False

    activity_eligible: bool = Field(
        ...,
        description="Activité éligible au dispositif TPME",
    )

    tourism_activity: bool = False
    priority_activity: bool = False

    territorial_category: Literal["A", "B"] | None = None


class TpmeSimulationResponse(TpmePrimeCalculationResponse):
    primable_breakdown: dict[str, Any]


@router.post(
    "/tpme/simulate",
    response_model=TpmeSimulationResponse,
    summary="Simuler les primes TPME avec montant primable automatique",
)
def simulate_tpme_primes(
    payload: TpmeSimulationRequest,
) -> TpmeSimulationResponse:
    try:
        result = calculate_tpme_simulation(
            total_investment_mad=payload.total_investment_mad,
            stable_jobs=payload.stable_jobs,
            equity_financing_mad=payload.equity_financing_mad,
            company_age_years=payload.company_age_years,
            annual_turnover_mad=payload.annual_turnover_mad,

            studies_trademarks_processes_mad=(
                payload.studies_trademarks_processes_mad
            ),
            private_land_mad=payload.private_land_mad,
            vehicles_mad=payload.vehicles_mad,
            related_party_investment_mad=(
                payload.related_party_investment_mad
            ),
            private_land_eligible=payload.private_land_eligible,

            owned_over_25_by_large_company=(
                payload.owned_over_25_by_large_company
            ),
            has_public_entity_shareholder=(
                payload.has_public_entity_shareholder
            ),

            activity_eligible=payload.activity_eligible,
            tourism_activity=payload.tourism_activity,
            priority_activity=payload.priority_activity,
            territorial_category=payload.territorial_category,
        )

        return TpmeSimulationResponse(**result)

    except (
        TpmePrimeCalculationError,
        TpmePrimableCalculationError,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
