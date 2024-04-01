from __future__ import annotations
from dataclasses import dataclass, field

from .base import Base


@dataclass
class User(Base):
    """A matrix user."""

    user_id: str
    avatar_url: str | None = field(repr=False)
    displayname: str | None = field(repr=False)

    @property
    def nonmatrix_avatar_url(self) -> str | None:
        """The avatar URL outside of mxc://."""
        if not self.avatar_url:
            return None
        server, media_id = self.avatar_url[6:].split("/")
        return f"{self._client.homeserver_url}/_matrix/media/v3/thumbnail/{server}/{media_id}?width=64&height=64"
