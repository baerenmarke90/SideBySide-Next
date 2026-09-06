"""Boot-time fail-closed coverage for production/Cloud configuration.

compose.yaml (#746) deliberately defaults SBS_DATABASE_URL, SBS_ALLOWED_HOSTS,
SBS_PUBLIC_BASE_URL, and SBS_CURSOR_SIGNING_KEY to blank/empty for every
profile, including ``cloud``, rather than a Compose-level ``${VAR:?...}``: a
hard interpolation failure there would break every profile's ability to
render independently, since Compose interpolates the whole file regardless of
which ``--profile`` is active. The fail-closed guarantee for these values
therefore lives here, in ``Settings`` validation, instead. These tests prove
that an operator who leaves one of them unset in a real ``cloud`` deployment
(which is exactly what compose.yaml then passes to the container: an empty
string, or an empty list) still cannot boot the application.
"""

import pytest
from pydantic import SecretStr, ValidationError

from sidebyside.config import DatabaseSettings, Deployment, Environment, MailTransport, Settings


def _cloud_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": Environment.PRODUCTION,
        "deployment": Deployment.CLOUD,
        "database_url": "postgresql+psycopg://user:pass@db.private:5432/sidebyside",
        "cursor_signing_key": SecretStr("x" * 48),
        "allowed_hosts": ["cloud.example.test"],
        "public_base_url": "https://cloud.example.test",
        "mail_transport": MailTransport.NONE,
    }
    values.update(overrides)
    return Settings.model_validate(values)


def test_cloud_settings_are_otherwise_valid() -> None:
    settings = _cloud_settings()
    assert settings.is_production is True


def test_empty_database_url_is_rejected() -> None:
    # What compose.yaml's `${SBS_DATABASE_URL:-}` actually sets when unset.
    with pytest.raises(ValidationError, match="SBS_DATABASE_URL is empty"):
        _cloud_settings(database_url="")


def test_database_settings_also_rejects_an_empty_url() -> None:
    with pytest.raises(ValidationError, match="SBS_DATABASE_URL is empty"):
        DatabaseSettings.model_validate({"database_url": ""})


def test_production_rejects_an_empty_allowed_hosts_list() -> None:
    # What compose.yaml's cloud profile sets by default: `${SBS_ALLOWED_HOSTS:-[]}`.
    with pytest.raises(ValidationError, match="explicit SBS_ALLOWED_HOSTS"):
        _cloud_settings(allowed_hosts=[])


def test_production_rejects_a_wildcard_allowed_host() -> None:
    with pytest.raises(ValidationError, match="explicit SBS_ALLOWED_HOSTS"):
        _cloud_settings(allowed_hosts=["*"])


def test_production_requires_a_cursor_signing_key() -> None:
    with pytest.raises(ValidationError, match="requires SBS_CURSOR_SIGNING_KEY"):
        _cloud_settings(cursor_signing_key=None)


def test_production_rejects_a_blank_public_base_url() -> None:
    # What compose.yaml's cloud profile sets by default: `${SBS_PUBLIC_BASE_URL:-}`.
    with pytest.raises(ValidationError, match="https SBS_PUBLIC_BASE_URL"):
        _cloud_settings(public_base_url="")


def test_production_rejects_a_non_https_public_base_url() -> None:
    with pytest.raises(ValidationError, match="https SBS_PUBLIC_BASE_URL"):
        _cloud_settings(public_base_url="http://cloud.example.test")
