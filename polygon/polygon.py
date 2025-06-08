import aiohttp
import re
from typing import List, Dict, Literal, Union, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from bars import Bar, TimeFrame


class Polygon:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.api_key = api_key
        self.baseurl = base_url
        self.headers = {
            "Accepts": "application/json",
            "Authorization": "Bearer " + self.api_key,
        }
        self.todays_date = datetime.now().strftime("%Y-%m-%d")
        self.yesterdays_date = self.get_yesterdays_date()

    def get_yesterdays_date(self) -> str:
        current_date = datetime.now()

        if current_date.day == 1:
            # If today is the first day of the month, subtract one day
            # and move to the last day of the previous month
            previous_month = datetime(
                current_date.year, current_date.month, 1
            ) - timedelta(days=1)
            previous_date = previous_month.strftime("%Y-%m-%d")
        else:
            # Otherwise, subtract one day to get the previous day
            # in the current month
            previous_date = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")

        return previous_date

    def format_symbol(self, symbol: str) -> str:
        return f"X:{symbol}USD"

    def convert_date(self, timestamp: str) -> str:
        timestamp_msec = int(timestamp)
        timestamp_sec = timestamp_msec / 1000
        formated_date = datetime.fromtimestamp(timestamp_sec).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return formated_date

    def build_ohlcv_url(
        self,
        symbol: str,
        mult: int,
        span: Literal["year", "month", "week", "day", "hour", "minute", "second"],
        dfrom: Union[str, datetime],
        dto: Union[str, datetime],
        adjusted: bool = False,
        sort: Literal["asc", "desc"] = "desc",
        limit: int = 5000,
    ) -> str:
        """
        Build OHCLV aggregate URL for Polygon.io API.

        Args:
            symbol: Asset symbol (e.g. BTC, ETH)
            mult: The multiplier for the timespan (e.g. 1 for daily)
            span: The timespan unit
            dfrom: Start date (YYYY-MM-DD or datetime object)
            dto: End date (YYYY-MM-DD or datetime object)
            adjusted: Whether to adjust for splits
            sort: Sort order by timestamp
            limit: Max results per page (max 50000)

        Returns:
            Complete URL string for the API request

        Raises:
            ValueError: Invalid parameters
        """
        # Validate inputs
        if mult < 1:
            raise ValueError("Multiplier must be >= 1")
        if limit < 1 or limit > 50000:
            raise ValueError("Limit must be between 1 and 50000")

        # Format dates if needed
        if isinstance(dfrom, datetime):
            dfrom = dfrom.strftime("%Y-%m-%d")
        if isinstance(dto, datetime):
            dto = dto.strftime("%Y-%m-%d")

        # Build URL
        fsym = self.format_symbol(symbol)
        endpoint = f"/v2/aggs/ticker/{fsym}/range/{mult}/{span}/{dfrom}/{dto}"

        # Build query parameters
        params = [f"adjusted={str(adjusted).lower()}", f"sort={sort}", f"limit={limit}"]

        query_string = "&".join(params)
        url = f"{self.baseurl}{endpoint}?{query_string}"

        return url

    def parse_polygon_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Parse a Polygon API URL to extract components.

        Args:
            url: Complete Polygon API URL
                (e.g. https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31)

        Returns:
            Dict containing parsed components: symbol, mult, span, from, to
            Returns None if URL doesn't match expected pattern

        Example:
            >>> polygon.parse_polygon_url("https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31")
            {'symbol': 'BTC', 'mult': '1', 'span': 'day', 'from': '2025-01-01', 'to': '2025-01-31'}
        """
        pattern = r"/ticker/X:(?P<symbol>\w+)USD/range/(?P<mult>\d+)/(?P<span>\w+)/(?P<from>\d{4}-\d{2}-\d{2})/(?P<to>\d{4}-\d{2}-\d{2})"
        match = re.search(pattern, url)
        if match:
            return match.groupdict()
        return None

    async def ohlvc_url(self, url: str) -> Dict:
        """
        Fetch data from any Polygon API URL.

        Args:
            url: Complete Polygon API URL (
            e.g. https://api.polygon.io/v2/aggs/ticker/...
            )

        Returns:
            Dict containing the API response

        Raises:
            ValueError: Invalid URL or API error
            aiohttp.ClientError: Request failed
        """
        # Validate URL
        if not url.startswith(self.baseurl):
            raise ValueError(f"URL must start with {self.baseurl}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    # Validate response
                    if "status" in data and data["status"] == "ERROR":
                        raise ValueError(
                            f"API Error: {data.get('error', 'Unknown error')}"
                        )

                    return data

            except aiohttp.ClientError as e:
                raise aiohttp.ClientError(f"Request failed: {str(e)}")

    def build_bars(
        self, json_response: dict, asset_name: str, timeframe: TimeFrame
    ) -> List[Bar]:
        # ensure they are sorted by timestamp, THIS IS IMPORTANT
        # as we need the oldest bar first to calculate each new bar from
        # previous bar
        sorted_ohlcv_results = sorted(
            json_response["results"], key=lambda item: item["t"]
        )

        # setup the vars needed to process ohlcv
        prev_bar = None
        ohlcv_list = []
        for i, ohlcv in enumerate(sorted_ohlcv_results):
            # if index is zero this is the last period element
            # and we need to store it as the previous ohlcv
            if i == 0:
                # So we store this ohlcv to be referenced as prev_ohlcv["c"]
                # in the next iteration
                # so we can calculate the true range for the next ohlcv
                # this Bar will not have a true range because we don't have
                # the previous close
                newbar = Bar(
                    timeframe=timeframe,
                    asset_name=asset_name,
                    open=Decimal(str(ohlcv["o"])),
                    high=Decimal(str(ohlcv["h"])),
                    close=Decimal(str(ohlcv["c"])),
                    low=Decimal(str(ohlcv["l"])),
                    volume=Decimal(str(ohlcv["v"])),
                    vwap=Decimal(str(ohlcv["vw"])),
                    num_trx=ohlcv["n"],
                    timestamp=ohlcv["t"],
                    readable_timestamp=self.convert_date(ohlcv["t"]),
                    atr=Decimal("0"),
                )

                ohlcv_list.append(newbar)
                prev_bar = newbar
                continue

            # process remaining bars after marking the first bar
            newbar = Bar(
                timeframe=timeframe,
                asset_name=asset_name,
                open=Decimal(str(ohlcv["o"])),
                high=Decimal(str(ohlcv["h"])),
                close=Decimal(str(ohlcv["c"])),
                low=Decimal(str(ohlcv["l"])),
                volume=Decimal(str(ohlcv["v"])),
                vwap=Decimal(str(ohlcv["vw"])),
                num_trx=ohlcv["n"],
                timestamp=ohlcv["t"],
                readable_timestamp=self.convert_date(ohlcv["t"]),
                atr=Decimal("0"),
            )

            ohlcv_list.append(newbar)
            prev_bar = newbar

        return ohlcv_list
