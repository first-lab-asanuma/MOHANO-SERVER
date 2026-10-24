from app.repositories.account_repository import AccountRepository
from app.services.object_storage_service import ObjectStorageService


class AccountService:
    """Coordinates irreversible customer-data removal across storage and MySQL."""

    def __init__(self, repository: AccountRepository, storage: ObjectStorageService) -> None:
        self._repository = repository
        self._storage = storage

    def delete_account(self, user_id: str) -> None:
        # Storage comes first: if it is unavailable, retain database data so deletion can be retried.
        self._storage.delete_user_objects(user_id)
        self._repository.delete_account(user_id)
