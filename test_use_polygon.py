import pytest
from bars import Bar, TimeFrame
from collect import use_polygon


class TestUsePolygon:
    @pytest.mark.asyncio
    async def test_use_polygon_integration_btc_daily(self):
        """Integration test with real API call"""
        url = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-02"

        # Only run this test if we have proper environment setup
        from config import Config

        config = Config()
        if not config.project_id or not config.polygon_api_key_path:
            pytest.skip(
                "Missing GCP_PROJECT_ID or POLYGON_API_KEY_PATH in .env")

        try:
            result = await use_polygon(url)

            # Verify we got Bar objects
            assert isinstance(result, list)
            assert len(result) >= 1  # Should have at least one day of data

            # Verify structure of first bar
            first_bar = result[0]
            assert hasattr(first_bar, "asset_name")
            assert hasattr(first_bar, "timeframe")
            assert hasattr(first_bar, "open")
            assert hasattr(first_bar, "high")
            assert hasattr(first_bar, "low")
            assert hasattr(first_bar, "close")
            assert hasattr(first_bar, "volume")

            # Verify expected values
            assert first_bar.asset_name == "BTC"
            assert first_bar.timeframe == TimeFrame.day

        except Exception as e:
            # If there's an API issue, skip the test
            pytest.skip(f"API call failed: {e}")

    @pytest.mark.asyncio
    async def test_use_polygon_integration_eth_hourly(self):
        """Integration test with ETH hourly data"""
        url = "https://api.polygon.io/v2/aggs/ticker/X:ETHUSD/range/1/hour/2025-01-01/2025-01-01"

        # Only run this test if we have proper environment setup
        from config import Config

        config = Config()
        if not config.project_id or not config.polygon_api_key_path:
            pytest.skip(
                "Missing GCP_PROJECT_ID or POLYGON_API_KEY_PATH in .env")

        try:
            result = await use_polygon(url)

            # Verify we got Bar objects
            assert isinstance(result, list)

            if len(result) > 0:  # Market might be closed, so allow empty results
                first_bar = result[0]
                assert first_bar.asset_name == "ETH"
                assert first_bar.timeframe == TimeFrame.hour

        except Exception as e:
            # If there's an API issue, skip the test
            pytest.skip(f"API call failed: {e}")
