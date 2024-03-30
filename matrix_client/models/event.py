from __future__ import annotations
from dataclasses import dataclass, field
import datetime
from typing import TYPE_CHECKING

from .base import Base
from .room import Room
from .user import User

if TYPE_CHECKING:
    from .redaction_event import RedactionEvent


@dataclass
class Event(Base):
    """Represents an event."""

    type: str
    raw: dict = field(repr=False)
    _sender: str = field(repr=False)
    _room: str = field(repr=False)
    _age: int = field(repr=False)
    event_id: str = field(repr=False)
    redacted: RedactionEvent | None = field(repr=False)

    @property
    def room(self) -> Room | None:
        """Return the room."""
        return self._client.get_room(self._room)

    async def sender(self) -> User:
        """Return the sender."""
        sender = await self._client.get_user(self._sender)
        if sender is None:
            raise ValueError("Could not find sender.")
        return sender

    @property
    def age(self) -> datetime.timedelta:
        """Return the age."""
        return datetime.timedelta(milliseconds=self._age)

    async def redact(self, reason: str | None = None) -> None:
        """Redact the event."""
        await self._client.send_redaction(self._room, self.event_id, reason)

    async def reply(self, content: str) -> None:
        """Reply to the event."""
        await self._client.send_text_message(
            self._room, content, reply_to=self.event_id
        )
