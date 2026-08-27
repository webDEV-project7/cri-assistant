from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


RULES_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "rules"
    / "tpme_investment_rules.json"
)


class TpmePrimeCalculationError(ValueError):
    """Erreur de validation du calcul des primes TPME."""


def load_tpme_rules() -> dict[str, Any]:
    if not RULES_PATH.exists():
        raise FileNotFoundError(
            f"Configuration réglementaire TPME introuvable : {RULES_PATH}"
        )

    with RULES_PATH.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_tpme_investment_bonus(
    *,
    total_investment_mad: Decimal | int | float | str,
    primable_investment_mad: Decimal | int | float | str,
    stable_jobs: int,
    equity_financing_mad: Decimal | int | float | str,
    company_age_years: Decimal | int | float | str,
    annual_turnover_mad: Decimal | int | float | str | None = None,
    owned_over_25_by_large_company: bool = False,
    has_public_entity_shareholder: bool = False,
    activity_eligible: bool = True,
    tourism_activity: bool = False,
    priority_activity: bool = False,
    territorial_category: str | None = None,
) -> dict[str, Any]:
    """
    Calcule les primes du dispositif spécifique de soutien destiné
    aux TPME pr?vu par le décret n° 2-25-342.

    Le calcul est d?terministe.
    """

    rules = load_tpme_rules()

    total_investment = Decimal(str(total_investment_mad))
    primable_investment = Decimal(str(primable_investment_mad))
    equity_financing = Decimal(str(equity_financing_mad))
    company_age = Decimal(str(company_age_years))

    turnover = (
        Decimal(str(annual_turnover_mad))
        if annual_turnover_mad is not None
        else None
    )

    if total_investment <= 0:
        raise TpmePrimeCalculationError(
            "Le montant total d'investissement doit être positif."
        )

    if primable_investment <= 0:
        raise TpmePrimeCalculationError(
            "Le montant d'investissement primable doit être positif."
        )

    if primable_investment > total_investment:
        raise TpmePrimeCalculationError(
            "Le montant primable ne peut pas dépasser "
            "le montant total d'investissement."
        )

    if stable_jobs < 0:
        raise TpmePrimeCalculationError(
            "Le nombre d'emplois stables ne peut pas être négatif."
        )

    if equity_financing < 0:
        raise TpmePrimeCalculationError(
            "Le montant des fonds propres ne peut pas être négatif."
        )

    if equity_financing > total_investment:
        raise TpmePrimeCalculationError(
            "Les fonds propres ne peuvent pas dépasser "
            "le montant total d'investissement."
        )

    if company_age < 0:
        raise TpmePrimeCalculationError(
            "L'âge de l'entreprise ne peut pas être négatif."
        )

    if turnover is not None and turnover < 0:
        raise TpmePrimeCalculationError(
            "Le chiffre d'affaires ne peut pas être négatif."
        )

    if territorial_category is not None:
        territorial_category = territorial_category.strip().upper()

        if territorial_category not in {"A", "B"}:
            raise TpmePrimeCalculationError(
                "La catégorie territoriale doit être A, B ou non renseignée."
            )

    tpme_rules = rules["definition_tpme"]
    eligibility_rules = rules["eligibilite_projet"]

    new_company = (
        company_age
        < Decimal(
            str(
                tpme_rules[
                    "nouvelle_entreprise_age_max_exclusif_ans"
                ]
            )
        )
    )

    turnover_eligible = False

    if new_company:
        turnover_eligible = True
    elif turnover is not None:
        turnover_eligible = (
            turnover
            >= Decimal(
                str(
                    tpme_rules[
                        "chiffre_affaires_min_mad"
                    ]
                )
            )
            and turnover
            < Decimal(
                str(
                    tpme_rules[
                        "chiffre_affaires_max_exclusif_mad"
                    ]
                )
            )
        )

    ownership_eligible = not owned_over_25_by_large_company
    public_shareholder_eligible = not has_public_entity_shareholder

    investment_amount_eligible = (
        total_investment
        >= Decimal(
            str(
                eligibility_rules[
                    "investissement_min_mad"
                ]
            )
        )
        and total_investment
        < Decimal(
            str(
                eligibility_rules[
                    "investissement_max_exclusif_mad"
                ]
            )
        )
    )

    investment_in_millions = (
        total_investment / Decimal("1000000")
    )

    employment_ratio = (
        Decimal(stable_jobs) / investment_in_millions
        if investment_in_millions > 0
        else Decimal("0")
    )

    required_employment_ratio = Decimal(
        str(
            eligibility_rules[
                "ratio_emplois_min_tourisme"
                if tourism_activity
                else "ratio_emplois_min_general"
            ]
        )
    )

    employment_ratio_eligible = (
        employment_ratio >= required_employment_ratio
    )

    equity_ratio = (
        equity_financing / total_investment
        if total_investment > 0
        else Decimal("0")
    )

    required_equity_ratio = Decimal(
        str(eligibility_rules["fonds_propres_min"])
    )

    equity_eligible = equity_ratio >= required_equity_ratio

    eligibility_details = {
        "tpme_definition": (
            turnover_eligible
            and ownership_eligible
            and public_shareholder_eligible
        ),
        "turnover_or_new_company": turnover_eligible,
        "ownership_structure": ownership_eligible,
        "no_public_entity_shareholder": public_shareholder_eligible,
        "investment_amount": investment_amount_eligible,
        "employment_ratio": employment_ratio_eligible,
        "equity_financing": equity_eligible,
        "eligible_activity": activity_eligible,
    }

    eligible = all(eligibility_details.values())

    base_result = {
        "eligible": eligible,
        "eligibility_details": eligibility_details,
        "total_investment_mad": float(
            money(total_investment)
        ),
        "primable_investment_mad": float(
            money(primable_investment)
        ),
        "stable_jobs": stable_jobs,
        "employment_ratio": float(
            employment_ratio.quantize(
                Decimal("0.0001"),
                rounding=ROUND_HALF_UP,
            )
        ),
        "required_employment_ratio": float(
            required_employment_ratio
        ),
        "equity_financing_mad": float(
            money(equity_financing)
        ),
        "equity_ratio": float(
            equity_ratio.quantize(
                Decimal("0.0001"),
                rounding=ROUND_HALF_UP,
            )
        ),
        "new_company": new_company,
        "territorial_category": territorial_category,
        "legal_references": rules["references_juridiques"],
    }

    if not eligible:
        failed_conditions = [
            key
            for key, value in eligibility_details.items()
            if not value
        ]

        return {
            **base_result,
            "reason": (
                "Le projet ne satisfait pas toutes les conditions "
                "d'?ligibilit? du dispositif TPME."
            ),
            "failed_conditions": failed_conditions,
            "raw_rate": 0.0,
            "raw_rate_percent": 0.0,
            "total_rate": 0.0,
            "total_rate_percent": 0.0,
            "total_bonus_mad": 0.0,
            "details": [],
            "warnings": [],
        }

    details: list[dict[str, Any]] = []
    warnings: list[str] = []
    raw_rate = Decimal("0")

    employment_rate = Decimal("0")

    if employment_ratio > Decimal("10"):
        employment_rate = Decimal("0.10")
    elif employment_ratio > Decimal("5"):
        employment_rate = Decimal("0.07")
    elif employment_ratio >= Decimal("2"):
        employment_rate = Decimal("0.05")

    if employment_rate > 0:
        raw_rate += employment_rate

        details.append(
            {
                "code": "prime_emplois_stables",
                "label": "Prime ? la création d'emplois stables",
                "rate": float(employment_rate),
                "rate_percent": float(
                    employment_rate * 100
                ),
                "calculated_ratio": float(
                    employment_ratio.quantize(
                        Decimal("0.0001"),
                        rounding=ROUND_HALF_UP,
                    )
                ),
            }
        )

    if territorial_category:
        territorial_rate = Decimal(
            str(
                rules["prime_territoriale"][
                    f"categorie_{territorial_category}"
                ]
            )
        )

        raw_rate += territorial_rate

        details.append(
            {
                "code": "prime_territoriale",
                "label": (
                    "Prime territoriale - "
                    f"catégorie {territorial_category}"
                ),
                "category": territorial_category,
                "rate": float(territorial_rate),
                "rate_percent": float(
                    territorial_rate * 100
                ),
            }
        )
    else:
        warnings.append(
            "La catégorie territoriale n'est pas renseignée : "
            "aucune prime territoriale n'a été ajout?e."
        )

    if priority_activity:
        priority_rate = Decimal(
            str(
                rules[
                    "prime_activite_prioritaire"
                ]["taux"]
            )
        )

        raw_rate += priority_rate

        details.append(
            {
                "code": "prime_activite_prioritaire",
                "label": "Prime liée aux activités prioritaires",
                "rate": float(priority_rate),
                "rate_percent": float(
                    priority_rate * 100
                ),
            }
        )

    maximum_rate = Decimal(
        str(
            rules["plafonds"]["taux_global_max"]
        )
    )

    applied_rate = min(raw_rate, maximum_rate)

    if raw_rate > maximum_rate:
        warnings.append(
            "Le cumul th?orique dépasse 30 %. "
            "Le plafond réglementaire de 30 % a été appliqué."
        )

    total_bonus = money(
        primable_investment * applied_rate
    )

    return {
        **base_result,
        "failed_conditions": [],
        "raw_rate": float(raw_rate),
        "raw_rate_percent": float(raw_rate * 100),
        "total_rate": float(applied_rate),
        "total_rate_percent": float(
            applied_rate * 100
        ),
        "total_bonus_mad": float(total_bonus),
        "details": details,
        "warnings": warnings,
        "reason": None,
    }
