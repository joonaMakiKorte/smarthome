import pytest
from typing import List

# pytest tests/test_openweather_integration.py::test_get_real_hourly_weather
@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_real_hourly_weather(async_client):
    """
    Test fetching real hourly weather data from OpenWeather API via the /weather/hourly endpoint.
    """
    response = await async_client.get("/weather/hourly")

    assert response.status_code == 200
    weather_data = response.json()

    assert isinstance(weather_data, List)
    assert len(weather_data) == 24, "No 24 hour weather data returned"

    first_entry = weather_data[0]
    assert "timestamp" in first_entry
    assert "temperature" in first_entry
    assert "icon_code" in first_entry
    assert "icon_url" in first_entry

# pytest tests/test_openweather_integration.py::test_get_real_current_weather
@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_real_current_weather(async_client):
    """
    Test fetching real current weather data from OpenWeather API via the /weather/current endpoint.
    """
    response = await async_client.get("/weather/current")

    assert response.status_code == 200
    current_weather = response.json()

    assert "temperature" in current_weather
    assert "temperature_feels_like" in current_weather
    assert "humidity" in current_weather
    assert "wind_speed" in current_weather
    assert "description" in current_weather
    assert "icon_code" in current_weather
    assert "icon_url" in current_weather