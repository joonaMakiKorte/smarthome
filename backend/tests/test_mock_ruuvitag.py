from datetime import datetime

# pytest tests/test_mock_ruuvitag.py::test_ruuvi_websocket_stream
def test_ruuvi_websocket_stream(sync_client):
    """Test that the WebSocket accepts connections"""
    with sync_client.websocket_connect("/ruuvitag/ws") as websocket:
        # Receive packets
        data1 = websocket.receive_json()
        data2 = websocket.receive_json()
        data3 = websocket.receive_json()

        # Assert base properties
        assert "mac" in data1
        assert "temperature" in data1
        assert "humidity" in data1
        assert isinstance(data2["battery"],int)

        # Time should increase in packets
        assert data1["timestamp"] < data2["timestamp"] < data3["timestamp"]
