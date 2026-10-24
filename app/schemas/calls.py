from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.profile import PublicProfile


class CallRequestCreateRequest(BaseModel):
    candidate_id: str = Field(min_length=1)


class CallRequestResponse(BaseModel):
    request_id: str
    direction: Literal["outgoing", "incoming"]
    status: Literal["pending", "accepted", "rejected", "cancelled", "expired"]
    counterpart: PublicProfile
    created_at: datetime
    call_session_id: Optional[str] = None


class CallRequestListResponse(BaseModel):
    items: List[CallRequestResponse]
    next_cursor: Optional[str] = None


class CallSessionResponse(BaseModel):
    session_id: str
    status: Literal["connecting", "ended", "expired"]
    peer: PublicProfile
    expires_at: datetime
    ended_at: Optional[datetime] = None


class SignalCreateRequest(BaseModel):
    signal_type: Literal["offer", "answer", "ice"]
    payload: Dict[str, Any]


class CallSignal(BaseModel):
    signal_id: str
    sender_id: str
    signal_type: Literal["offer", "answer", "ice"]
    payload: Dict[str, Any]
    created_at: datetime
    expires_at: datetime


class SignalListResponse(BaseModel):
    items: List[CallSignal]
    next_cursor: Optional[str] = None
