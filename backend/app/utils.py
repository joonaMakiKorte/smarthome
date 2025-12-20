import httpx
import logging
from contextlib import asynccontextmanager
from fastapi import HTTPException, status

logger = logging.getLogger("uvicorn.info")

@asynccontextmanager
async def handle_upstream_errors(service_name: str = "External Service"):
    """
    Context manager to catch upstream API errors and convert them 
    to standardized FastAPI HTTPExceptions.
    """
    try:
        yield
    except httpx.RequestError as e:
        # Connectivity issues (DNS, Timeout, Connection Refused)
        logger.error(f"{service_name} Connectivity Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to connect to {service_name}."
        )
    except httpx.HTTPStatusError as e:
        # 4xx or 5xx responses from the provider
        logger.error(f"{service_name} Status Error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Received error from {service_name}."
        )
    except (KeyError, IndexError, TypeError, ValueError) as e:
        # Parsing errors
        logger.error(f"{service_name} Parsing Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unexpected data format received from {service_name}."
        )
    except Exception as e:
        # Unknown internal errors
        logger.error(f"Internal Error processing {service_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred."
        )