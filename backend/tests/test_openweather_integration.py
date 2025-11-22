import pytest
import json
from app.services import openweather_service
from app.schemas import GeoLocation
from app.config import AppConfig, LocationConfig

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_coordinates_integration(monkeypatch, tmp_path):
    """Integration test for getting coordinates from OpenWeather API."""
    temp_config_path = tmp_path / "config.json"
    monkeypatch.setattr("app.config.CONFIG_PATH", temp_config_path)

    lat, lon = await openweather_service.get_coordinates()

    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert 59 < lat < 70 # Roughly between southern and northern Finland
    assert 20 < lon < 32 # Roughly between western and eastern Finland

    assert temp_config_path.exists()

    with open(temp_config_path, "r") as f:
        saved_data = json.load(f)
        assert "location" in saved_data
        assert saved_data["location"]["lat"] == lat
        assert saved_data["location"]["city"] is not None
