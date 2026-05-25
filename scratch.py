from typing import Optional
from pydantic import BaseModel

class SocialRejectRequest(BaseModel):
    chat_id: str
    reason: Optional[str] = None
