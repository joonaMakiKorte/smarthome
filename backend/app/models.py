from sqlmodel import SQLModel, Field
from datetime import datetime

class CompletedTask(SQLModel, table=True):
    id: str = Field(primary_key=True, description="Unique ID from Todoist")
    content: str = Field(description="The task description/title")
    priority: int = Field(
        ge=1,
        le=4,
        description="Priority level: 4 (Very Urgent) to 1 (Natural)")
    completed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC Timestamp when the task was completed",
        alias="completedAt")