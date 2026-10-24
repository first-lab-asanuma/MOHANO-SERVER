from threading import RLock
from typing import Any, Dict, Set


class MockStore:
    """개발용 프로세스 메모리 저장소.

    FastAPI 재시작 시 모두 사라진다. router는 이 객체에 직접 접근하지 않고 서비스만 사용한다.
    """

    def __init__(self) -> None:
        self.lock = RLock()
        self.user_ids: Set[str] = set()
        self.refresh_sessions: Dict[str, Dict[str, Any]] = {}
        self.profiles: Dict[str, Any] = {}
        self.candidate_ids: Set[str] = set()
        self.match_preferences: Dict[str, Any] = {}
        self.call_requests: Dict[str, Dict[str, Any]] = {}
        self.call_sessions: Dict[str, Dict[str, Any]] = {}
        self.chats: Dict[str, Dict[str, Any]] = {}
