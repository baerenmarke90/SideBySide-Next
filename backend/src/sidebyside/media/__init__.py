"""Media storage.

Configuration selects the active adapter, not the domain. The domain sees
only `MediaStore`.
"""

from __future__ import annotations

from functools import lru_cache

from sidebyside.config import MediaStoreBackend, get_settings
from sidebyside.media.base import (
    ByteSource,
    MediaStore,
    StoredObject,
    build_storage_key,
)
from sidebyside.media.local import LocalMediaStore
from sidebyside.media.presigned import (
    SignedUpload,
    create_signed_upload,
    supports_signed_upload,
)
from sidebyside.media.s3 import S3MediaStore

__all__ = [
    "ByteSource",
    "LocalMediaStore",
    "MediaStore",
    "S3MediaStore",
    "SignedUpload",
    "StoredObject",
    "build_storage_key",
    "create_signed_upload",
    "get_media_store",
    "supports_signed_upload",
]


@lru_cache(maxsize=1)
def get_media_store() -> MediaStore:
    """Return configured storage without exposing S3 knowledge to domain code."""
    settings = get_settings()
    if settings.media_store is MediaStoreBackend.LOCAL:
        return LocalMediaStore(settings.media_root)

    if settings.s3_access_key_id is None or settings.s3_secret_access_key is None:
        # Settings already validates this. The defensive check keeps the
        # factory type-safe and failure-safe when used in isolation.
        raise RuntimeError("S3 media credentials are missing.")

    return S3MediaStore(
        endpoint=settings.s3_endpoint,
        region=settings.s3_region,
        bucket=settings.s3_bucket,
        access_key_id=settings.s3_access_key_id.get_secret_value(),
        secret_access_key=settings.s3_secret_access_key.get_secret_value(),
        session_token=(
            settings.s3_session_token.get_secret_value()
            if settings.s3_session_token is not None
            else None
        ),
    )
