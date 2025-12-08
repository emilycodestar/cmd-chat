from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Message(BaseModel):
    message: str
    timestamp: Optional[float] = None
    sequence: Optional[int] = None
    room_id: Optional[str] = None
    username: Optional[str] = None 