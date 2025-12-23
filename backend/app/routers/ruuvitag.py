import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services import ruuvitag_service

router = APIRouter()

info_logger = logging.getLogger("uvicorn.info")
error_logger = logging.getLogger("uvicorn.error")

@router.websocket("/ruuvitag/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time sensor data.
    """
    await websocket.accept()
    service = ruuvitag_service.get_sensor_service()
    try:
        info_logger.info("RuuviTag WebSocket connected.")
        while True:
            data = service.latest_data     
            if data:
                await websocket.send_text(data.model_dump_json())
            
            # Wait 1 second for rate limiting
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        info_logger.info("RuuviTag WebSocket disconnected.")
    except Exception as e:
        error_logger.error(f"RuuviTag Error: {e}")
