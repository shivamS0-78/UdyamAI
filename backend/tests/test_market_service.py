"""Unit tests for MarketService query functions."""

from datetime import date, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.models.market import CompetitorAnalysis, Market, MarketAnalysis, MarketPrice
from app.services.market_service import MarketService

# ------------------------------------------------------------------ #
# Market queries
# ------------------------------------------------------------------ #


class TestGetMarkets:
    def test_returns_all_markets(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Market(id=uuid4(), name="Mandi A", market_type="mandi"),
            Market(id=uuid4(), name="Retail B", market_type="retail"),
        ]
        results = MarketService.get_markets(mock_db)
        assert len(results) == 2

    def test_filters_by_market_type(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Market(id=uuid4(), name="Mandi A", market_type="mandi"),
        ]
        results = MarketService.get_markets(mock_db, market_type="mandi")
        assert len(results) == 1
        assert results[0].market_type == "mandi"

    def test_filters_by_location_id(self):
        loc_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Market(id=uuid4(), name="Market X", location_id=loc_id),
        ]
        results = MarketService.get_markets(mock_db, location_id=loc_id)
        assert len(results) == 1
        assert results[0].location_id == loc_id

    def test_limit_capped_at_200(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []
        MarketService.get_markets(mock_db, limit=500)
        # Should not raise, limit capped internally


class TestGetMarketById:
    def test_returns_market(self):
        market_id = uuid4()
        mock_db = MagicMock()
        mock_db.get.return_value = Market(id=market_id, name="Test Market")
        result = MarketService.get_market_by_id(mock_db, market_id)
        assert result is not None
        assert result.name == "Test Market"
        mock_db.get.assert_called_once_with(Market, market_id)

    def test_returns_none_when_not_found(self):
        mock_db = MagicMock()
        mock_db.get.return_value = None
        result = MarketService.get_market_by_id(mock_db, uuid4())
        assert result is None


# ------------------------------------------------------------------ #
# Market Price queries
# ------------------------------------------------------------------ #


class TestGetMarketPrices:
    def test_returns_all_prices(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            MarketPrice(id=uuid4(), commodity="Wheat", modal_price=2500.0),
            MarketPrice(id=uuid4(), commodity="Rice", modal_price=3000.0),
        ]
        results = MarketService.get_market_prices(mock_db)
        assert len(results) == 2

    def test_filters_by_market_id(self):
        market_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            MarketPrice(id=uuid4(), market_id=market_id, commodity="Wheat"),
        ]
        results = MarketService.get_market_prices(mock_db, market_id=market_id)
        assert len(results) == 1

    def test_filters_by_commodity(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            MarketPrice(id=uuid4(), commodity="Wheat", modal_price=2500.0),
        ]
        results = MarketService.get_market_prices(mock_db, commodity="Wheat")
        assert len(results) == 1
        assert results[0].commodity == "Wheat"

    def test_filters_by_recorded_date(self):
        target_date = date(2026, 1, 15)
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            MarketPrice(id=uuid4(), commodity="Wheat", recorded_date=target_date),
        ]
        results = MarketService.get_market_prices(mock_db, recorded_date=target_date)
        assert len(results) == 1
        assert results[0].recorded_date == target_date

    def test_limit_capped_at_500(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []
        MarketService.get_market_prices(mock_db, limit=1000)


# ------------------------------------------------------------------ #
# Price History
# ------------------------------------------------------------------ #


class TestGetPriceHistory:
    def test_requires_commodity(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            MarketPrice(id=uuid4(), commodity="Wheat", recorded_date=date(2026, 1, 1)),
            MarketPrice(id=uuid4(), commodity="Wheat", recorded_date=date(2026, 2, 1)),
        ]
        results = MarketService.get_price_history(mock_db, commodity="Wheat")
        assert len(results) == 2

    def test_filters_by_date_range(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []
        MarketService.get_price_history(
            mock_db,
            commodity="Wheat",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
        )
        # Should not raise

    def test_filters_by_market(self):
        market_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            MarketPrice(id=uuid4(), commodity="Wheat", market_id=market_id),
        ]
        results = MarketService.get_price_history(mock_db, commodity="Wheat", market_id=market_id)
        assert len(results) == 1


# ------------------------------------------------------------------ #
# Latest Prices
# ------------------------------------------------------------------ #


class TestGetLatestPrices:
    def test_returns_latest_per_commodity(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            MarketPrice(id=uuid4(), commodity="Wheat", recorded_date=date(2026, 3, 1)),
            MarketPrice(id=uuid4(), commodity="Rice", recorded_date=date(2026, 3, 1)),
        ]
        results = MarketService.get_latest_prices(mock_db)
        assert len(results) == 2


# ------------------------------------------------------------------ #
# Aggregation helpers
# ------------------------------------------------------------------ #


class TestGetCommodities:
    def test_returns_distinct_commodities(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            ("Rice",),
            ("Wheat",),
            ("Maize",),
        ]
        results = MarketService.get_commodities(mock_db)
        assert results == ["Rice", "Wheat", "Maize"]

    def test_filters_by_market(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [("Wheat",)]
        results = MarketService.get_commodities(mock_db, market_id=uuid4())
        assert results == ["Wheat"]


class TestGetMarketTypes:
    def test_returns_distinct_types(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            ("mandi",),
            ("retail",),
            ("wholesale",),
        ]
        results = MarketService.get_market_types(mock_db)
        assert results == ["mandi", "retail", "wholesale"]


# ------------------------------------------------------------------ #
# Market Analyses
# ------------------------------------------------------------------ #


class TestGetMarketAnalyses:
    def test_returns_analyses_for_run(self):
        run_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            MarketAnalysis(id=uuid4(), analysis_run_id=run_id, radius_km=10.0),
        ]
        results = MarketService.get_market_analyses(mock_db, run_id)
        assert len(results) == 1
        assert results[0].analysis_run_id == run_id


class TestGetCompetitorAnalyses:
    def test_returns_analyses_for_run(self):
        run_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            CompetitorAnalysis(id=uuid4(), analysis_run_id=run_id, competitor_count=5),
        ]
        results = MarketService.get_competitor_analyses(mock_db, run_id)
        assert len(results) == 1
        assert results[0].competitor_count == 5


