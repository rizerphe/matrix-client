from __future__ import annotations
from dataclasses import dataclass, field

from .event import Event


@dataclass
class RedactionEvent(Event):
    """Represents a redaction event."""

    content: dict = field(repr=False)

    @property
    def redacts(self) -> Event | None:
        """Return the event redacted."""
        event_id = self.content.get("redacts")
        if event_id is None:
            return None
        return self._client.get_event(event_id)

    @property
    def reason(self) -> str | None:
        """Return the reason."""
        return self.content.get("reason")
