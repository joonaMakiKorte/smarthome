from sqlmodel import SQLModel, Field
from datetime import datetime

class CompletedTask(SQLModel, table=True):
    id: str = Field(primary_key=True)
    content: str
    priority: int
    completed_at: datetime = Field(default_factory=datetime.utcnow)