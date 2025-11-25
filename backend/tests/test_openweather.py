import pytest

@pytest.mark.asyncio
async def test_get_hourly_weather(async_client, mocker):
    """Test fetching hourly weather data from OpenWeather."""
    mock_data = [
        {
            "timestamp": 10,
            "temperature": 15.5,
            "iconCode": "01d",
            "iconUrl": "https://"
        }]
    mock_get_weather_data = mocker.patch(
        "app.services.openweather_service.get_hourly_weather_data"
    )
    mock_get_weather_data.return_value = mock_data

    response = await async_client.get("/weather/hourly")

    assert response.status_code == 200
    assert response.json() == mock_data
    mock_get_weather_data.assert_called_once()

@pytest.mark.asyncio
async def test_get_current_weather(async_client, mocker):
    """Test fetching current weather data from OpenWeather."""
    mock_data = {
        "temperature": 20.0,
        "temperatureFeelsLike": 19.5,
        "humidity": 60,
        "windSpeed": 5.0,
        "description": "clear sky",
        "iconCode": "02d",
        "iconUrl": "https://"
    }
    mock_get_current_weather_data = mocker.patch(
        "app.services.openweather_service.get_current_weather_data"
    )
    mock_get_current_weather_data.return_value = mock_data

    response = await async_client.get("/weather/current")

    assert response.status_code == 200
    assert response.json() == mock_data
    mock_get_current_weather_data.assert_called_once()