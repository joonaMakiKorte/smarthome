from pydantic import BaseModel

class TodoTask(BaseModel):
    id: str
    content: str
    priority: int # (4=highest, 1=lowest)