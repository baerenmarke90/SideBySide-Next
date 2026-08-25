"""Sichere Transportgrenzen im produktiven Betrieb."""

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from sidebyside.config import Environment, MailTransport, Settings
from sidebyside.main import create_app


CURSOR_SIGNING_KEY = "cursor-test-" + ("x" * 40)


def production_settings(**ueberschreibungen: object) -> Settings:
    """Eine vollstaendige Produktionskonfiguration.

    In Produktion sind mehrere Felder Pflicht - unter anderem echter
    Mailversand und ein installationsspezifischer Cursor-Schluessel. Die
    Tests hier pruefen den Transport und sollen an diesen Pflichten nicht
    scheitern, sie aber auch nicht umgehen.
    """
    werte: dict[str, object] = {
        "environment": Environment.PRODUCTION,
        "allowed_hosts": ["app.example"],
        "mail_transport": MailTransport.SMTP,
        "public_base_url": "https://app.example",
        "cursor_signing_key": CURSOR_SIGNING_KEY,
    }
    werte.update(ueberschreibungen)
    return Settings(**werte)  # type: ignore[arg-type]


def production_client(
    monkeypatch: pytest.MonkeyPatch, base_url: str, allowed_hosts: list[str]
) -> TestClient:
    monkeypatch.setattr(
        "sidebyside.main.get_settings",
        lambda: production_settings(allowed_hosts=allowed_hosts),
    )
    return TestClient(create_app(), base_url=base_url, raise_server_exceptions=False)


class TestAllowedHosts:
    def test_unbekannter_host_wird_abgewiesen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = production_client(monkeypatch, "https://falsch.example", ["app.example"])
        assert client.get("/api/v1/health").status_code == 400

    def test_offener_wildcard_ist_in_produktion_verboten(self) -> None:
        with pytest.raises(ValueError, match="SBS_ALLOWED_HOSTS"):
            production_settings(allowed_hosts=["*"])


class TestBootstrapKonfiguration:
    def test_kurzes_geheimnis_wird_abgewiesen(self) -> None:
        with pytest.raises(ValueError, match="SBS_BOOTSTRAP_TOKEN"):
            Settings(bootstrap_token="zu-kurz")

    def test_geheimnis_erscheint_nicht_in_settings_ausgabe(self) -> None:
        geheimnis = "test-bootstrap-secret-with-at-least-32-characters"
        settings = Settings(bootstrap_token=geheimnis)
        assert geheimnis not in repr(settings)


class TestCursorKonfiguration:
    def test_production_braucht_cursor_signing_key(self) -> None:
        with pytest.raises(ValueError, match="SBS_CURSOR_SIGNING_KEY"):
            production_settings(cursor_signing_key=None)

    def test_kurzer_cursor_signing_key_wird_abgewiesen(self) -> None:
        with pytest.raises(ValueError, match="SBS_CURSOR_SIGNING_KEY"):
            Settings(cursor_signing_key="zu-kurz")

    def test_cursor_signing_key_erscheint_nicht_in_settings_ausgabe(self) -> None:
        settings = Settings(cursor_signing_key=CURSOR_SIGNING_KEY)
        assert CURSOR_SIGNING_KEY not in repr(settings)


class TestHttpsGrenze:
    def test_loopback_darf_klartext_verwenden(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = production_client(monkeypatch, "http://127.0.0.1", ["127.0.0.1"])
        assert client.get("/api/v1/health").status_code == 200

    def test_externer_host_braucht_https(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = production_client(monkeypatch, "http://app.example", ["app.example"])
        response = client.get(
            "/api/v1/health",
            # Nur ein vertrauter Proxy darf das ASGI-Scheme aendern. Der
            # Header eines normalen Clients darf die Pruefung nicht umgehen.
            headers={"X-Forwarded-Proto": "https"},
        )
        assert response.status_code == 400
        assert response.json()["code"] == "HTTPS_REQUIRED"

    def test_externer_https_host_ist_erlaubt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = production_client(monkeypatch, "https://app.example", ["app.example"])
        assert client.get("/api/v1/health").status_code == 200
