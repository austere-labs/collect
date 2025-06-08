import pytest
import aiohttp
from datetime import datetime
from config import Config
from secret_manager import SecretManager
from polygon.polygon import Polygon


@pytest.fixture
def polygon():
    config = Config()
    # For integration tests, we need the actual API key
    if not config.project_id or not config.polygon_api_key_path:
        pytest.skip("Missing GCP_PROJECT_ID or POLYGON_API_KEY_PATH in .env")

    secret_mgr = SecretManager(config.project_id)
    polygon_api_key = secret_mgr.get_secret(config.polygon_api_key_path)
    return Polygon(config.polygon_base_url, polygon_api_key)


class TestBuildOhlcvUrl:
    def test_build_ohlcv_url_basic(self, polygon):
        url = polygon.build_ohlcv_url(
            symbol="BTC",
            mult=1,
            span="day",
            dfrom="2025-01-01",
            dto="2025-01-31",
            adjusted=True,
            sort="asc",
            limit=120,
        )

        expected = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31?adjusted=true&sort=asc&limit=120"
        assert url == expected

    def test_build_ohlcv_url_with_datetime_objects(self, polygon):
        url = polygon.build_ohlcv_url(
            symbol="ETH",
            mult=5,
            span="minute",
            dfrom=datetime(2025, 1, 15),
            dto=datetime(2025, 1, 16),
            adjusted=False,
            sort="desc",
            limit=1000,
        )

        expected = "https://api.polygon.io/v2/aggs/ticker/X:ETHUSD/range/5/minute/2025-01-15/2025-01-16?adjusted=false&sort=desc&limit=1000"
        assert url == expected

    def test_build_ohlcv_url_defaults(self, polygon):
        url = polygon.build_ohlcv_url(
            symbol="SOL", mult=1, span="hour", dfrom="2025-01-01", dto="2025-01-02"
        )

        expected = "https://api.polygon.io/v2/aggs/ticker/X:SOLUSD/range/1/hour/2025-01-01/2025-01-02?adjusted=false&sort=desc&limit=5000"
        assert url == expected

    def test_build_ohlcv_url_invalid_mult(self, polygon):
        with pytest.raises(ValueError, match="Multiplier must be >= 1"):
            polygon.build_ohlcv_url(
                symbol="BTC", mult=0, span="day", dfrom="2025-01-01", dto="2025-01-31"
            )

    def test_build_ohlcv_url_invalid_limit_too_low(self, polygon):
        with pytest.raises(ValueError, match="Limit must be between 1 and 50000"):
            polygon.build_ohlcv_url(
                symbol="BTC",
                mult=1,
                span="day",
                dfrom="2025-01-01",
                dto="2025-01-31",
                limit=0,
            )

    def test_build_ohlcv_url_invalid_limit_too_high(self, polygon):
        with pytest.raises(ValueError, match="Limit must be between 1 and 50000"):
            polygon.build_ohlcv_url(
                symbol="BTC",
                mult=1,
                span="day",
                dfrom="2025-01-01",
                dto="2025-01-31",
                limit=50001,
            )

    def test_build_ohlcv_url_all_spans(self, polygon):
        spans = ["year", "month", "week", "day", "hour", "minute", "second"]
        for span in spans:
            url = polygon.build_ohlcv_url(
                symbol="BTC", mult=1, span=span, dfrom="2025-01-01", dto="2025-01-31"
            )
            assert f"/range/1/{span}/" in url


class TestParsePolygonUrl:
    def test_parse_polygon_url_basic(self, polygon):
        url = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31"
        result = polygon.parse_polygon_url(url)

        expected = {
            "symbol": "BTC",
            "mult": "1",
            "span": "day",
            "from": "2025-01-01",
            "to": "2025-01-31",
        }
        assert result == expected

    def test_parse_polygon_url_with_query_params(self, polygon):
        url = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31?adjusted=true&sort=asc&limit=120"
        result = polygon.parse_polygon_url(url)

        expected = {
            "symbol": "BTC",
            "mult": "1",
            "span": "day",
            "from": "2025-01-01",
            "to": "2025-01-31",
        }
        assert result == expected

    def test_parse_polygon_url_eth_minute(self, polygon):
        url = "https://api.polygon.io/v2/aggs/ticker/X:ETHUSD/range/5/minute/2025-01-15/2025-01-16"
        result = polygon.parse_polygon_url(url)

        expected = {
            "symbol": "ETH",
            "mult": "5",
            "span": "minute",
            "from": "2025-01-15",
            "to": "2025-01-16",
        }
        assert result == expected

    def test_parse_polygon_url_sol_hour(self, polygon):
        url = "https://api.polygon.io/v2/aggs/ticker/X:SOLUSD/range/2/hour/2024-12-01/2024-12-31"
        result = polygon.parse_polygon_url(url)

        expected = {
            "symbol": "SOL",
            "mult": "2",
            "span": "hour",
            "from": "2024-12-01",
            "to": "2024-12-31",
        }
        assert result == expected

    def test_parse_polygon_url_invalid_url(self, polygon):
        url = "https://wrong-domain.com/invalid/path"
        result = polygon.parse_polygon_url(url)
        assert result is None

    def test_parse_polygon_url_malformed_ticker(self, polygon):
        url = "https://api.polygon.io/v2/aggs/ticker/BTCUSD/range/1/day/2025-01-01/2025-01-31"
        result = polygon.parse_polygon_url(url)
        assert result is None

    def test_parse_polygon_url_missing_dates(self, polygon):
        url = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/"
        result = polygon.parse_polygon_url(url)
        assert result is None


