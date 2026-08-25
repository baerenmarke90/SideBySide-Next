"""Medienablage.

Welcher Adapter laeuft, entscheidet die Konfiguration - nicht die Domaene.
Sie sieht nur `MediaStore`.
"""

from __future__ import annotations

from functools import lru_cache

from sidebyside.config import get_settings
from sidebyside.media.base import (
    ByteSource,
    MediaStore,
    StoredObject,
    build_storage_key,
)
from sidebyside.media.local import LocalMediaStore

__all__ = [
    "ByteSource",
    "LocalMediaStore",
    "MediaStore",
    "StoredObject",
    "build_storage_key",
    "get_media_store",
]


@lru_cache(maxsize=1)
def get_media_store() -> MediaStore:
    """Die konfigurierte Ablage.

    Heute gibt es genau eine Umsetzung. Der S3-Adapter kommt als eigener
    Slice dazu und waehlt hier ueber die Konfiguration, ohne dass eine
    Domaene davon erfaehrt.
    """
    return LocalMediaStore(get_settings().media_root)
