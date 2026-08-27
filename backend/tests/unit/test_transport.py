"""Secure transport boundaries in production."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sidebyside.config import Environment, MailTransport, Settings
from sidebyside.main import create_app

CURSOR_SIGNING_KEY = "cursor-test-" + ("x" * 40)


def production_settings(**overrides: object) -> Settings:
    """Return a complete production configuration.

    Production requires several fields, including a real mail transport and
    an installation-specific cursor key. These tests exercise transport and
    must not fail on those requirements, but must not bypass them either.
    """
    values: dict[str, object] = {
        "environment": Environment.PRODUCTION,
        "allowed_hosts": ["app.example"],
        "mail_transport": MailTransport.SMTP,
        "public_base_url": "https://app.example",
        "cursor_signing_key": CURSOR_SIGNING_KEY,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def production_client(
    monkeypatch: pytest.MonkeyPatch, base_url: str, allowed_hosts: list[str]
) -> TestClient:
    monkeypatch.setattr(
        "sidebyside.main.get_settings",
        lambda: production_settings(allowed_hosts=allowed_hosts),
    )
    return TestClient(create_app(), base_url=base_url, raise_server_exceptions=False)


class TestAllowedHosts:
    def test_unknown_host_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = production_client(monkeypatch, "https://wrong.example", ["app.example"])
        assert client.get("/api/v1/health").status_code == 400

    def test_open_wildcard_is_forbidden_in_production(self) -> None:
        with pytest.raises(ValueError, match="SBS_ALLOWED_HOSTS"):
            production_settings(allowed_hosts=["*"])


class TestBootstrapConfiguration:
    def test_short_secret_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="SBS_BOOTSTRAP_TOKEN"):
            Settings(bootstrap_token="too-short")

    def test_secret_does_not_appear_in_settings_output(self) -> None:
        secret = "test-bootstrap-secret-with-at-least-32-characters"
        settings = Settings(bootstrap_token=secret)
        assert secret not in repr(settings)


class TestCursorConfiguration:
    def test_production_requires_cursor_signing_key(self) -> None:
        with pytest.raises(ValueError, match="SBS_CURSOR_SIGNING_KEY"):
            production_settings(cursor_signing_key=None)

    def test_short_cursor_signing_key_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="SBS_CURSOR_SIGNING_KEY"):
            Settings(cursor_signing_key="too-short")

    def test_cursor_signing_key_does_not_appear_in_settings_output(self) -> None:
        settings = Settings(cursor_signing_key=CURSOR_SIGNING_KEY)
        assert CURSOR_SIGNING_KEY not in repr(settings)


class TestHttpsBoundary:
    def test_loopback_may_use_plaintext(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = production_client(monkeypatch, "http://127.0.0.1", ["127.0.0.1"])
        assert client.get("/api/v1/health").status_code == 200

    def test_external_host_requires_https(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = production_client(monkeypatch, "http://app.example", ["app.example"])
        response = client.get(
            "/api/v1/health",
            # Only a trusted proxy may change the ASGI scheme. A header from a
            # normal client must not bypass the check.
            headers={"X-Forwarded-Proto": "https"},
        )
        assert response.status_code == 400
        assert response.json()["code"] == "HTTPS_REQUIRED"

    def test_external_https_host_is_allowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = production_client(monkeypatch, "https://app.example", ["app.example"])
        assert client.get("/api/v1/health").status_code == 200
