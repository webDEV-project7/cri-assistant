from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.prime_routes import router


app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_tpme_route_calculates_bonus():
    response = client.post(
        "/primes/tpme",
        json={
            "total_investment_mad": 10000000,
            "primable_investment_mad": 8000000,
            "stable_jobs": 30,
            "equity_financing_mad": 2000000,
            "company_age_years": 2,
            "activity_eligible": True,
            "tourism_activity": False,
            "priority_activity": True,
            "territorial_category": "B",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["eligible"] is True
    assert data["employment_ratio"] == 3.0
    assert data["total_rate_percent"] == 30.0
    assert data["total_bonus_mad"] == 2400000.0


def test_tpme_route_rejects_invalid_category():
    response = client.post(
        "/primes/tpme",
        json={
            "total_investment_mad": 10000000,
            "primable_investment_mad": 8000000,
            "stable_jobs": 30,
            "equity_financing_mad": 2000000,
            "company_age_years": 2,
            "activity_eligible": True,
            "territorial_category": "C",
        },
    )

    assert response.status_code == 422


def test_tpme_route_rejects_50_million_project():
    response = client.post(
        "/primes/tpme",
        json={
            "total_investment_mad": 50000000,
            "primable_investment_mad": 40000000,
            "stable_jobs": 100,
            "equity_financing_mad": 5000000,
            "company_age_years": 1,
            "activity_eligible": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["eligible"] is False
    assert (
        data["eligibility_details"]["investment_amount"]
        is False
    )


def test_tpme_route_requires_activity_eligibility():
    response = client.post(
        "/primes/tpme",
        json={
            "total_investment_mad": 10_000_000,
            "primable_investment_mad": 8_000_000,
            "stable_jobs": 30,
            "equity_financing_mad": 2_000_000,
            "company_age_years": 2,
            "priority_activity": True,
            "territorial_category": "B",
        },
    )

    assert response.status_code == 422


def test_tpme_catalog_returns_regulatory_hierarchy():
    response = client.get("/primes/tpme/catalog")

    assert response.status_code == 200

    data = response.json()

    assert data["region"] == "Guelmim-Oued Noun"
    assert len(data["provinces"]) == 4
    assert len(data["sectors"]) == 14

    branch_count = sum(
        len(sector["branches"])
        for sector in data["sectors"]
    )
    assert branch_count == 54

    guelmim = next(
        province
        for province in data["provinces"]
        if province["name"] == "Guelmim"
    )
    assert guelmim["territorial_category"] == "B"

    for sector in data["sectors"]:
        assert "name" in sector
        assert "tourism_activity" in sector
        assert isinstance(sector["branches"], list)

        for branch in sector["branches"]:
            assert "name" in branch
            assert isinstance(branch["priority_activities"], list)


def test_tpme_simulation_route_calculates_primable_automatically():
    response = client.post(
        "/primes/tpme/simulate",
        json={
            "total_investment_mad": 10_000_000,
            "stable_jobs": 30,
            "equity_financing_mad": 2_000_000,
            "company_age_years": 2,
            "vehicles_mad": 1_000_000,
            "activity_eligible": True,
            "priority_activity": True,
            "territorial_category": "B",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["eligible"] is True
    assert data["primable_investment_mad"] == 9_000_000.0
    assert data["total_rate_percent"] == 30.0
    assert data["total_bonus_mad"] == 2_700_000.0

    assert (
        data["primable_breakdown"]["excluded_vehicles_mad"]
        == 1_000_000.0
    )


def test_tpme_simulation_route_does_not_require_primable_input():
    response = client.post(
        "/primes/tpme/simulate",
        json={
            "total_investment_mad": 10_000_000,
            "stable_jobs": 30,
            "equity_financing_mad": 2_000_000,
            "company_age_years": 2,
            "activity_eligible": True,
            "territorial_category": "B",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["primable_investment_mad"] == 10_000_000.0


def test_tpme_simulation_route_rejects_invalid_expense_breakdown():
    response = client.post(
        "/primes/tpme/simulate",
        json={
            "total_investment_mad": 10_000_000,
            "stable_jobs": 30,
            "equity_financing_mad": 2_000_000,
            "company_age_years": 2,
            "studies_trademarks_processes_mad": 4_000_000,
            "private_land_mad": 4_000_000,
            "vehicles_mad": 3_000_000,
            "activity_eligible": True,
            "territorial_category": "B",
        },
    )

    assert response.status_code == 422
