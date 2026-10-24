from datetime import timedelta
from typing import Optional
from uuid import uuid4

from app.core.errors import ServiceError
from app.core.security import utc_now
from app.repositories.availability_repository import AvailabilityRepository
from app.schemas.calls import (
    CallRequestCreateRequest,
    CallRequestListResponse,
    CallRequestResponse,
    CallSessionResponse,
    CallSignal,
    SignalCreateRequest,
    SignalListResponse,
)
from app.services.mock_store import MockStore
from app.services.profile_service import ProfileService
from app.services.chat_service import ChatService


class CallService:
    """통화 신청과 P2P signaling 제어만 담당한다. 음성 데이터는 다루지 않는다."""

    def __init__(
        self,
        store: MockStore,
        profile_service: ProfileService,
        chat_service: ChatService,
        availability_repository: AvailabilityRepository,
    ) -> None:
        self._store = store
        self._profile_service = profile_service
        self._chat_service = chat_service
        self._availability_repository = availability_repository

    def create_request(self, user_id: str, payload: CallRequestCreateRequest) -> CallRequestResponse:
        if payload.candidate_id == user_id:
            raise ServiceError("candidate_not_found", "Candidate not found", 404)
        try:
            self._profile_service.get_public_profile(payload.candidate_id)
        except ServiceError as error:
            raise ServiceError("candidate_not_found", "Candidate not found", 404) from error
        if not self._availability_repository.is_contactable(payload.candidate_id):
            raise ServiceError("candidate_unavailable", "This person is not available right now.", 409)
        with self._store.lock:
            request_id = str(uuid4())
            record = {
                "request_id": request_id,
                "requester_id": user_id,
                "recipient_id": payload.candidate_id,
                "status": "pending",
                "created_at": utc_now(),
                "call_session_id": None,
            }
            self._store.call_requests[request_id] = record
        return self._request_response(user_id, record)

    def list_inbox(self, user_id: str, cursor: Optional[str]) -> CallRequestListResponse:
        with self._store.lock:
            records = [record for record in self._store.call_requests.values() if record["recipient_id"] == user_id]
        records.sort(key=lambda record: record["created_at"], reverse=True)
        if cursor:
            records = [record for record in records if record["request_id"] < cursor]
        page = records[:20]
        return CallRequestListResponse(
            items=[self._request_response(user_id, record) for record in page],
            next_cursor=page[-1]["request_id"] if len(page) == 20 else None,
        )

    def get_request(self, user_id: str, request_id: str) -> CallRequestResponse:
        record = self._request_for_participant(user_id, request_id)
        return self._request_response(user_id, record)

    def accept_request(self, user_id: str, request_id: str) -> CallRequestResponse:
        with self._store.lock:
            record = self._request_for_participant(user_id, request_id)
            if record["recipient_id"] != user_id:
                raise ServiceError("call_request_forbidden", "Only the recipient can accept this request", 403)
            if record["status"] != "pending":
                raise ServiceError("call_request_not_pending", "Call request is no longer pending", 409)
            session_id = str(uuid4())
            self._store.call_sessions[session_id] = {
                "session_id": session_id,
                "participant_ids": [record["requester_id"], record["recipient_id"]],
                "status": "connecting",
                "expires_at": utc_now() + timedelta(minutes=10),
                "ended_at": None,
                "signals": [],
            }
            record["status"] = "accepted"
            record["call_session_id"] = session_id
            self._chat_service.record_call_connected(record["requester_id"], record["recipient_id"])
        return self._request_response(user_id, record)

    def reject_request(self, user_id: str, request_id: str) -> CallRequestResponse:
        return self._close_request(user_id, request_id, "rejected", "recipient_id")

    def cancel_request(self, user_id: str, request_id: str) -> CallRequestResponse:
        return self._close_request(user_id, request_id, "cancelled", "requester_id")

    def get_session(self, user_id: str, session_id: str) -> CallSessionResponse:
        with self._store.lock:
            session = self._session_for_participant(user_id, session_id)
            self._expire_session_if_needed(session)
            return self._session_response(user_id, session)

    def add_signal(self, user_id: str, session_id: str, payload: SignalCreateRequest) -> CallSignal:
        with self._store.lock:
            session = self._session_for_participant(user_id, session_id)
            self._expire_session_if_needed(session)
            if session["status"] != "connecting":
                raise ServiceError("call_session_closed", "Call session is no longer active", 409)
            signal = {
                "signal_id": str(uuid4()),
                "sender_id": user_id,
                "signal_type": payload.signal_type,
                "payload": payload.payload,
                "created_at": utc_now(),
                "expires_at": utc_now() + timedelta(minutes=10),
            }
            session["signals"].append(signal)
            return CallSignal(**signal)

    def list_signals(self, user_id: str, session_id: str, after: Optional[str]) -> SignalListResponse:
        with self._store.lock:
            session = self._session_for_participant(user_id, session_id)
            self._expire_session_if_needed(session)
            signals = [signal for signal in session["signals"] if signal["sender_id"] != user_id]
            if after:
                try:
                    after_index = next(index for index, signal in enumerate(signals) if signal["signal_id"] == after)
                    signals = signals[after_index + 1 :]
                except StopIteration:
                    signals = []
            return SignalListResponse(
                items=[CallSignal(**signal) for signal in signals],
                next_cursor=signals[-1]["signal_id"] if signals else after,
            )

    def end_session(self, user_id: str, session_id: str) -> CallSessionResponse:
        with self._store.lock:
            session = self._session_for_participant(user_id, session_id)
            if session["status"] == "connecting":
                session["status"] = "ended"
                session["ended_at"] = utc_now()
            return self._session_response(user_id, session)

    def _close_request(self, user_id: str, request_id: str, status: str, permitted_field: str) -> CallRequestResponse:
        with self._store.lock:
            record = self._request_for_participant(user_id, request_id)
            if record[permitted_field] != user_id:
                raise ServiceError("call_request_forbidden", "You cannot update this call request", 403)
            if record["status"] != "pending":
                raise ServiceError("call_request_not_pending", "Call request is no longer pending", 409)
            record["status"] = status
        return self._request_response(user_id, record)

    def _request_for_participant(self, user_id: str, request_id: str) -> dict:
        record = self._store.call_requests.get(request_id)
        if record is None:
            raise ServiceError("call_request_not_found", "Call request not found", 404)
        if user_id not in (record["requester_id"], record["recipient_id"]):
            raise ServiceError("call_request_forbidden", "You cannot access this call request", 403)
        return record

    def _session_for_participant(self, user_id: str, session_id: str) -> dict:
        session = self._store.call_sessions.get(session_id)
        if session is None:
            raise ServiceError("call_session_not_found", "Call session not found", 404)
        if user_id not in session["participant_ids"]:
            raise ServiceError("call_session_forbidden", "You cannot access this call session", 403)
        return session

    def _request_response(self, user_id: str, record: dict) -> CallRequestResponse:
        counterpart_id = record["recipient_id"] if record["requester_id"] == user_id else record["requester_id"]
        return CallRequestResponse(
            request_id=record["request_id"],
            direction="outgoing" if record["requester_id"] == user_id else "incoming",
            status=record["status"],
            counterpart=self._profile_service.get_public_profile(counterpart_id),
            created_at=record["created_at"],
            call_session_id=record["call_session_id"],
        )

    def _session_response(self, user_id: str, session: dict) -> CallSessionResponse:
        peer_id = next(participant_id for participant_id in session["participant_ids"] if participant_id != user_id)
        return CallSessionResponse(
            session_id=session["session_id"],
            status=session["status"],
            peer=self._profile_service.get_public_profile(peer_id),
            expires_at=session["expires_at"],
            ended_at=session["ended_at"],
        )

    @staticmethod
    def _expire_session_if_needed(session: dict) -> None:
        if session["status"] == "connecting" and session["expires_at"] <= utc_now():
            session["status"] = "expired"
