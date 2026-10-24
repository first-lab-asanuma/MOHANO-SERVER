from sqlalchemy import delete, text

from app.core.errors import ServiceError
from app.core.security import utc_now
from app.db.session import SessionLocal
from app.models.auth import AuthIdentity, RefreshSession
from app.models.profile import Profile
from app.models.user import User


class AccountRepository:
    """Erases account-owned records while retaining only a non-identifying deletion audit row."""

    def delete_account(self, user_id: str) -> None:
        with SessionLocal.begin() as session:
            user = session.get(User, user_id)
            if user is None or user.status != "active":
                raise ServiceError("user_unavailable", "User unavailable", 401)

            now = utc_now()
            # These are MySQL tables already present in the migration. Remove the
            # account's private activity as well, even though matching/call/chat
            # endpoints still use MockStore during the MVP.
            session.execute(text("DELETE FROM messages WHERE sender_id = :user_id"), {"user_id": user_id})
            session.execute(text("DELETE FROM conversation_members WHERE user_id = :user_id"), {"user_id": user_id})
            session.execute(
                text(
                    "DELETE FROM conversations "
                    "WHERE NOT EXISTS (SELECT 1 FROM conversation_members "
                    "WHERE conversation_members.conversation_id = conversations.id)"
                )
            )
            session.execute(text("DELETE FROM call_signals WHERE sender_id = :user_id"), {"user_id": user_id})
            session.execute(
                text("DELETE FROM call_requests WHERE requester_id = :user_id OR recipient_id = :user_id"),
                {"user_id": user_id},
            )
            session.execute(
                text("DELETE FROM match_exposures WHERE viewer_id = :user_id OR candidate_id = :user_id"),
                {"user_id": user_id},
            )
            session.execute(text("DELETE FROM match_preferences WHERE user_id = :user_id"), {"user_id": user_id})
            # Profile cascades remove its languages, interests, and photo references.
            session.execute(delete(Profile).where(Profile.user_id == user_id))
            # Removing the identity also allows the same Google account to start fresh later.
            session.execute(delete(AuthIdentity).where(AuthIdentity.user_id == user_id))
            session.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))
            user.status = "deleted"
            user.last_active_at = None
            user.call_notifications_enabled = False
            user.push_token = None
            user.deleted_at = now
