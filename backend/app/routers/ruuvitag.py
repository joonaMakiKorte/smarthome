import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services import ruuvitag_service

router = APIRouter()

@router.websocket("/ruuvitag/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time sensor data.
    """
    await websocket.accept()
    service = ruuvitag_service.get_sensor_service()
    try:
        print("RuuviTag connected")
        # Subscribe the websocket to the async generator
        async for data in service.stream_data(interval=0.2):
            await websocket.send_text(data.model_dump_json())
    except WebSocketDisconnect:
        print("RuuviTag disconnected")
    except Exception as e:
        print(f"RuuviTag Error: {e}")
