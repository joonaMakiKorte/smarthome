import logging
from fastapi import APIRouter, HTTPException
from app.services import network_service
from app.schemas import NetworkHealth

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

@router.get("/network/health", response_model=NetworkHealth)
async def get_network_health():
    """Get current network health."""
    try:
        return await network_service.get_network_status()
    except Exception as e:
        logger.error(f"Network Health API Error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Network monitoring service is currently unavailable"
        )
    