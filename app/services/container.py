"""프로세스 수명 동안 공유되는 개발용 서비스 조립 지점."""

from app.repositories.auth_repository import AuthRepository
from app.repositories.account_repository import AccountRepository
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.matching_repository import MatchingRepository
from app.core.config import get_settings
from app.services.auth_service import AuthService
from app.services.account_service import AccountService
from app.services.call_service import CallService
from app.services.chat_service import ChatService
from app.services.database_profile_service import DatabaseProfileService
from app.services.google_identity_verifier import GoogleIdentityVerifier
from app.services.matching_service import MatchingService
from app.services.mock_store import MockStore
from app.services.object_storage_service import ObjectStorageService

mock_store = MockStore()
profile_service = DatabaseProfileService(
    ProfileRepository(),
    ObjectStorageService(get_settings()),
    seed_candidates=get_settings().environment == "local",
)
auth_service = AuthService(AuthRepository(), GoogleIdentityVerifier())
account_service = AccountService(AccountRepository(), ObjectStorageService(get_settings()))
availability_repository = AvailabilityRepository()
matching_service = MatchingService(
    MatchingRepository(),
    profile_service,
    get_settings().jwt_secret_key,
)
chat_service = ChatService(mock_store, profile_service)
call_service = CallService(mock_store, profile_service, chat_service, availability_repository)


def get_auth_service() -> AuthService:
    return auth_service


def get_account_service() -> AccountService:
    return account_service


def get_availability_repository() -> AvailabilityRepository:
    return availability_repository


def get_profile_service() -> DatabaseProfileService:
    return profile_service


def get_matching_service() -> MatchingService:
    return matching_service


def get_call_service() -> CallService:
    return call_service


def get_chat_service() -> ChatService:
    return chat_service
