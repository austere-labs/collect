import pytest
from secret_manager import SecretManager
from config import Config
from polygon.polygon import Polygon
from bars import TimeFrameMatcher


@pytest.fixture
def polygon() -> Polygon:
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    api_key = secret_mgr.get_secret(config.polygon_api_key_path)
    return Polygon(config.polygon_base_url, api_key)


@pytest.mark.asyncio
async def test_ohlcv(polygon):
    url = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31?adjusted=true&sort=asc&limit=120"

    # Parse URL and validate components
    parsed_url = polygon.parse_polygon_url(url)
    assert parsed_url is not None, "Failed to parse polygon URL"
    assert parsed_url["symbol"] == "BTC", f"Expected symbol 'BTC', got {
        parsed_url['symbol']}"
    assert parsed_url["span"] == "day", f"Expected span 'day', got {
        parsed_url['span']}"
    assert parsed_url["mult"] == "1", f"Expected mult '1', got {
        parsed_url['mult']}"
    assert parsed_url["from"] == "2025-01-01", f"Expected from '2025-01-01', got {
        parsed_url['from']}"
    assert parsed_url["to"] == "2025-01-31", f"Expected to '2025-01-31', got {
        parsed_url['to']}"

    # Validate timeframe before making API call
    matcher = TimeFrameMatcher()
    timeframe = matcher.match(parsed_url["span"])
    assert timeframe is not None, f"Failed to match timeframe for span '{
        parsed_url['span']}'"

    # Fetch data from API
    json_response = await polygon.ohlvc_url(url)
    assert "results" in json_response, "API response missing 'results' field"
    assert len(json_response["results"]
               ) > 0, "API response contains no results"

    symbol = parsed_url["symbol"]
    assert symbol == "BTC", f"Expected symbol 'BTC', got {symbol}"

    # Build bars and validate
    bars = polygon.build_bars(json_response, symbol, timeframe)
    assert len(bars) > 0, "No bars were built from API response"
    assert len(bars) == len(json_response["results"]), f"Expected {
        len(json_response['results'])} bars, got {len(bars)}"

    # Validate first bar structure
    first_bar = bars[0]
    assert first_bar.asset_name == "BTC", f"Expected asset_name 'BTC', got {
        first_bar.asset_name}"
    assert first_bar.timeframe == timeframe, f"Expected timeframe {
        timeframe}, got {first_bar.timeframe}"
    assert first_bar.open > 0, f"Expected positive open price, got {
        first_bar.open}"
    assert first_bar.high > 0, f"Expected positive high price, got {
        first_bar.high}"
    assert first_bar.low > 0, f"Expected positive low price, got {
        first_bar.low}"
    assert first_bar.close > 0, f"Expected positive close price, got {
        first_bar.close}"
    assert first_bar.volume >= 0, f"Expected non-negative volume, got {
        first_bar.volume}"

    # Validate OHLC relationships
    assert first_bar.high >= first_bar.open, "High should be >= open"
    assert first_bar.high >= first_bar.close, "High should be >= close"
    assert first_bar.low <= first_bar.open, "Low should be <= open"
    assert first_bar.low <= first_bar.close, "Low should be <= close"

    print(f"Successfully processed {len(bars)} bars for {symbol}")
    print(f"Sample bar: {first_bar}")
