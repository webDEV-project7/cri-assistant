from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


STUDIES_RATE_CAP = Decimal("0.05")
STUDIES_AMOUNT_CAP_MAD = Decimal("500000")

PRIVATE_LAND_RATE_CAP = Decimal("0.20")
PRIVATE_LAND_AMOUNT_CAP_MAD = Decimal("5000000")


class TpmePrimableCalculationError(ValueError):
    """Erreur de validation du calcul du montant primable TPME."""


def _decimal(value: Decimal | int | float | str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise TpmePrimableCalculationError(
            "Montant numérique invalide."
        ) from exc


def _money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_tpme_primable_investment(
    *,
    total_investment_mad: Decimal | int | float | str,
    studies_trademarks_processes_mad: Decimal | int | float | str = 0,
    private_land_mad: Decimal | int | float | str = 0,
    vehicles_mad: Decimal | int | float | str = 0,
    related_party_investment_mad: Decimal | int | float | str = 0,
    private_land_eligible: bool = False,
) -> dict[str, Any]:
    """
    Calcule automatiquement le montant d'investissement primable TPME.

    Règles appliquées conformément à l'article 2 du décret n° 2-25-342 :
    - études, enregistrement de marques et mise au point des procédés :
      maximum 5 % du montant primable et maximum 500 000 MAD ;
    - foncier privé, lorsqu'il est éligible :
      maximum 20 % du montant primable et maximum 5 000 000 MAD ;
    - véhicules : exclus ;
    - investissements réalisés entre entreprises liées par un même
      investisseur : exclus.

    Les plafonds proportionnels étant définis par rapport au montant
    primable lui-même, le montant est déterminé par convergence
    d'un point fixe.
    """

    total = _decimal(total_investment_mad)
    studies = _decimal(studies_trademarks_processes_mad)
    private_land = _decimal(private_land_mad)
    vehicles = _decimal(vehicles_mad)
    related_party = _decimal(related_party_investment_mad)

    amounts = {
        "total_investment_mad": total,
        "studies_trademarks_processes_mad": studies,
        "private_land_mad": private_land,
        "vehicles_mad": vehicles,
        "related_party_investment_mad": related_party,
    }

    if total <= 0:
        raise TpmePrimableCalculationError(
            "Le montant total d'investissement doit être positif."
        )

    for name, amount in amounts.items():
        if name != "total_investment_mad" and amount < 0:
            raise TpmePrimableCalculationError(
                "Les composantes de l'investissement "
                "ne peuvent pas être négatives."
            )

    special_total = (
        studies
        + private_land
        + vehicles
        + related_party
    )

    if special_total > total:
        raise TpmePrimableCalculationError(
            "La somme des composantes détaillées ne peut pas "
            "dépasser le montant total d'investissement."
        )

    other_investment = total - special_total

    primable = total

    for _ in range(200):
        eligible_studies = min(
            studies,
            STUDIES_AMOUNT_CAP_MAD,
            primable * STUDIES_RATE_CAP,
        )

        if private_land_eligible:
            eligible_private_land = min(
                private_land,
                PRIVATE_LAND_AMOUNT_CAP_MAD,
                primable * PRIVATE_LAND_RATE_CAP,
            )
        else:
            eligible_private_land = Decimal("0")

        new_primable = (
            other_investment
            + eligible_studies
            + eligible_private_land
        )

        if abs(new_primable - primable) < Decimal("0.0001"):
            primable = new_primable
            break

        primable = new_primable
    else:
        raise TpmePrimableCalculationError(
            "Le calcul du montant primable n'a pas convergé."
        )

    primable = _money(primable)

    eligible_studies = _money(
        min(
            studies,
            STUDIES_AMOUNT_CAP_MAD,
            primable * STUDIES_RATE_CAP,
        )
    )

    eligible_private_land = Decimal("0.00")

    if private_land_eligible:
        eligible_private_land = _money(
            min(
                private_land,
                PRIVATE_LAND_AMOUNT_CAP_MAD,
                primable * PRIVATE_LAND_RATE_CAP,
            )
        )

    primable = _money(
        other_investment
        + eligible_studies
        + eligible_private_land
    )

    excluded_studies = _money(
        studies - eligible_studies
    )

    excluded_private_land = _money(
        private_land - eligible_private_land
    )

    return {
        "total_investment_mad": float(_money(total)),
        "primable_investment_mad": float(primable),

        "other_investment_mad": float(
            _money(other_investment)
        ),

        "studies_trademarks_processes_mad": float(
            _money(studies)
        ),
        "eligible_studies_mad": float(
            eligible_studies
        ),
        "excluded_studies_mad": float(
            excluded_studies
        ),

        "private_land_mad": float(
            _money(private_land)
        ),
        "private_land_eligible": private_land_eligible,
        "eligible_private_land_mad": float(
            eligible_private_land
        ),
        "excluded_private_land_mad": float(
            excluded_private_land
        ),

        "excluded_vehicles_mad": float(
            _money(vehicles)
        ),
        "excluded_related_party_investment_mad": float(
            _money(related_party)
        ),
    }