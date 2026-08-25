"""Konfiguration und Adapterauswahl fuer Medien."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sidebyside.config import MediaStoreBackend, Settings, get_settings
from sidebyside.media import S3MediaStore, get_media_store


def test_local_store_is_the_default() -> None:
    settings = Settings()
    assert settings.media_store is MediaStoreBackend.LOCAL


def test_ffmpeg_is_enabled_by_default_and_can_be_disabled(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    assert Settings().ffmpeg_enabled is True
    monkeypatch.setenv("SBS_FFMPEG_ENABLED", "false")
    assert Settings().ffmpeg_enabled is False


def test_s3_store_requires_complete_configuration() -> None:
    with pytest.raises(ValidationError, match="SBS_S3_ENDPOINT"):
        Settings(media_store=MediaStoreBackend.S3)


def test_s3_credentials_are_redacted_from_settings_repr() -> None:
    settings = Settings(
        media_store=MediaStoreBackend.S3,
        s3_endpoint="https://s3.example.test",
        s3_region="eu-central-1",
        s3_bucket="sidebyside-private",
        s3_access_key_id="AKIATEST",
        s3_secret_access_key="very-secret-value",
    )
    assert "very-secret-value" not in repr(settings)
    assert "AKIATEST" not in repr(settings)


def test_s3_endpoint_rejects_embedded_credentials() -> None:
    with pytest.raises(ValidationError, match="without credentials"):
        Settings(
            media_store="s3",
            s3_endpoint="https://user:password@s3.example.test",
            s3_region="eu-central-1",
            s3_bucket="sidebyside-private",
            s3_access_key_id="AKIATEST",
            s3_secret_access_key="very-secret-value",
        )


def test_factory_selects_s3_without_exposing_it_to_domain_code(
    monkeypatch,  # type: ignore[no-untyped-def]
) -> None:
    monkeypatch.setenv("SBS_MEDIA_STORE", "s3")
    monkeypatch.setenv("SBS_S3_ENDPOINT", "https://s3.example.test")
    monkeypatch.setenv("SBS_S3_REGION", "eu-central-1")
    monkeypatch.setenv("SBS_S3_BUCKET", "sidebyside-private")
    monkeypatch.setenv("SBS_S3_ACCESS_KEY_ID", "AKIATEST")
    monkeypatch.setenv("SBS_S3_SECRET_ACCESS_KEY", "very-secret-value")
    get_settings.cache_clear()
    get_media_store.cache_clear()
    try:
        assert isinstance(get_media_store(), S3MediaStore)
    finally:
        get_media_store.cache_clear()
        get_settings.cache_clear()
