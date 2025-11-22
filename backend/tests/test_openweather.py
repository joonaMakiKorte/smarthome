import pytest
import json
from app.services import openweather_service
from app.schemas import GeoLocation
from app.config import AppConfig, LocationConfig

@pytest.mark.asyncio
async def test_get_coordinates_uses_cache(mocker):
    """Test returning cached coordinates."""
    mock_config = AppConfig(
        location=LocationConfig(lat=60.1, lon=24.9, city="Helsinki", country="FI")
    )
    mocker.patch("app.services.openweather_service.load_config", return_value=mock_config)

    mock_api = mocker.patch("app.services.geocoding_service.get_geolocation")

    lat, lon = await openweather_service.get_coordinates()

    assert lat == 60.1
    assert lon == 24.9
    mock_api.assert_not_called()

@pytest.mark.asyncio
async def test_get_coordinates_fetches_and_updates(mocker):
    """Test fetching coordinates when not cached and updating config."""
    mocker.patch("app.services.openweather_service.load_config", return_value=AppConfig())

    mock_geo_data = GeoLocation(name="Helsinki", lat=60.1, lon=24.9, country="FI")
    mock_api = mocker.patch(
        "app.services.geocoding_service.get_geolocation",
        return_value=mock_geo_data,
    )

    mock_save = mocker.patch("app.services.openweather_service.update_location")

    lat, lon = await openweather_service.get_coordinates()

    assert lat == 60.1
    assert lon == 24.9
    mock_api.assert_called_once()
    mock_save.assert_called_once_with(60.1, 24.9, "Helsinki", "FI")
