from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client


@dataclass
class Base:
    """A base class for matrix objects."""

    _client: Client = field(repr=False)