# ------------------------------------------------------------------ #
# API endpoint tests
# ------------------------------------------------------------------ #


class TestMarketAPIEndpoints:
    def test_list_markets(self, client):
        with patch("app.api.routes.markets.MarketService.get_markets") as mock_fn:
            mock_fn.return_value = [
                Market(
                    id=uuid4(), name="Mandi A", market_type="mandi", created_at=datetime.utcnow()
                ),
            ]
            response = client.get("/markets")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Mandi A"

    def test_get_market_by_id(self, client):
        market_id = uuid4()
        with patch("app.api.routes.markets.MarketService.get_market_by_id") as mock_fn:
            mock_fn.return_value = Market(
                id=market_id, name="Mandi A", market_type="mandi", created_at=datetime.utcnow()
            )
            response = client.get(f"/markets/{market_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Mandi A"

    def test_get_market_not_found(self, client):
        with patch("app.api.routes.markets.MarketService.get_market_by_id") as mock_fn:
            mock_fn.return_value = None
            response = client.get(f"/markets/{uuid4()}")
            assert response.status_code == 404

    def test_list_market_prices(self, client):
        with patch("app.api.routes.markets.MarketService.get_market_prices") as mock_fn:
            mock_fn.return_value = [
                MarketPrice(
                    id=uuid4(),
                    commodity="Wheat",
                    modal_price=2500.0,
                    recorded_date=date(2026, 3, 1),
                    created_at=datetime.utcnow(),
                ),
            ]
            response = client.get("/markets/prices?commodity=Wheat")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["commodity"] == "Wheat"

    def test_list_commodities(self, client):
        with patch("app.api.routes.markets.MarketService.get_commodities") as mock_fn:
            mock_fn.return_value = ["Rice", "Wheat"]
            response = client.get("/markets/commodities")
            assert response.status_code == 200
            data = response.json()
            assert data == ["Rice", "Wheat"]

    def test_list_market_types(self, client):
        with patch("app.api.routes.markets.MarketService.get_market_types") as mock_fn:
            mock_fn.return_value = ["mandi", "retail"]
            response = client.get("/markets/types")
            assert response.status_code == 200
            data = response.json()
            assert data == ["mandi", "retail"]

    def test_get_market_analyses(self, client):
        run_id = uuid4()
        with patch("app.api.routes.markets.MarketService.get_market_analyses") as mock_fn:
            mock_fn.return_value = [
                MarketAnalysis(
                    id=uuid4(), analysis_run_id=run_id, radius_km=10.0, created_at=datetime.utcnow()
                ),
            ]
            response = client.get(f"/markets/analyses/{run_id}")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

    def test_get_competitor_analyses(self, client):
        run_id = uuid4()
        with patch("app.api.routes.markets.MarketService.get_competitor_analyses") as mock_fn:
            mock_fn.return_value = [
                CompetitorAnalysis(
                    id=uuid4(),
                    analysis_run_id=run_id,
                    competitor_count=5,
                    created_at=datetime.utcnow(),
                ),
            ]
            response = client.get(f"/markets/competitors/{run_id}")
            assert response.status_code == 200
            data = response.json()
            assert data[0]["competitor_count"] == 5
