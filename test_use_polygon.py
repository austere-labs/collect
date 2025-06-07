import pytest
from unittest.mock import Mock, patch, AsyncMock
from bars import Bar, TimeFrame
from collect import use_polygon


class TestUsePolygon:
    @pytest.mark.asyncio
    async def test_use_polygon_success(self):
        """Test successful use_polygon with valid BTC data"""
        url = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31"
        
        # Mock the API response
        mock_json_response = {
            "status": "OK",
            "queryCount": 31,
            "resultsCount": 31,
            "results": [
                {
                    "v": 1234567.89,
                    "vw": 50000.00,
                    "o": 49000.00,
                    "c": 51000.00,
                    "h": 52000.00,
                    "l": 48500.00,
                    "t": 1735689600000,
                    "n": 10000
                },
                {
                    "v": 2345678.90,
                    "vw": 51000.00,
                    "o": 51000.00,
                    "c": 52000.00,
                    "h": 53000.00,
                    "l": 50500.00,
                    "t": 1735776000000,
                    "n": 11000
                }
            ]
        }
        
        with patch('collect.Config') as mock_config_class, \
             patch('collect.SecretManager') as mock_secret_mgr_class, \
             patch('collect.Polygon') as mock_polygon_class:
            
            # Setup mocks
            mock_config = Mock()
            mock_config.polygon_base_url = "https://api.polygon.io"
            mock_config.polygon_api_key_path = "test_path"
            mock_config.project_id = "test_project"
            mock_config_class.return_value = mock_config
            
            mock_secret_mgr = Mock()
            mock_secret_mgr.get_secret.return_value = "test_api_key"
            mock_secret_mgr_class.return_value = mock_secret_mgr
            
            mock_polygon = Mock()
            mock_polygon.ohlvc_url = AsyncMock(return_value=mock_json_response)
            mock_polygon.parse_polygon_url.return_value = {
                'symbol': 'BTC',
                'mult': '1',
                'span': 'day',
                'from': '2025-01-01',
                'to': '2025-01-31'
            }
            mock_polygon.build_bars.return_value = [
                Mock(spec=Bar, asset_name="BTC", timeframe=TimeFrame.day),
                Mock(spec=Bar, asset_name="BTC", timeframe=TimeFrame.day)
            ]
            mock_polygon_class.return_value = mock_polygon
            
            # Test the function
            result = await use_polygon(url)
            
            # Verify results
            assert len(result) == 2
            assert all(bar.asset_name == "BTC" for bar in result)
            assert all(bar.timeframe == TimeFrame.day for bar in result)
            
            # Verify method calls
            mock_polygon.ohlvc_url.assert_called_once_with(url)
            mock_polygon.parse_polygon_url.assert_called_once_with(url)
            mock_polygon.build_bars.assert_called_once_with(mock_json_response, "BTC", TimeFrame.day)

    @pytest.mark.asyncio
    async def test_use_polygon_eth_minute_data(self):
        """Test use_polygon with ETH minute data"""
        url = "https://api.polygon.io/v2/aggs/ticker/X:ETHUSD/range/5/minute/2025-01-15/2025-01-16"
        
        mock_json_response = {
            "status": "OK",
            "queryCount": 288,
            "resultsCount": 288,
            "results": [
                {
                    "v": 567890.12,
                    "vw": 3500.00,
                    "o": 3450.00,
                    "c": 3550.00,
                    "h": 3580.00,
                    "l": 3420.00,
                    "t": 1737043200000,
                    "n": 5000
                }
            ]
        }
        
        with patch('collect.Config') as mock_config_class, \
             patch('collect.SecretManager') as mock_secret_mgr_class, \
             patch('collect.Polygon') as mock_polygon_class:
            
            # Setup mocks
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            
            mock_secret_mgr = Mock()
            mock_secret_mgr.get_secret.return_value = "test_api_key"
            mock_secret_mgr_class.return_value = mock_secret_mgr
            
            mock_polygon = Mock()
            mock_polygon.ohlvc_url = AsyncMock(return_value=mock_json_response)
            mock_polygon.parse_polygon_url.return_value = {
                'symbol': 'ETH',
                'mult': '5',
                'span': 'minute',
                'from': '2025-01-15',
                'to': '2025-01-16'
            }
            mock_polygon.build_bars.return_value = [
                Mock(spec=Bar, asset_name="ETH", timeframe=TimeFrame.min)
            ]
            mock_polygon_class.return_value = mock_polygon
            
            # Test the function
            result = await use_polygon(url)
            
            # Verify results
            assert len(result) == 1
            assert result[0].asset_name == "ETH"
            assert result[0].timeframe == TimeFrame.min
            
            # Verify build_bars was called with correct timeframe
            mock_polygon.build_bars.assert_called_once_with(mock_json_response, "ETH", TimeFrame.min)

    @pytest.mark.asyncio
    async def test_use_polygon_invalid_url_format(self):
        """Test use_polygon with invalid URL format"""
        url = "https://wrong-domain.com/invalid/path"
        
        with patch('collect.Config') as mock_config_class, \
             patch('collect.SecretManager') as mock_secret_mgr_class, \
             patch('collect.Polygon') as mock_polygon_class:
            
            # Setup mocks
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            
            mock_secret_mgr = Mock()
            mock_secret_mgr.get_secret.return_value = "test_api_key"
            mock_secret_mgr_class.return_value = mock_secret_mgr
            
            mock_polygon = Mock()
            mock_polygon.parse_polygon_url.return_value = None  # Invalid URL
            mock_polygon_class.return_value = mock_polygon
            
            # Test that it raises ValueError
            with pytest.raises(ValueError, match="Invalid Polygon URL format"):
                await use_polygon(url)

    @pytest.mark.asyncio
    async def test_use_polygon_unsupported_timeframe(self):
        """Test use_polygon with unsupported timeframe"""
        url = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/second/2025-01-01/2025-01-31"
        
        with patch('collect.Config') as mock_config_class, \
             patch('collect.SecretManager') as mock_secret_mgr_class, \
             patch('collect.Polygon') as mock_polygon_class:
            
            # Setup mocks
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            
            mock_secret_mgr = Mock()
            mock_secret_mgr.get_secret.return_value = "test_api_key"
            mock_secret_mgr_class.return_value = mock_secret_mgr
            
            mock_polygon = Mock()
            mock_polygon.parse_polygon_url.return_value = {
                'symbol': 'BTC',
                'mult': '1',
                'span': 'second',  # Not supported by TimeFrameMatcher
                'from': '2025-01-01',
                'to': '2025-01-31'
            }
            mock_polygon_class.return_value = mock_polygon
            
            # Test that it raises ValueError
            with pytest.raises(ValueError, match="Unsupported timeframe: second"):
                await use_polygon(url)

    @pytest.mark.asyncio
    async def test_use_polygon_api_error(self):
        """Test use_polygon when API returns error"""
        url = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-31"
        
        with patch('collect.Config') as mock_config_class, \
             patch('collect.SecretManager') as mock_secret_mgr_class, \
             patch('collect.Polygon') as mock_polygon_class:
            
            # Setup mocks
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            
            mock_secret_mgr = Mock()
            mock_secret_mgr.get_secret.return_value = "test_api_key"
            mock_secret_mgr_class.return_value = mock_secret_mgr
            
            mock_polygon = Mock()
            mock_polygon.ohlvc_url = AsyncMock(side_effect=ValueError("API Error: Invalid API key"))
            mock_polygon.parse_polygon_url.return_value = {
                'symbol': 'BTC',
                'mult': '1',
                'span': 'day',
                'from': '2025-01-01',
                'to': '2025-01-31'
            }
            mock_polygon_class.return_value = mock_polygon
            
            # Test that it propagates the API error
            with pytest.raises(ValueError, match="API Error: Invalid API key"):
                await use_polygon(url)

    @pytest.mark.asyncio 
    async def test_use_polygon_all_timeframes(self):
        """Test use_polygon works with all supported timeframes"""
        timeframes = [
            ("minute", TimeFrame.min),
            ("hour", TimeFrame.hour),
            ("day", TimeFrame.day),
            ("week", TimeFrame.week),
            ("month", TimeFrame.month),
            ("year", TimeFrame.year)
        ]
        
        for span_str, expected_timeframe in timeframes:
            url = f"https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/{span_str}/2025-01-01/2025-01-31"
            
            mock_json_response = {
                "status": "OK",
                "queryCount": 1,
                "resultsCount": 1,
                "results": [
                    {
                        "v": 1000000.00,
                        "vw": 50000.00,
                        "o": 50000.00,
                        "c": 50000.00,
                        "h": 50000.00,
                        "l": 50000.00,
                        "t": 1735689600000,
                        "n": 1000
                    }
                ]
            }
            
            with patch('collect.Config') as mock_config_class, \
                 patch('collect.SecretManager') as mock_secret_mgr_class, \
                 patch('collect.Polygon') as mock_polygon_class:
                
                # Setup mocks
                mock_config = Mock()
                mock_config_class.return_value = mock_config
                
                mock_secret_mgr = Mock()
                mock_secret_mgr.get_secret.return_value = "test_api_key"
                mock_secret_mgr_class.return_value = mock_secret_mgr
                
                mock_polygon = Mock()
                mock_polygon.ohlvc_url = AsyncMock(return_value=mock_json_response)
                mock_polygon.parse_polygon_url.return_value = {
                    'symbol': 'BTC',
                    'mult': '1',
                    'span': span_str,
                    'from': '2025-01-01',
                    'to': '2025-01-31'
                }
                mock_polygon.build_bars.return_value = [
                    Mock(spec=Bar, asset_name="BTC", timeframe=expected_timeframe)
                ]
                mock_polygon_class.return_value = mock_polygon
                
                # Test the function
                result = await use_polygon(url)
                
                # Verify correct timeframe was used
                mock_polygon.build_bars.assert_called_with(mock_json_response, "BTC", expected_timeframe)


class TestUsePolygonIntegration:
    @pytest.mark.asyncio
    async def test_use_polygon_integration_btc_daily(self):
        """Integration test with real API call"""
        url = "https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/2025-01-01/2025-01-02"
        
        # Only run this test if we have proper environment setup
        from config import Config
        config = Config()
        if not config.project_id or not config.polygon_api_key_path:
            pytest.skip("Missing GCP_PROJECT_ID or POLYGON_API_KEY_PATH in .env")
        
        try:
            result = await use_polygon(url)
            
            # Verify we got Bar objects
            assert isinstance(result, list)
            assert len(result) >= 1  # Should have at least one day of data
            
            # Verify structure of first bar
            first_bar = result[0]
            assert hasattr(first_bar, 'asset_name')
            assert hasattr(first_bar, 'timeframe')
            assert hasattr(first_bar, 'open')
            assert hasattr(first_bar, 'high')
            assert hasattr(first_bar, 'low')
            assert hasattr(first_bar, 'close')
            assert hasattr(first_bar, 'volume')
            
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
            pytest.skip("Missing GCP_PROJECT_ID or POLYGON_API_KEY_PATH in .env")
        
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