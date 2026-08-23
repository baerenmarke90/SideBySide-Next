"""MediaStore-Schnittstelle.

Self-Hosted legt Dateien ins Dateisystem, Cloud in einen Objektspeicher.
Der Application Core kennt keinen von beiden.

Zwei Regeln, die für jede Implementierung gelten:

- Der Storage Key wird NIEMALS aus einem Benutzer-Dateinamen abgeleitet.
  Ein Dateiname aus einer Anfrage kann Pfadbestandteile enthalten.
- Medien sind nicht öffentlich. Lesen erfolgt über eine autorisierte Route
  oder eine kurzlebige signierte URL.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import BinaryIO
from uuid import UUID


@dataclass(frozen=True)
class StoredObject:
    storage_key: str
    size: int
    content_type: str


def build_storage_key(space_id: UUID, attachment_id: UUID, variant: str = "original") -> str:
    """Den Ablageort bilden.

        spaces/{spaceUuid}/attachments/{attachmentUuid}/original

    Ausschließlich aus UUIDs. Der ursprüngliche Dateiname wird als
    Metadatum geführt und geht nie in den Pfad ein.
    """
    if "/" in variant or ".." in variant:
        raise ValueError("Ungültige Variante.")
    return f"spaces/{space_id}/attachments/{attachment_id}/{variant}"


class MediaStore(ABC):
    """Ablage für Anhänge."""

    @abstractmethod
    def put(self, storage_key: str, data: BinaryIO, content_type: str) -> StoredObject:
        """Einen Datenstrom ablegen."""

    @abstractmethod
    def open(self, storage_key: str) -> BinaryIO:
        """Zum Lesen öffnen."""

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        """Entfernen. Ein bereits fehlendes Objekt ist kein Fehler."""

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        ...

    @abstractmethod
    def create_read_url(self, storage_key: str, expires_in: timedelta) -> str | None:
        """Eine kurzlebige Lese-URL, sofern die Ablage das kann.

        Gibt None zurück, wenn nicht - dann muss die Anwendung den Inhalt
        selbst ausliefern. Das Dateisystem kann keine signierten URLs.
        """
