"""MediaStore interface.

Self-hosted deployments store files on the filesystem, while cloud deployments
use object storage. The application core knows neither implementation.

Two rules apply to every implementation:

- A storage key is NEVER derived from a user-provided filename. A filename
  from a request may contain path components.
- Media is not public. Reads happen through an authorized route or a
  short-lived signed URL.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import BinaryIO, Protocol
from uuid import UUID


class ByteSource(Protocol):
    """The minimal surface required for storage.

    Deliberately not `BinaryIO`: that protocol requires many methods while
    this boundary uses only one. A caller wrapping a bounded or counting
    stream would otherwise need to emulate a full file interface or cast it,
    and such a cast here would incorrectly claim the boundary does not matter.
    """

    def read(self, size: int = -1, /) -> bytes: ...


@dataclass(frozen=True)
class StoredObject:
    storage_key: str
    size: int
    content_type: str


def build_storage_key(space_id: UUID, attachment_id: UUID, variant: str = "original") -> str:
    """Build the storage location.

        spaces/{spaceUuid}/attachments/{attachmentUuid}/original

    The path is derived exclusively from UUIDs. The original filename remains
    metadata and never becomes part of the path.
    """
    if "/" in variant or ".." in variant:
        raise ValueError("Invalid variant.")
    return f"spaces/{space_id}/attachments/{attachment_id}/{variant}"


class MediaStore(ABC):
    """Storage interface for attachments."""

    @abstractmethod
    def put(self, storage_key: str, data: ByteSource, content_type: str) -> StoredObject:
        """Store a byte stream."""

    @abstractmethod
    def open(self, storage_key: str) -> BinaryIO:
        """Open an object for reading."""

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        """Delete an object. An already missing object is not an error."""

    @abstractmethod
    def exists(self, storage_key: str) -> bool: ...

    @abstractmethod
    def create_read_url(self, storage_key: str, expires_in: timedelta) -> str | None:
        """Create a short-lived read URL when the backend supports one.

        Return None otherwise, in which case the application must serve the
        content itself. A filesystem cannot create signed URLs.
        """
