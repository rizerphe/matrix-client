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

    @property
    def non_matrix_url(self) -> str | None:
        """Return the non-matrix URL."""
        if self.url is None:
            return None
        server, media_id = self.url[6:].split("/")
        return f"{self._client.homeserver_url}/_matrix/media/v3/download/{server}/{media_id}"

    @property
    def non_matrix_thumbnail_url(self) -> str | None:
        """Return the non-matrix thumbnail URL."""
        if self.thumbnail_url is None:
            return None
        server, media_id = self.thumbnail_url[6:].split("/")
        return f"{self._client.homeserver_url}/_matrix/media/v3/download/{server}/{media_id}"

    async def download(self) -> bytes | None:
        """Download the attachment."""
        if self.url is None:
            return None
        return await self._client._download_mxc(self.url)
