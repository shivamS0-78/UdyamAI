"""Tests for the new data query routes: agriculture, economic, infrastructure, livestock, population, weather."""

from datetime import date, datetime
from unittest.mock import patch
from uuid import uuid4

# ---------------------------------------------------------------------------
# Agriculture routes
# ---------------------------------------------------------------------------


def test_list_crop_names(client):
    with patch(
        "app.api.routes.agriculture.AgricultureService.get_crop_names",
        return_value=["Rice", "Wheat"],
    ):
        resp = client.get("/agriculture/crops")
        assert resp.status_code == 200
        assert resp.json() == ["Rice", "Wheat"]


def test_list_crop_names_filter(client):
    location = uuid4()
    with patch(
        "app.api.routes.agriculture.AgricultureService.get_crop_names",
        return_value=["Rice"],
    ) as mock_svc:
        resp = client.get(f"/agriculture/crops?location_id={location}")
        assert resp.status_code == 200
        mock_svc.assert_called_once()


def test_list_seasons(client):
    with patch(
        "app.api.routes.agriculture.AgricultureService.get_seasons",
        return_value=["kharif", "rabi"],
    ):
        resp = client.get("/agriculture/seasons")
        assert resp.status_code == 200
        assert resp.json() == ["kharif", "rabi"]


def test_list_agriculture(client):
    loc = uuid4()
    dummy = {
        "id": str(uuid4()),
        "location_id": str(loc),
        "crop_name": "Rice",
        "crop_category": "cereals",
        "cultivated_area": 10.5,
        "production": 25.0,
        "production_unit": "tonnes",
        "irrigated_area": 5.0,
        "year": 2023,
        "season": "kharif",
        "source": "gov",
        "source_url": None,
        "data_year": 2023,
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.agriculture.AgricultureService.get_agriculture_records",
        return_value=[dummy],
    ):
        resp = client.get(f"/agriculture?location_id={loc}&crop_name=Rice&year=2023")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["crop_name"] == "Rice"


def test_get_agriculture_found(client):
    ag_id = uuid4()
    dummy = {
        "id": str(ag_id),
        "location_id": str(uuid4()),
        "crop_name": "Wheat",
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.agriculture.AgricultureService.get_agriculture_by_id",
        return_value=dummy,
    ):
        resp = client.get(f"/agriculture/{ag_id}")
        assert resp.status_code == 200
        assert resp.json()["crop_name"] == "Wheat"


def test_get_agriculture_not_found(client):
    ag_id = uuid4()
    with patch(
        "app.api.routes.agriculture.AgricultureService.get_agriculture_by_id",
        return_value=None,
    ):
        resp = client.get(f"/agriculture/{ag_id}")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Economic routes
# ---------------------------------------------------------------------------


def test_list_indicator_names(client):
    with patch(
        "app.api.routes.economic.EconomicService.get_indicator_names",
        return_value=["GDP_per_capita", "literacy_rate"],
    ):
        resp = client.get("/economic/indicators")
        assert resp.status_code == 200
        assert resp.json() == ["GDP_per_capita", "literacy_rate"]


def test_list_economic_indicators(client):
    dummy = {
        "id": str(uuid4()),
        "location_id": str(uuid4()),
        "indicator_name": "GDP_per_capita",
        "indicator_value": 50000.0,
        "unit": "INR",
        "year": 2023,
        "source": "gov",
        "source_url": None,
        "data_year": 2023,
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.economic.EconomicService.get_economic_indicators",
        return_value=[dummy],
    ):
        resp = client.get("/economic?indicator_name=GDP_per_capita&year=2023")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


def test_get_economic_indicator_found(client):
    ind_id = uuid4()
    dummy = {
        "id": str(ind_id),
        "indicator_name": "GDP_per_capita",
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.economic.EconomicService.get_economic_indicator_by_id",
        return_value=dummy,
    ):
        resp = client.get(f"/economic/{ind_id}")
        assert resp.status_code == 200
        assert resp.json()["indicator_name"] == "GDP_per_capita"


