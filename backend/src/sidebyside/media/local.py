"""MediaStore im Dateisystem, für Self-Hosted und Entwicklung."""

from __future__ import annotations

import shutil
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO

from sidebyside.media.base import ByteSource, MediaStore, StoredObject


class LocalMediaStore(MediaStore):
    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, storage_key: str) -> Path:
        ziel = (self._root / storage_key).resolve()
        # Ein Key, der aus dem Wurzelverzeichnis herausführt, wird
        # abgewiesen. build_storage_key erzeugt so etwas nicht, aber diese
        # Klasse verlässt sich nicht darauf - sie ist die letzte Instanz vor
        # dem Dateisystem.
        if not ziel.is_relative_to(self._root):
            raise ValueError("Storage Key zeigt aus dem Wurzelverzeichnis heraus.")
        return ziel

    def put(self, storage_key: str, data: ByteSource, content_type: str) -> StoredObject:
        ziel = self._path(storage_key)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        with ziel.open("wb") as datei:
            shutil.copyfileobj(data, datei)
        return StoredObject(
            storage_key=storage_key,
            size=ziel.stat().st_size,
            content_type=content_type,
        )

    def open(self, storage_key: str) -> BinaryIO:
        return self._path(storage_key).open("rb")

    def delete(self, storage_key: str) -> None:
        self._path(storage_key).unlink(missing_ok=True)

    def exists(self, storage_key: str) -> bool:
        return self._path(storage_key).is_file()

    def object_size(self, storage_key: str) -> int | None:
        ziel = self._path(storage_key)
        try:
            return ziel.stat().st_size
        except FileNotFoundError:
            return None

    def create_read_url(self, storage_key: str, expires_in: timedelta) -> str | None:
        # Das Dateisystem kann keine signierten URLs. Die Anwendung liefert
        # den Inhalt über eine autorisierte Route aus.
        return None
