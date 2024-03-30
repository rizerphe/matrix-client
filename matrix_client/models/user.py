from dataclasses import dataclass, field

from .base import Base


@dataclass
class User(Base):
    """A matrix user."""

    user_id: str
    avatar_url: str | None = field(repr=False)
    displayname: str | None = field(repr=False)
