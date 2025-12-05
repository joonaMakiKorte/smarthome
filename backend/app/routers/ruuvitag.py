import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services import ruuvitag_service

router = APIRouter()

@router.websocket("/ruuvitag/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time sensor data.
    """
    await websocket.accept()
    service = ruuvitag_service.get_service()
    try:
        # Subscribe the websocket to the async generator
        async for data in service.stream_data(interval_seconds=0.2):
            await websocket.send_text(json.dumps(data))
    except WebSocketDisconnect:
        print("Dashboard disconnected")
    except Exception as e:
        print(f"Error: {e}")
