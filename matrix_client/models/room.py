from __future__ import annotations
from dataclasses import dataclass, field
from typing import AsyncIterable, TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .user import User


@dataclass
class RoomMember(Base):
    """Represents a room member."""

    user_id: str
    displayname: str | None
    membership: str | None

    async def user(self) -> User | None:
        """Get the user."""
        return await self._client.get_user(self.user_id)


@dataclass
class Room(Base):
    """Represents a room."""

    room_id: str
    state: dict = field(repr=False)

    @property
    def name(self) -> str | None:
        """Return the name of the room."""
        for event in reversed(self.state.get("events", [])):
            if event.get("type") == "m.room.name":
                return event.get("content", {}).get("name")
        return None

    @property
    def members(self) -> list[RoomMember]:
        """Return the members of the room."""
        members: dict[str, RoomMember] = {}
        for event in self.state.get("events", []):
            if event.get("type") != "m.room.member":
                continue
            if "state_key" not in event:
                continue
            member = RoomMember(
                self._client,
                user_id=event.get("state_key"),
                displayname=event.get("content", {}).get("displayname"),
                membership=event.get("content", {}).get("membership"),
            )
            members[member.user_id] = member
        return list(members.values())

    async def aliases(self) -> list[str]:
        """Return the aliases of the room."""
        room = await self._client._request(
            "GET", f"_matrix/client/v3/rooms/{self.room_id}/aliases"
        )
        return room.get("aliases", [])

    async def messages(self) -> AsyncIterable[dict]:
        """Return the messages of the room."""
        messages = await self._client._request(
            "GET", f"_matrix/client/v3/rooms/{self.room_id}/messages"
        )
        while messages:
            for message in messages["chunk"]:
                yield message
            if not messages.get("end"):
                break
            messages = await self._client._request(
                "GET",
                f"_matrix/client/v3/rooms/{self.room_id}/messages",
                params={"from": messages["end"]},
            )

    async def send_text_message(self, content: str) -> None:
        """Send a text message to the room."""
        await self._client.send_text_message(self.room_id, content)
