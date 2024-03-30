from dataclasses import dataclass

from .base import Base
from .user import User


@dataclass
class Myself(Base):
    """Represents the authenticated user."""

    user_id: str | None
    device_id: str | None

    async def user(self) -> User | None:
        """Return the user."""
        if self.user_id is None:
            return None
        return await self._client.get_user(self.user_id)
