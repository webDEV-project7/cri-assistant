from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


RULES_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "rules"
    / "investment_rules.json"
)


class PrimeCalculationError(ValueError):
    """Erreur de validation du calcul des primes."""


def load_rules() -> dict[str, Any]:
    if not RULES_PATH.exists():
        raise FileNotFoundError(
            f"Configuration réglementaire introuvable : {RULES_PATH}"
        )

    with RULES_PATH.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_investment_bonus(
    *,
    total_investment_mad: Decimal | int | float | str,
    primable_investment_mad: Decimal | int | float | str,
    stable_jobs: int,
    female_payroll_mad: Decimal | int | float | str = 0,
    total_payroll_mad: Decimal | int | float | str = 0,
    future_business: bool = False,
    sustainable_project: bool = False,
    local_integration: bool = False,
    province: str | None = None,
    sector: str | None = None,
    renewable_energy_production: bool = False,
) -> dict[str, Any]:
    """
    Calcule les primes du dispositif principal de soutien à l'investissement.

    Le calcul est déterministe. Aucun modèle d'intelligence artificielle
    n'intervient dans la détermination de l'éligibilité ou des taux.
    """

    rules = load_rules()

    total_investment = Decimal(str(total_investment_mad))
    primable_investment = Decimal(str(primable_investment_mad))
    female_payroll = Decimal(str(female_payroll_mad))
    total_payroll = Decimal(str(total_payroll_mad))

    if total_investment <= 0:
        raise PrimeCalculationError(
            "Le montant total d'investissement doit être positif."
        )

    if primable_investment <= 0:
        raise PrimeCalculationError(
            "Le montant d'investissement primable doit être positif."
        )

    if primable_investment > total_investment:
        raise PrimeCalculationError(
            "Le montant primable ne peut pas dépasser "
            "le montant total d'investissement."
        )

    if stable_jobs < 0:
        raise PrimeCalculationError(
            "Le nombre d'emplois stables ne peut pas être négatif."
        )

    if female_payroll < 0 or total_payroll < 0:
        raise PrimeCalculationError(
            "Les masses salariales ne peuvent pas être négatives."
        )

    if female_payroll > total_payroll:
        raise PrimeCalculationError(
            "La masse salariale féminine ne peut pas dépasser "
            "la masse salariale totale."
        )

    # Décret 2-23-1 :
    # investissement strictement supérieur à 50 MDH et au moins 50 emplois,
    # OU création d'au moins 150 emplois stables.
    eligible_by_investment_and_jobs = (
        total_investment > Decimal("50000000")
        and stable_jobs >= 50
    )
    eligible_by_jobs = stable_jobs >= 150

    eligible = (
        eligible_by_investment_and_jobs
        or eligible_by_jobs
    )

    eligibility_details = {
        "investment_over_50_million_and_50_jobs": (
            eligible_by_investment_and_jobs
        ),
        "at_least_150_jobs": eligible_by_jobs,
    }

    if not eligible:
        investment_in_millions = (
            total_investment / Decimal("1000000")
            if total_investment > 0
            else Decimal("0")
        )

        employment_ratio = (
            Decimal(stable_jobs) / investment_in_millions
            if investment_in_millions > 0
            else Decimal("0")
        )

        gender_ratio = (
            female_payroll / total_payroll
            if total_payroll > 0
            else Decimal("0")
        )

        return {
            "eligible": False,
            "eligibility_details": eligibility_details,
            "reason": (
                "Le projet doit prévoir un investissement strictement "
                "supérieur à 50 000 000 MAD et au moins 50 emplois stables, "
                "ou créer au moins 150 emplois stables."
            ),
            "total_rate": 0.0,
            "total_rate_percent": 0.0,
            "total_bonus_mad": 0.0,
            "details": [],
            "warnings": [],
            "legal_references": rules["references_juridiques"],
            "total_investment_mad": float(total_investment),
            "primable_investment_mad": float(primable_investment),
            "stable_jobs": stable_jobs,
            "employment_ratio": float(employment_ratio),
            "gender_ratio": float(gender_ratio),
            "raw_rate": 0.0,
            "raw_rate_percent": 0.0,
        }

    details: list[dict[str, Any]] = []
    warnings: list[str] = []
    raw_rate = Decimal("0")

    # Ratio d'emplois :
    # nombre d'emplois / montant total exprimé en millions de MAD.
    investment_in_millions = total_investment / Decimal("1000000")
    employment_ratio = (
        Decimal(stable_jobs) / investment_in_millions
    )

    employment_rate = Decimal("0")

    if employment_ratio > Decimal("3"):
        employment_rate = Decimal("0.10")
    elif employment_ratio > Decimal("1.5"):
        employment_rate = Decimal("0.07")
    elif employment_ratio > Decimal("1"):
        employment_rate = Decimal("0.05")

    if employment_rate > 0:
        raw_rate += employment_rate
        details.append(
            {
                "code": "ratio_emplois",
                "label": "Prime liée au ratio d'emplois stables",
                "rate": float(employment_rate),
                "rate_percent": float(employment_rate * 100),
                "calculated_ratio": float(
                    employment_ratio.quantize(
                        Decimal("0.0001"),
                        rounding=ROUND_HALF_UP,
                    )
                ),
            }
        )

    # Ratio genre :
    # masse salariale féminine / masse salariale totale.
    gender_ratio: Decimal | None = None

    if total_payroll > 0:
        gender_ratio = female_payroll / total_payroll

        if gender_ratio >= Decimal("0.30"):
            gender_rate = Decimal("0.03")
            raw_rate += gender_rate
            details.append(
                {
                    "code": "ratio_genre",
                    "label": "Prime liée au ratio genre",
                    "rate": float(gender_rate),
                    "rate_percent": 3.0,
                    "calculated_ratio": float(
                        gender_ratio.quantize(
                            Decimal("0.0001"),
                            rounding=ROUND_HALF_UP,
                        )
                    ),
                }
            )
    elif female_payroll > 0:
        raise PrimeCalculationError(
            "La masse salariale totale doit être renseignée "
            "pour calculer le ratio genre."
        )

    common_boolean_bonuses = (
        (
            future_business,
            "metier_avenir",
            "Métier d'avenir ou montée en gamme",
        ),
        (
            sustainable_project,
            "investissement_durable",
            "Projet d'investissement durable",
        ),
        (
            local_integration,
            "integration_locale",
            "Projet d'intégration locale",
        ),
    )

    for active, code, label in common_boolean_bonuses:
        if active:
            rate = Decimal("0.03")
            raw_rate += rate
            details.append(
                {
                    "code": code,
                    "label": label,
                    "rate": float(rate),
                    "rate_percent": 3.0,
                }
            )

    # Prime territoriale Guelmim-Oued Noun.
    allowed_provinces = {
        "Guelmim",
        "Tan-Tan",
        "Sidi Ifni",
        "Assa-Zag",
    }

    normalized_province = province.strip() if province else ""

    if normalized_province not in allowed_provinces:
        raise PrimeCalculationError(
            "Province invalide. Choix autorises : "
            "Guelmim, Tan-Tan, Sidi Ifni ou Assa-Zag."
        )

    territorial_rate = Decimal("0.15")
    raw_rate += territorial_rate

    details.append(
        {
            "code": "prime_territoriale_B",
            "label": (
                "Prime territoriale - "
                f"{normalized_province} (categorie B)"
            ),
            "rate": float(territorial_rate),
            "rate_percent": 15.0,
            "province": normalized_province,
            "territorial_category": "B",
        }
    )
    # Prime sectorielle.
    normalized_sector = (
        sector.strip().lower()
        .replace(" ", "_")
        .replace("-", "_")
        if sector
        else None
    )

    sector_aliases = {
        "technologies_de_l'information": "numerique",
        "technologies_de_l’information": "numerique",
        "technologies_de_linformation": "numerique",
        "technologie_de_l'information": "numerique",
        "technologie_de_l’information": "numerique",
        "informatique": "numerique",
        "digital": "numerique",
        "it": "numerique",
    }

    if normalized_sector:
        normalized_sector = sector_aliases.get(
            normalized_sector,
            normalized_sector,
        )

    official_sectors = set(
        rules["prime_sectorielle"]["secteurs"]
    )

    if normalized_sector:
        if normalized_sector in official_sectors:
            sector_rate = Decimal(
                str(rules["prime_sectorielle"]["taux"])
            )
            raw_rate += sector_rate
            details.append(
                {
                    "code": "prime_sectorielle",
                    "label": "Prime sectorielle",
                    "sector": normalized_sector,
                    "rate": float(sector_rate),
                    "rate_percent": float(sector_rate * 100),
                }
            )
        else:
            warnings.append(
                "Le secteur renseigné ne correspond pas exactement "
                "à un secteur prioritaire enregistré."
            )

    maximum_rate = Decimal(
        str(rules["plafonds"]["taux_global_max"])
    )
    applied_rate = min(raw_rate, maximum_rate)

    if raw_rate > maximum_rate:
        warnings.append(
            "Le cumul théorique des primes dépasse 30 %. "
            "Le plafond réglementaire de 30 % a été appliqué."
        )

    theoretical_bonus = money(
        primable_investment * applied_rate
    )
    applied_bonus = theoretical_bonus

    if renewable_energy_production:
        energy_cap = Decimal(
            str(
                rules["plafonds"][
                    "energies_eolienne_solaire_hydraulique_montant_max_mad"
                ]
            )
        )

        if applied_bonus > energy_cap:
            applied_bonus = money(energy_cap)
            warnings.append(
                "Le plafond de 30 000 000 MAD applicable à la production "
                "d'énergie éolienne, solaire ou hydraulique a été appliqué."
            )

    return {
        "eligible": True,
        "eligibility_details": eligibility_details,
        "total_investment_mad": float(money(total_investment)),
        "primable_investment_mad": float(money(primable_investment)),
        "stable_jobs": stable_jobs,
        "employment_ratio": float(
            employment_ratio.quantize(
                Decimal("0.0001"),
                rounding=ROUND_HALF_UP,
            )
        ),
        "gender_ratio": (
            float(
                gender_ratio.quantize(
                    Decimal("0.0001"),
                    rounding=ROUND_HALF_UP,
                )
            )
            if gender_ratio is not None
            else None
        ),
        "raw_rate": float(raw_rate),
        "raw_rate_percent": float(raw_rate * 100),
        "total_rate": float(applied_rate),
        "total_rate_percent": float(applied_rate * 100),
        "total_bonus_mad": float(applied_bonus),
        "details": details,
        "warnings": warnings,
        "legal_references": rules["references_juridiques"],
    }

