from pydantic import BaseModel, Field


class AvailabilityResponse(BaseModel):
    is_online: bool
    call_notifications_enabled: bool
    has_push_token: bool


class AvailabilityUpdateRequest(BaseModel):
    call_notifications_enabled: bool
    push_token: str | None = Field(default=None, max_length=4096)
