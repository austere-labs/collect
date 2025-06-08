# Polygon API Usage Guide

## Tool: `use_polygon`

The `use_polygon` tool fetches and processes financial market data from the Polygon.io API. It takes a single argument - a properly formatted Polygon API URL.

## URL Format

The URL must follow this exact pattern:
```
https://api.polygon.io/v2/aggs/ticker/X:{SYMBOL}USD/range/{MULTIPLIER}/{TIMEFRAME}/{FROM_DATE}/{TO_DATE}
```

### Parameters:
- **SYMBOL**: The cryptocurrency symbol (e.g., BTC, ETH, SOL)
- **MULTIPLIER**: The time multiplier (e.g., 1, 5, 15)
- **TIMEFRAME**: The time unit - one of:
  - `minute`
  - `hour`
  - `day`
  - `week`
  - `month`
  - `year`
- **FROM_DATE**: Start date in YYYY-MM-DD format
- **TO_DATE**: End date in YYYY-MM-DD format

## Examples

### Daily Bitcoin data for January 2025:
```
use_polygon("https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31")
```

### Hourly Ethereum data for a specific day:
```
use_polygon("https://api.polygon.io/v2/aggs/ticker/X:ETHUSD/range/1/hour/2025-01-15/2025-01-15")
```

### 5-minute Solana data:
```
use_polygon("https://api.polygon.io/v2/aggs/ticker/X:SOLUSD/range/5/minute/2025-01-20/2025-01-21")
```

### Weekly Bitcoin data for a year:
```
use_polygon("https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/week/2024-01-01/2024-12-31")
```

## Return Value

The tool returns a list of `Bar` objects, each containing:
- `asset_name`: The symbol (e.g., "BTC")
- `timeframe`: The timeframe enum
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `volume`: Trading volume
- `vwap`: Volume-weighted average price
- `num_trx`: Number of transactions
- `timestamp`: Unix timestamp in milliseconds
- `readable_timestamp`: Human-readable timestamp
- `atr`: Average true range

## Common Use Cases

1. **Price Analysis**: Fetch historical price data for technical analysis
2. **Volume Studies**: Analyze trading volume patterns
3. **Multi-timeframe Analysis**: Compare different timeframes for the same asset
4. **Market Comparison**: Compare different cryptocurrencies over the same period

## Error Handling

The tool validates:
- URL format must match the expected pattern
- Timeframe must be supported (minute, hour, day, week, month, year)
- API key must be configured in the environment
- Network and API responses are handled gracefully

If the URL format is incorrect or the timeframe is unsupported, you'll receive a `ValueError` with a descriptive message.