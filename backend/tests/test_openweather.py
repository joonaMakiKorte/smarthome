import pytest
from app.services.openweather_service import hourly_cache

@pytest.fixture(autouse=True)
def reset_hourly_cache():
    """Automatically runs before every test to clear the global singleton cache."""
    hourly_cache.data = None
    hourly_cache.expiry = None
    yield

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
async def test_get_hourly_weather(async_client, mock_httpx_client):
    """Test fetching hourly weather."""
    mock_client = mock_httpx_client(
        patch_target="app.services.openweather_service.httpx.AsyncClient",
        response_data=RAW_HOURLY_DATA
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
    mock_client.get.assert_called_once()

# pytest tests/test_openweather.py::test_get_current_weather
@pytest.mark.asyncio
async def test_get_current_weather(async_client, mock_httpx_client):
    """Test fetching current weather data from OpenWeather."""
    mock_client = mock_httpx_client(
        patch_target="app.services.openweather_service.httpx.AsyncClient",
        response_data=RAW_CURRENT_DATA
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
    mock_client.get.assert_called_once()
