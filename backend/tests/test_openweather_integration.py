import pytest
from typing import List
from app.schemas import HourlyWeather

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
    assert "iconCode" in first_entry
    assert "iconUrl" in first_entry

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
    assert "temperatureFeelsLike" in current_weather
    assert "humidity" in current_weather
    assert "windSpeed" in current_weather
    assert "description" in current_weather
    assert "iconCode" in current_weather
    assert "iconUrl" in current_weather