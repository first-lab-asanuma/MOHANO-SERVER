from typing import Optional
from uuid import uuid4

from app.core.errors import ServiceError
from app.core.security import utc_now
from app.schemas.chats import (
    ChatListItem,
    ChatListResponse,
    ChatMessage,
    MessageCreateRequest,
    MessageListResponse,
)
from app.services.mock_store import MockStore
from app.services.profile_service import ProfileService


class ChatService:
    """REST 채팅 목록·메시지 비즈니스 로직. 현재 데이터는 프로세스 메모리에만 남는다."""

    def __init__(self, store: MockStore, profile_service: ProfileService) -> None:
        self._store = store
        self._profile_service = profile_service

    def list_chats(self, user_id: str, cursor: Optional[str]) -> ChatListResponse:
        self._ensure_demo_chat(user_id)
        with self._store.lock:
            records = [record for record in self._store.chats.values() if user_id in record["member_ids"]]
        records.sort(key=lambda record: record["messages"][-1]["created_at"], reverse=True)
        if cursor:
            records = [record for record in records if record["chat_id"] < cursor]
        page = records[:20]
        return ChatListResponse(
            items=[self._chat_list_item(user_id, record) for record in page],
            next_cursor=page[-1]["chat_id"] if len(page) == 20 else None,
        )

    def list_messages(self, user_id: str, chat_id: str, before: Optional[str]) -> MessageListResponse:
        record = self._chat_for_member(user_id, chat_id)
        messages = list(record["messages"])
        if before:
            try:
                before_index = next(index for index, message in enumerate(messages) if message["message_id"] == before)
                messages = messages[:before_index]
            except StopIteration:
                messages = []
        page = messages[-50:]
        return MessageListResponse(
            items=[self._message_response(user_id, message) for message in page],
            next_cursor=page[0]["message_id"] if len(messages) > len(page) else None,
        )

    def create_message(self, user_id: str, chat_id: str, payload: MessageCreateRequest) -> ChatMessage:
        text = payload.text.strip()
        if not text:
            raise ServiceError("message_empty", "Message cannot be empty", 422)
        record = self._chat_for_member(user_id, chat_id)
        message = {
            "message_id": str(uuid4()),
            "sender_id": user_id,
            "text": text,
            "message_type": "message",
            "created_at": utc_now(),
        }
        with self._store.lock:
            record["messages"].append(message)
        return self._message_response(user_id, message)

    def mark_read(self, user_id: str, chat_id: str) -> None:
        record = self._chat_for_member(user_id, chat_id)
        with self._store.lock:
            record["last_read_at"][user_id] = utc_now()

    def record_call_connected(self, requester_id: str, recipient_id: str) -> str:
        """Create or reuse a pair chat and append one call-history event."""
        member_ids = {requester_id, recipient_id}
        with self._store.lock:
            record = next(
                (chat for chat in self._store.chats.values() if set(chat["member_ids"]) == member_ids),
                None,
            )
            if record is None:
                chat_id = str(uuid4())
                record = {
                    "chat_id": chat_id,
                    "member_ids": [requester_id, recipient_id],
                    "messages": [],
                    "last_read_at": {requester_id: None, recipient_id: None},
                }
                self._store.chats[chat_id] = record

            record["messages"].append(
                {
                    "message_id": str(uuid4()),
                    "sender_id": "system",
                    "text": "call_connected",
                    "message_type": "call_connected",
                    "created_at": utc_now(),
                }
            )
            return record["chat_id"]

    def _ensure_demo_chat(self, user_id: str) -> None:
        chat_id = "mock-chat-" + user_id
        with self._store.lock:
            existing = self._store.chats.get(chat_id)
            if existing is not None:
                if not any(message.get("message_type") == "call_connected" for message in existing["messages"]):
                    existing["messages"].append(
                        {
                            "message_id": "mock-call-connected-" + user_id,
                            "sender_id": "system",
                            "text": "call_connected",
                            "message_type": "call_connected",
                            "created_at": utc_now(),
                        }
                    )
                return
            self._store.chats[chat_id] = {
                "chat_id": chat_id,
                "member_ids": [user_id, "mock-yuki"],
                "messages": [
                    {
                        "message_id": "mock-message-" + user_id,
                        "sender_id": "mock-yuki",
                        "text": "Hi! How is your day going?",
                        "message_type": "message",
                        "created_at": utc_now(),
                    },
                    {
                        "message_id": "mock-call-connected-" + user_id,
                        "sender_id": "system",
                        "text": "call_connected",
                        "message_type": "call_connected",
                        "created_at": utc_now(),
                    },
                ],
                "last_read_at": {user_id: None},
            }

    def _chat_for_member(self, user_id: str, chat_id: str) -> dict:
        with self._store.lock:
            record = self._store.chats.get(chat_id)
            if record is None:
                raise ServiceError("chat_not_found", "Chat not found", 404)
            if user_id not in record["member_ids"]:
                raise ServiceError("chat_forbidden", "You cannot access this chat", 403)
            return record

    def _chat_list_item(self, user_id: str, record: dict) -> ChatListItem:
        peer_id = next(member_id for member_id in record["member_ids"] if member_id != user_id)
        last_message = record["messages"][-1] if record["messages"] else None
        last_read_at = record["last_read_at"].get(user_id)
        unread_count = sum(
            1
            for message in record["messages"]
            if message["sender_id"] not in (user_id, "system")
            and (last_read_at is None or message["created_at"] > last_read_at)
        )
        return ChatListItem(
            chat_id=record["chat_id"],
            counterpart=self._profile_service.get_public_profile(peer_id),
            last_message=last_message["text"] if last_message else None,
            last_message_at=last_message["created_at"] if last_message else None,
            unread_count=unread_count,
            last_message_type=last_message.get("message_type", "message") if last_message else "message",
        )

    @staticmethod
    def _message_response(user_id: str, message: dict) -> ChatMessage:
        return ChatMessage(
            message_id=message["message_id"],
            sender_id=message["sender_id"],
            text=message["text"],
            created_at=message["created_at"],
            is_mine=message["sender_id"] == user_id,
            message_type=message.get("message_type", "message"),
        )
