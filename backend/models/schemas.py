"""
models/schemas.py
All Pydantic request/response models used across the API and agent layers.
"""
from pydantic import BaseModel
from typing import Optional, Literal


class EventState(BaseModel):
    model_config = {"extra": "forbid"}
    who: Optional[str] = None
    what: Optional[str] = None
    where: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    status: Literal["negotiating", "pending_approval", "resolved"] = "negotiating"


class SocialApprovalRequest(BaseModel):
    chat_id: str
    approved_message: str
    event_title: str
    event_start: str
    event_end: str


class SocialRejectRequest(BaseModel):
    chat_id: str
    reason: Optional[str] = None


class SocialConflictResponseRequest(BaseModel):
    """Used when the user approves sending a conflict-apology message without creating a calendar event."""
    chat_id: str
    approved_message: str


class EditMessageRequest(BaseModel):
    new_text: str
