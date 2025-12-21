import pytest
from unittest.mock import patch, AsyncMock
from app.schemas import NetworkHealth
from app.services.network_service import health_cache

@pytest.fixture
def mock_health_data():
    return NetworkHealth(
        wan_latency_ms=25.5,
        lan_latency_ms=2.1,
        packet_loss=0.0,
        server_upload_mbps=10.5,
        server_download_mbps=50.2,
        connected=True,
        ssid="TestWiFi",
        signal_quality=85
    )

@pytest.fixture(autouse=True)
def reset_task_cache():
    """Automatically runs before every test to clear the global singleton cache."""
    health_cache._cache = []
    health_cache._last_updated = None
    yield

# pytest tests/test_network.py::test_get_network_health
@pytest.mark.asyncio
async def test_get_network_health(async_client, mock_health_data):
    """Test successfull health fetch"""
    with patch("app.services.network_service.get_network_status", new_callable=AsyncMock) as mock_service:
        mock_service.return_value = mock_health_data

        response = await async_client.get("/network")

        assert response.status_code == 200
        data = response.json()
        
        assert data["ssid"] == "TestWiFi"
        assert data["wan_latency_ms"] == 25.5
        assert data["packet_loss"] == 0.0
        
        mock_service.assert_called_once()
        