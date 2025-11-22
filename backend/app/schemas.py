from pydantic import BaseModel

class TodoTask(BaseModel):
    """Schema for an active todo task."""
    id: str
    content: str
    priority: int # (4=highest, 1=lowest)

class GeoLocation(BaseModel):
    """Schema for geolocation data."""
    name: str
    lat: float
    lon: float
    country: str
