import asyncio
from collect import use_polygon

async def test_mcp_polygon():
    url = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31?adjusted=true&sort=asc&limit=120"
    
    print("Starting MCP polygon test...")
    try:
        result = await use_polygon(url)
        print(f"Success! Got {len(result)} bars")
        print(f"First bar: {result[0]}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_polygon())