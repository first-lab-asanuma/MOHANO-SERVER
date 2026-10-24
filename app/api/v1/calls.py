from typing import Optional

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.schemas.calls import (
    CallRequestCreateRequest,
    CallRequestListResponse,
    CallRequestResponse,
    CallSessionResponse,
    CallSignal,
    SignalCreateRequest,
    SignalListResponse,
)
from app.services.call_service import CallService
from app.services.container import get_call_service

router = APIRouter()


@router.post("/call-requests", response_model=CallRequestResponse)
def create_call_request(
    payload: CallRequestCreateRequest,
    user_id: str = Depends(get_current_user_id),
    service: CallService = Depends(get_call_service),
) -> CallRequestResponse:
    return service.create_request(user_id, payload)


@router.get("/call-requests/inbox", response_model=CallRequestListResponse)
def list_call_request_inbox(
    cursor: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    service: CallService = Depends(get_call_service),
) -> CallRequestListResponse:
    return service.list_inbox(user_id, cursor)


@router.get("/call-requests/{request_id}", response_model=CallRequestResponse)
def get_call_request(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CallService = Depends(get_call_service),
) -> CallRequestResponse:
    return service.get_request(user_id, request_id)


@router.post("/call-requests/{request_id}/accept", response_model=CallRequestResponse)
def accept_call_request(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CallService = Depends(get_call_service),
) -> CallRequestResponse:
    return service.accept_request(user_id, request_id)


@router.post("/call-requests/{request_id}/reject", response_model=CallRequestResponse)
def reject_call_request(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CallService = Depends(get_call_service),
) -> CallRequestResponse:
    return service.reject_request(user_id, request_id)


@router.post("/call-requests/{request_id}/cancel", response_model=CallRequestResponse)
def cancel_call_request(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CallService = Depends(get_call_service),
) -> CallRequestResponse:
    return service.cancel_request(user_id, request_id)


@router.get("/call-sessions/{session_id}", response_model=CallSessionResponse)
def get_call_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CallService = Depends(get_call_service),
) -> CallSessionResponse:
    return service.get_session(user_id, session_id)


@router.post("/call-sessions/{session_id}/signals", response_model=CallSignal)
def add_call_signal(
    session_id: str,
    payload: SignalCreateRequest,
    user_id: str = Depends(get_current_user_id),
    service: CallService = Depends(get_call_service),
) -> CallSignal:
    return service.add_signal(user_id, session_id, payload)


@router.get("/call-sessions/{session_id}/signals", response_model=SignalListResponse)
def list_call_signals(
    session_id: str,
    after: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    service: CallService = Depends(get_call_service),
) -> SignalListResponse:
    return service.list_signals(user_id, session_id, after)


@router.post("/call-sessions/{session_id}/end", response_model=CallSessionResponse)
def end_call_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CallService = Depends(get_call_service),
) -> CallSessionResponse:
    return service.end_session(user_id, session_id)
