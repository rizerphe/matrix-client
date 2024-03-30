from __future__ import annotations
from dataclasses import dataclass, field
import enum
from typing import TYPE_CHECKING

from .attachment import Attachment
from .event import Event

if TYPE_CHECKING:
    from .message_edit_event import MessageEditEvent


class MessageType(enum.Enum):
    """Represents a message type."""

    TEXT = "m.text"
    NOTICE = "m.notice"
    EMOTE = "m.emote"
    IMAGE = "m.image"
    FILE = "m.file"
    AUDIO = "m.audio"
    VIDEO = "m.video"
    LOCATION = "m.location"
    UNKNOWN = None


@dataclass
class MessageEvent(Event):
    """Represents a message event."""

    content: dict = field(repr=False)
    edits: list[MessageEditEvent] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"MessageEvent(message_type={self.message_type!r}, body={self.body!r})"

    @property
    def reply_to(self) -> Event | None:
        """Return the event replied to."""
        event_id = (
            self.content.get("m.relates_to", {})
            .get("m.in_reply_to", {})
            .get("event_id")
        )
        if event_id is None:
            return None
        return self._client.get_event(event_id)

    @property
    def message_type(self) -> MessageType:
        """Return the message type."""
        return self.content.get("msgtype", MessageType.UNKNOWN)

    @property
    def body(self) -> str | None:
        """Return the body."""
        if self.content.get("msgtype") == "m.text":
            body = self.content.get("body", "")
            if self.content.get("m.relates_to", {}).get("m.in_reply_to"):
                body = "\n\n".join(body.split("\n\n")[1:])
            return body
        if self.content.get("msgtype") in ["m.notice", "m.emote"]:
            return self.content.get("body", "")
        return None

    @property
    def attachment(self) -> Attachment | None:
        """Return the attachment."""
        if self.content.get("msgtype") in ["m.image", "m.file", "m.audio", "m.video"]:
            return Attachment(self._client, self.content)
        return None

    @property
    def geo_uri(self) -> str | None:
        """Return the geo URI for location messages."""
        if self.content.get("msgtype") == "m.location":
            return self.content.get("body")
        return None

    @property
    def attachment_filename(self) -> str | None:
        """Return the image filename."""
        if self.content.get("msgtype") in ["m.image", "m.file", "m.audio", "m.video"]:
            return self.content.get("body")
        return None

    @property
    def edited(self) -> bool:
        """Return whether the message was edited.

        Use this with caution - the edits are always in the future relative
        to the event itself, so this should only be used when you need to
        know whether the message was edited. The value of this property might
        change as new edits are received, even while you're processing the event.
        """
        return bool(self.edits)

    @property
    def future_body(self) -> str | None:
        """Return the body of the message, taking edits into account.

        Use this with caution - the edits are always in the future relative
        to the event itself, so this should only be used when you need to
        know the final state of the message. The value of this property
        might change as new edits are received, even while you're processing
        the event.
        """
        if self.edited:
            return self.edits[-1].body
        return self.body
