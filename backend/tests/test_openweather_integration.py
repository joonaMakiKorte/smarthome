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
    assert "icon_code" in first_entry
    assert "icon_url" in first_entry