class TestOhlvcUrlIntegration:
    @pytest.mark.asyncio
    async def test_ohlvc_url_btc_january_2025(self, polygon):
        """Test fetching BTC daily data for January 2025"""
        url = polygon.build_ohlcv_url(
            symbol="BTC",
            mult=1,
            span="day",
            dfrom="2025-01-01",
            dto="2025-01-31",
            adjusted=True,
            sort="asc",
            limit=120,
        )

        result = await polygon.ohlvc_url(url)

        assert result["status"] == "OK"
        assert result["queryCount"] == 31
        assert result["resultsCount"] == 31
        assert "results" in result
        assert len(result["results"]) == 31

        # Verify first result structure
        first_bar = result["results"][0]
        assert "o" in first_bar  # open
        assert "h" in first_bar  # high
        assert "l" in first_bar  # low
        assert "c" in first_bar  # close
        assert "v" in first_bar  # volume
        assert "vw" in first_bar  # vwap
        assert "t" in first_bar  # timestamp
        assert "n" in first_bar  # number of transactions

    @pytest.mark.asyncio
    async def test_ohlvc_url_eth_hourly_data(self, polygon):
        """Test fetching ETH hourly data for a specific date"""
        url = polygon.build_ohlcv_url(
            symbol="ETH",
            mult=1,
            span="hour",
            dfrom="2025-01-01",
            dto="2025-01-02",
            adjusted=False,
            sort="asc",
            limit=50,
        )

        result = await polygon.ohlvc_url(url)

        assert result["status"] == "OK"
        assert "results" in result
        assert len(result["results"]) <= 24  # Max 24 hours in a day

    @pytest.mark.asyncio
    async def test_ohlvc_url_invalid_url(self, polygon):
        """Test that invalid URLs raise appropriate errors"""
        url = "https://wrong-domain.com/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31"

        with pytest.raises(ValueError, match="URL must start with"):
            await polygon.ohlvc_url(url)

    @pytest.mark.asyncio
    async def test_ohlvc_url_invalid_symbol(self, polygon):
        """Test fetching data for an invalid symbol"""
        url = polygon.build_ohlcv_url(
            symbol="INVALID_SYMBOL_XYZ",
            mult=1,
            span="day",
            dfrom="2025-01-01",
            dto="2025-01-31",
        )

        result = await polygon.ohlvc_url(url)

        # Polygon typically returns empty results for invalid symbols
        assert result["status"] == "OK"
        assert result["resultsCount"] == 0
        # When no results, 'results' key may not be present
        assert result.get("results", []) == []

    @pytest.mark.asyncio
    async def test_ohlvc_url_future_dates(self, polygon):
        """Test fetching data for future dates (should return empty)"""
        url = polygon.build_ohlcv_url(
            symbol="BTC", mult=1, span="day", dfrom="2030-01-01", dto="2030-12-31"
        )

        result = await polygon.ohlvc_url(url)

        assert result["status"] == "OK"
        assert result["resultsCount"] == 0
        # When no results, 'results' key may not be present
        assert result.get("results", []) == []

    @pytest.mark.asyncio
    async def test_ohlvc_url_minute_data(self, polygon):
        """Test fetching minute-level data"""
        url = polygon.build_ohlcv_url(
            symbol="BTC",
            mult=5,
            span="minute",
            dfrom="2025-01-01",
            dto="2025-01-01",
            limit=100,
        )

        result = await polygon.ohlvc_url(url)

        assert result["status"] == "OK"
        assert "results" in result
        # Verify we get minute-level granularity
        if len(result["results"]) > 0:
            assert all("t" in bar for bar in result["results"])

    @pytest.mark.asyncio
    async def test_ohlvc_url_large_date_range(self, polygon):
        """Test fetching data for a large date range"""
        url = polygon.build_ohlcv_url(
            symbol="BTC",
            mult=1,
            span="day",
            dfrom="2024-01-01",
            dto="2024-12-31",
            limit=500,
        )

        result = await polygon.ohlvc_url(url)

        assert result["status"] == "OK"
        assert "results" in result
        # Should have data for most days in 2024
        assert len(result["results"]) > 300

    @pytest.mark.asyncio
    async def test_ohlvc_url_connection_timeout(self, polygon):
        """Test that connection timeouts are handled properly"""
        # Create URL that might timeout (using very large limit)
        url = polygon.build_ohlcv_url(
            symbol="BTC",
            mult=1,
            span="minute",
            dfrom="2020-01-01",
            dto="2024-12-31",
            limit=50000,
        )

        # This should either succeed or raise aiohttp.ClientError
        try:
            result = await polygon.ohlvc_url(url)
            assert result["status"] in ["OK", "ERROR"]
        except aiohttp.ClientError:
            # Expected if timeout occurs
            pass
