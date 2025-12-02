import pytest
from unittest.mock import MagicMock, AsyncMock

# Define sample RAW data
RAW_HOURLY_DATA = {
    "hourly": [
        {
            "dt": 1704067200,  # 2024-01-01 00:00:00 UTC
            "temp": 15.5,
            "weather": [{"icon": "01d"}]
        }
    ]
}

RAW_CURRENT_DATA = {
    "current": {
        "temp": 20.0,
        "feels_like": 19.5,
        "humidity": 60,
        "wind_speed": 5.0,
        "weather": [{"description": "clear sky", "icon": "02d"}]
    }
}

# pytest tests/test_openweather.py::test_get_hourly_weather
@pytest.mark.asyncio
async def test_get_hourly_weather(async_client, mocker):
    """Test fetching hourly weather."""
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = RAW_HOURLY_DATA
    mock_response.raise_for_status.return_value = None

    # Define mock client context
    mock_client_instance = MagicMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_context = MagicMock()
    mock_client_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_context.__aexit__ = AsyncMock(return_value=None)

    mocker.patch(
        "app.services.openweather_service.httpx.AsyncClient",
        return_value=mock_client_context
    )

    response = await async_client.get("/weather/hourly")

    # Construct the expected parsed data
    expected_parsed_data = [
        {
            "timestamp": "2024-01-01T00:00:00Z",
            "temperature": 15.5,
            "icon_code": "01d",
            "icon_url": "https://openweathermap.org/img/wn/01d@2x.png"
        }
    ]

    assert response.status_code == 200
    assert response.json() == expected_parsed_data

# pytest tests/test_openweather.py::test_get_current_weather
@pytest.mark.asyncio
async def test_get_current_weather(async_client, mocker):
    """Test fetching current weather data from OpenWeather."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = RAW_CURRENT_DATA
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_context = MagicMock()
    mock_client_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_context.__aexit__ = AsyncMock(return_value=None)

    mocker.patch(
        "app.services.openweather_service.httpx.AsyncClient",
        return_value=mock_client_context
    )

    response = await async_client.get("/weather/current")

    expected_parsed_data = {
        "temperature" : 20.0,
        "temperature_feels_like" : 19.5,
        "humidity" : 60,
        "wind_speed" : 5.0,
        "description" : "clear sky",
        "icon_code" : "02d",
        "icon_url": "https://openweathermap.org/img/wn/02d@2x.png"
    }

    assert response.status_code == 200
    assert response.json() == expected_parsed_data
