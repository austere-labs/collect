from pydantic import BaseModel
from enum import Enum


class TimeFrame(str, Enum):
    MIN = "min"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"


class Bar(BaseModel):
    timeframe: TimeFrame
    assetName: str
    open: float
    high: float
    close: float
    low: float
    volume: float
    vwap: float
    numTrx: int
    timestampInt: int
    readableTimestamp: str
    trueRange: float
    typicalPrice: float
    eightDayEMA: float
    twentyOneDayEMA: float
    fiftyDayEMA: float
    twoHundredDayEMA: float
    RSI: float
    MFI: float
    ATR: float
    alphaTrend: float
    buySignal: bool
    sellSignal: bool

    class Config:
        # Use field aliases to match the JSON field names exactly
        allow_population_by_field_name = True
        fields = {
            "timeframe": {"alias": "timeframe"},
            "assetName": {"alias": "assetName"},
            "open": {"alias": "open"},
            "high": {"alias": "high"},
            "close": {"alias": "close"},
            "low": {"alias": "low"},
            "volume": {"alias": "volume"},
            "vwap": {"alias": "vwap"},
            "numTrx": {"alias": "numTrx"},
            "timestampInt": {"alias": "timestampInt"},
            "readableTimestamp": {"alias": "readableTimestamp"},
            "trueRange": {"alias": "trueRange"},
            "typicalPrice": {"alias": "typicalPrice"},
            "eightDayEMA": {"alias": "eightDayEMA"},
            "twentyOneDayEMA": {"alias": "twentyOneDayEMA"},
            "fiftyDayEMA": {"alias": "fiftyDayEMA"},
            "twoHundredDayEMA": {"alias": "twoHundredDayEMA"},
            "RSI": {"alias": "RSI"},
            "MFI": {"alias": "MFI"},
            "ATR": {"alias": "ATR"},
            "alphaTrend": {"alias": "alphaTrend"},
            "buySignal": {"alias": "buySignal"},
            "sellSignal": {"alias": "sellSignal"},
        }