def test_get_economic_indicator_not_found(client):
    ind_id = uuid4()
    with patch(
        "app.api.routes.economic.EconomicService.get_economic_indicator_by_id",
        return_value=None,
    ):
        resp = client.get(f"/economic/{ind_id}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Infrastructure routes
# ---------------------------------------------------------------------------


def test_list_facility_types(client):
    with patch(
        "app.api.routes.infrastructure.InfrastructureService.get_facility_types",
        return_value=["hospital", "school"],
    ):
        resp = client.get("/infrastructure/types")
        assert resp.status_code == 200
        assert resp.json() == ["hospital", "school"]


def test_list_infrastructure(client):
    dummy = {
        "id": str(uuid4()),
        "location_id": str(uuid4()),
        "facility_type": "hospital",
        "name": "PHC",
        "latitude": 20.0,
        "longitude": 75.0,
        "distance_from_village": 2.5,
        "capacity": 50.0,
        "source": "gov",
        "source_url": None,
        "data_year": 2023,
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.infrastructure.InfrastructureService.get_infrastructure",
        return_value=[dummy],
    ):
        resp = client.get("/infrastructure?facility_type=hospital")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["facility_type"] == "hospital"


def test_get_infrastructure_found(client):
    infra_id = uuid4()
    dummy = {
        "id": str(infra_id),
        "name": "PHC",
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.infrastructure.InfrastructureService.get_infrastructure_by_id",
        return_value=dummy,
    ):
        resp = client.get(f"/infrastructure/{infra_id}")
        assert resp.status_code == 200


def test_get_infrastructure_not_found(client):
    infra_id = uuid4()
    with patch(
        "app.api.routes.infrastructure.InfrastructureService.get_infrastructure_by_id",
        return_value=None,
    ):
        resp = client.get(f"/infrastructure/{infra_id}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Livestock routes
# ---------------------------------------------------------------------------


def test_list_animal_types(client):
    with patch(
        "app.api.routes.livestock.LivestockService.get_animal_types",
        return_value=["cattle", "buffalo"],
    ):
        resp = client.get("/livestock/types")
        assert resp.status_code == 200
        assert resp.json() == ["cattle", "buffalo"]


def test_list_livestock(client):
    dummy = {
        "id": str(uuid4()),
        "location_id": str(uuid4()),
        "animal_type": "cattle",
        "animal_count": 120,
        "milk_production": 300.0,
        "milk_production_unit": "litres",
        "year": 2023,
        "source": "gov",
        "source_url": None,
        "data_year": 2023,
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.livestock.LivestockService.get_livestock_records",
        return_value=[dummy],
    ):
        resp = client.get("/livestock?animal_type=cattle&year=2023")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["animal_type"] == "cattle"


def test_get_livestock_found(client):
    live_id = uuid4()
    dummy = {
        "id": str(live_id),
        "location_id": str(uuid4()),
        "animal_type": "cattle",
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.livestock.LivestockService.get_livestock_by_id",
        return_value=dummy,
    ):
        resp = client.get(f"/livestock/{live_id}")
        assert resp.status_code == 200


def test_get_livestock_not_found(client):
    live_id = uuid4()
    with patch(
        "app.api.routes.livestock.LivestockService.get_livestock_by_id",
        return_value=None,
    ):
        resp = client.get(f"/livestock/{live_id}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Population routes
# ---------------------------------------------------------------------------


def test_list_available_years(client):
    with patch(
        "app.api.routes.population.PopulationService.get_available_years",
        return_value=[2021, 2011],
    ):
        resp = client.get("/population/years")
        assert resp.status_code == 200
        assert resp.json() == [2021, 2011]


def test_list_population(client):
    dummy = {
        "id": str(uuid4()),
        "location_id": str(uuid4()),
        "year": 2021,
        "population_total": 5000,
        "male_population": 2600,
        "female_population": 2400,
        "households": 1000,
        "working_population": 3000,
        "literacy_rate": 78.5,
        "source": "census",
        "source_url": None,
        "data_year": 2021,
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.population.PopulationService.get_population_records",
        return_value=[dummy],
    ):
        resp = client.get("/population?year=2021")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["year"] == 2021


def test_get_population_found(client):
    pop_id = uuid4()
    dummy = {
        "id": str(pop_id),
        "location_id": str(uuid4()),
        "year": 2021,
        "population_total": 5000,
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.population.PopulationService.get_population_by_id",
        return_value=dummy,
    ):
        resp = client.get(f"/population/{pop_id}")
        assert resp.status_code == 200


def test_get_population_not_found(client):
    pop_id = uuid4()
    with patch(
        "app.api.routes.population.PopulationService.get_population_by_id",
        return_value=None,
    ):
        resp = client.get(f"/population/{pop_id}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Weather routes
# ---------------------------------------------------------------------------


def test_list_weather(client):
    dummy = {
        "id": str(uuid4()),
        "location_id": str(uuid4()),
        "date": date(2023, 6, 15).isoformat(),
        "rainfall_mm": 12.5,
        "temperature_max_c": 35.0,
        "temperature_min_c": 22.0,
        "humidity_percent": 65.0,
        "drought_indicator": False,
        "source": "imd",
        "source_url": None,
        "data_year": 2023,
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.weather.WeatherService.get_weather_records",
        return_value=[dummy],
    ):
        resp = client.get("/weather?drought_only=false&limit=10")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


def test_get_weather_found(client):
    weather_id = uuid4()
    dummy = {
        "id": str(weather_id),
        "date": date(2023, 6, 15).isoformat(),
        "rainfall_mm": 12.5,
        "created_at": datetime.utcnow().isoformat(),
    }
    with patch(
        "app.api.routes.weather.WeatherService.get_weather_by_id",
        return_value=dummy,
    ):
        resp = client.get(f"/weather/{weather_id}")
        assert resp.status_code == 200


def test_get_weather_not_found(client):
    weather_id = uuid4()
    with patch(
        "app.api.routes.weather.WeatherService.get_weather_by_id",
        return_value=None,
    ):
        resp = client.get(f"/weather/{weather_id}")
        assert resp.status_code == 404
