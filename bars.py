from pydantic import BaseModel
from enum import Enum
from decimal import Decimal
from typing import Optional


class TimeFrame(Enum):
    min = "min"
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"
    year = "year"


class TimeFrameMatcher:
    def __init__(self):
        self.mappings = {
            # Minute variations
            "minute": TimeFrame.min,
            "minutes": TimeFrame.min,
            "min": TimeFrame.min,
            "m": TimeFrame.min,
            
            # Hour variations  
            "hour": TimeFrame.hour,
            "hours": TimeFrame.hour,
            "h": TimeFrame.hour,
            
            # Day variations
            "day": TimeFrame.day,
            "days": TimeFrame.day,
            "d": TimeFrame.day,
            
            # Week variations
            "week": TimeFrame.week,
            "weeks": TimeFrame.week,
            "w": TimeFrame.week,
            
            # Month variations
            "month": TimeFrame.month,
            "months": TimeFrame.month,
            "mo": TimeFrame.month,
            
            # Year variations
            "year": TimeFrame.year,
            "years": TimeFrame.year,
            "y": TimeFrame.year,
        }
    
    def match(self, span: str) -> Optional[TimeFrame]:
        """
        Match a string to a TimeFrame enum value.
        
        Args:
            span: String representation of timeframe (e.g. "day", "minute", "h", etc.)
            
        Returns:
            TimeFrame enum value or None if no match found
            
        Example:
            >>> matcher = TimeFrameMatcher()
            >>> matcher.match("day")
            <TimeFrame.day: 'day'>
            >>> matcher.match("minutes")
            <TimeFrame.min: 'min'>
        """
        return self.mappings.get(span.lower())
    
    def get_supported_strings(self) -> list[str]:
        """
        Get all supported string representations.
        
        Returns:
            List of all supported string values
        """
        return list(self.mappings.keys())


class Bar(BaseModel):
    timestamp: int
    timeframe: TimeFrame
    asset_name: str
    open: Decimal
    high: Decimal
    close: Decimal
    low: Decimal
    volume: Decimal
    vwap: Decimal
    num_trx: int
    readable_timestamp: str
    atr: Decimal
