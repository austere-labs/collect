from bars import TimeFrame, TimeFrameMatcher


class TestTimeFrameMatcher:
    def test_timeframe_matcher_minute_variations(self):
        matcher = TimeFrameMatcher()

        assert matcher.match("minute") == TimeFrame.min
        assert matcher.match("minutes") == TimeFrame.min
        assert matcher.match("min") == TimeFrame.min
        assert matcher.match("m") == TimeFrame.min
        assert matcher.match("MINUTE") == TimeFrame.min  # Case insensitive

    def test_timeframe_matcher_hour_variations(self):
        matcher = TimeFrameMatcher()

        assert matcher.match("hour") == TimeFrame.hour
        assert matcher.match("hours") == TimeFrame.hour
        assert matcher.match("h") == TimeFrame.hour
        assert matcher.match("HOUR") == TimeFrame.hour

    def test_timeframe_matcher_day_variations(self):
        matcher = TimeFrameMatcher()

        assert matcher.match("day") == TimeFrame.day
        assert matcher.match("days") == TimeFrame.day
        assert matcher.match("d") == TimeFrame.day
        assert matcher.match("DAY") == TimeFrame.day

    def test_timeframe_matcher_week_variations(self):
        matcher = TimeFrameMatcher()

        assert matcher.match("week") == TimeFrame.week
        assert matcher.match("weeks") == TimeFrame.week
        assert matcher.match("w") == TimeFrame.week

    def test_timeframe_matcher_month_variations(self):
        matcher = TimeFrameMatcher()

        assert matcher.match("month") == TimeFrame.month
        assert matcher.match("months") == TimeFrame.month
        assert matcher.match("mo") == TimeFrame.month

    def test_timeframe_matcher_year_variations(self):
        matcher = TimeFrameMatcher()

        assert matcher.match("year") == TimeFrame.year
        assert matcher.match("years") == TimeFrame.year
        assert matcher.match("y") == TimeFrame.year

    def test_timeframe_matcher_invalid_input(self):
        matcher = TimeFrameMatcher()

        assert matcher.match("invalid") is None
        assert matcher.match("") is None
        assert matcher.match("sec") is None
        assert matcher.match("second") is None

    def test_get_supported_strings(self):
        matcher = TimeFrameMatcher()
        supported = matcher.get_supported_strings()

        # Check that all expected strings are present
        expected_strings = [
            "minute",
            "minutes",
            "min",
            "m",
            "hour",
            "hours",
            "h",
            "day",
            "days",
            "d",
            "week",
            "weeks",
            "w",
            "month",
            "months",
            "mo",
            "year",
            "years",
            "y",
        ]

        for expected in expected_strings:
            assert expected in supported

        assert len(supported) == len(expected_strings)

    def test_polygon_api_strings(self):
        """Test that Polygon API strings work correctly"""
        matcher = TimeFrameMatcher()

        # These are the exact strings from Polygon API
        assert matcher.match("minute") == TimeFrame.min
        assert matcher.match("hour") == TimeFrame.hour
        assert matcher.match("day") == TimeFrame.day
        assert matcher.match("week") == TimeFrame.week
        assert matcher.match("month") == TimeFrame.month
        assert matcher.match("year") == TimeFrame.year
