"""Filesystem MediaStore for self-hosted deployments and development."""

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
        target = (self._root / storage_key).resolve()
        # Reject keys escaping the storage root. build_storage_key does not
        # create them, but this class does not rely on that because it is the
        # final boundary before the filesystem.
        if not target.is_relative_to(self._root):
            raise ValueError("Storage key escapes the storage root.")
        return target

    def put(self, storage_key: str, data: ByteSource, content_type: str) -> StoredObject:
        target = self._path(storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as file:
            shutil.copyfileobj(data, file)
        return StoredObject(
            storage_key=storage_key,
            size=target.stat().st_size,
            content_type=content_type,
        )

    def open(self, storage_key: str) -> BinaryIO:
        return self._path(storage_key).open("rb")

    def delete(self, storage_key: str) -> None:
        self._path(storage_key).unlink(missing_ok=True)

    def exists(self, storage_key: str) -> bool:
        return self._path(storage_key).is_file()

    def create_read_url(self, storage_key: str, expires_in: timedelta) -> str | None:
        # A filesystem cannot create signed URLs. The application serves the
        # content through an authorized route.
        return None
