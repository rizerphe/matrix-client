from __future__ import annotations
from dataclasses import dataclass, field

from .event import Event
from .message_event import MessageEvent


@dataclass
class MessageEditEvent(Event):
    """Represents a message event."""

    content: dict = field(repr=False)

    @property
    def original(self) -> MessageEvent | None:
        """Return the original message."""
        event_id = self.content.get("m.relates_to", {}).get("event_id")
        if event_id is None:
            return None
        event = self._client.get_event(event_id)
        if not isinstance(event, MessageEvent):
            return None
        return event

    @property
    def body(self) -> str:
        """Return the body."""
        if self.content.get("m.new_content", {}).get("msgtype") == "m.text":
            return self.content.get("m.new_content", {}).get("body", "")
        raise ValueError("Event is not a text message.")
