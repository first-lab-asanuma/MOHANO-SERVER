from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.profile import PublicProfile


class ChatMessage(BaseModel):
    message_id: str
    sender_id: str
    text: str
    created_at: datetime
    is_mine: bool
    message_type: Literal["message", "call_connected"] = "message"


class ChatListItem(BaseModel):
    chat_id: str
    counterpart: PublicProfile
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int
    last_message_type: Literal["message", "call_connected"] = "message"


class ChatListResponse(BaseModel):
    items: List[ChatListItem]
    next_cursor: Optional[str] = None


class MessageListResponse(BaseModel):
    items: List[ChatMessage]
    next_cursor: Optional[str] = None


class MessageCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
