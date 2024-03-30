from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client


@dataclass
class Attachment:
    """Represents an attachment."""

    _client: Client = field(repr=False)
    content: dict = field(repr=False)

    @property
    def url(self) -> str | None:
        """Return the URL."""
        return self.content.get("url")

    @property
    def filename(self) -> str | None:
        """Return the filename."""
        return self.content.get("body")

    @property
    def mimetype(self) -> str | None:
        """Return the mimetype."""
        return self.content.get("info", {}).get("mimetype")

    @property
    def size(self) -> int | None:
        """Return the size."""
        return self.content.get("info", {}).get("size")

    @property
    def thumbnail_url(self) -> str | None:
        """Return the thumbnail URL."""
        return self.content.get("info", {}).get("thumbnail_url")

    async def download(self) -> bytes | None:
        """Download the attachment."""
        if self.url is None:
            return None
        return await self._client._download_mxc(self.url)
