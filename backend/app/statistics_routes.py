from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import get_database_session
from app.models import RegionalInvestmentStatistic


router = APIRouter(
    prefix="/public/statistics",
    tags=["Public statistics"],
)


PROVINCES = (
    "Guelmim",
    "Tan-Tan",
    "Sidi Ifni",
    "Assa-Zag",
)


class ProvinceStatistic(BaseModel):
    province: str
    dossiers: int
    projects: int
    investment_amount_mad: float
    jobs: int
    investment_share_percent: float


class RegionalStatisticsResponse(BaseModel):
    has_data: bool
    year: int | None
    dossiers: int
    projects: int
    investment_amount_mad: float
    jobs: int
    provinces: list[ProvinceStatistic]


@router.get(
    "",
    response_model=RegionalStatisticsResponse,
)
def regional_statistics(
    year: int | None = Query(
        default=None,
        ge=2000,
        le=2100,
    ),
    database_session: Session = Depends(
        get_database_session
    ),
) -> RegionalStatisticsResponse:

    query = select(
        RegionalInvestmentStatistic
    )

    # Si une année est explicitement demandée,
    # retourner uniquement cette année.
    # Sinon : cumuler toutes les années disponibles.
    if year is not None:
        query = query.where(
            RegionalInvestmentStatistic.year == year
        )

    rows = list(
        database_session.scalars(
            query
        ).all()
    )

    if not rows:
        return RegionalStatisticsResponse(
            has_data=False,
            year=year,
            dossiers=0,
            projects=0,
            investment_amount_mad=0.0,
            jobs=0,
            provinces=[
                ProvinceStatistic(
                    province=province,
                    dossiers=0,
                    projects=0,
                    investment_amount_mad=0.0,
                    jobs=0,
                    investment_share_percent=0.0,
                )
                for province in PROVINCES
            ],
        )

    total_dossiers = sum(
        row.dossiers_count
        for row in rows
    )

    total_projects = sum(
        row.projects_count
        for row in rows
    )

    total_jobs = sum(
        row.jobs_count
        for row in rows
    )

    total_investment = sum(
        (
            row.investment_amount_mad
            or Decimal("0")
            for row in rows
        ),
        Decimal("0"),
    )

    province_results: list[ProvinceStatistic] = []

    for province in PROVINCES:

        province_rows = [
            row
            for row in rows
            if row.province == province
        ]

        dossiers = sum(
            row.dossiers_count
            for row in province_rows
        )

        projects = sum(
            row.projects_count
            for row in province_rows
        )

        jobs = sum(
            row.jobs_count
            for row in province_rows
        )

        amount = sum(
            (
                row.investment_amount_mad
                or Decimal("0")
                for row in province_rows
            ),
            Decimal("0"),
        )

        if total_investment > 0:
            share = round(
                float(
                    amount
                    / total_investment
                    * Decimal("100")
                ),
                2,
            )
        else:
            share = 0.0

        province_results.append(
            ProvinceStatistic(
                province=province,
                dossiers=dossiers,
                projects=projects,
                investment_amount_mad=float(amount),
                jobs=jobs,
                investment_share_percent=share,
            )
        )

    return RegionalStatisticsResponse(
        has_data=True,

        # None signifie : données cumulées toutes années.
        # Une valeur signifie : filtre sur cette année précise.
        year=year,

        dossiers=total_dossiers,
        projects=total_projects,
        investment_amount_mad=float(
            total_investment
        ),
        jobs=total_jobs,
        provinces=province_results,
    )

class TerritorialIndicator(BaseModel):
    code: str
    label: str
    value: float
    unit: str
    reference_year: int
    source_name: str
    source_url: str | None = None


class TerritorialStatisticsResponse(BaseModel):
    has_data: bool
    indicators: list[TerritorialIndicator]


@router.get(
    "/territorial",
    response_model=TerritorialStatisticsResponse,
)
def territorial_statistics(
    database_session: Session = Depends(
        get_database_session
    ),
) -> TerritorialStatisticsResponse:

    rows = database_session.execute(
        text(
            """
            SELECT DISTINCT ON (code)
                code,
                label,
                value,
                unit,
                reference_year,
                source_name,
                source_url
            FROM regional_key_indicators
            ORDER BY
                code,
                reference_year DESC,
                updated_at DESC
            """
        )
    ).mappings().all()

    indicators = [
        TerritorialIndicator(
            code=row["code"],
            label=row["label"],
            value=float(row["value"]),
            unit=row["unit"],
            reference_year=row["reference_year"],
            source_name=row["source_name"],
            source_url=row["source_url"],
        )
        for row in rows
    ]

    return TerritorialStatisticsResponse(
        has_data=bool(indicators),
        indicators=indicators,
    )