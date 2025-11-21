from pydantic import BaseModel

class TodoTask(BaseModel):
    id: str
    content: str
    completed: bool