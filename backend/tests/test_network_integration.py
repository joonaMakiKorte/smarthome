import pytest
from app.schemas import NetworkHealth

# pytest tests/test_network_integration.py::test_get_network_health_real_data
@pytest.mark.asyncio
async def test_get_network_health_real_data(async_client):
    """Test fetching real network health data"""
    response = await async_client.get("/network/health")

    assert response.status_code == 200
    
    data = response.json()

    if data["wan_latency_ms"] is not None:
        assert isinstance(data["wan_latency_ms"], float)
        assert data["wan_latency_ms"] >= 0
        
    if data["packet_loss"] is not None:
        assert 0 <= data["packet_loss"] <= 100
        
    assert data["server_upload_mbps"] >= 0.0
    assert data["server_download_mbps"] >= 0.0
