"""Sichere Transportgrenzen im produktiven Betrieb."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sidebyside.config import Environment, Settings
from sidebyside.main import create_app


def production_client(
    monkeypatch: pytest.MonkeyPatch, base_url: str, allowed_hosts: list[str]
) -> TestClient:
    monkeypatch.setattr(
        "sidebyside.main.get_settings",
        lambda: Settings(environment=Environment.PRODUCTION, allowed_hosts=allowed_hosts),
    )
    return TestClient(create_app(), base_url=base_url, raise_server_exceptions=False)


class TestAllowedHosts:
    def test_unbekannter_host_wird_abgewiesen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = production_client(monkeypatch, "https://falsch.example", ["app.example"])
        assert client.get("/api/v1/health").status_code == 400

    def test_offener_wildcard_ist_in_produktion_verboten(self) -> None:
        with pytest.raises(ValueError, match="SBS_ALLOWED_HOSTS"):
            Settings(environment=Environment.PRODUCTION, allowed_hosts=["*"])


class TestBootstrapKonfiguration:
    def test_kurzes_geheimnis_wird_abgewiesen(self) -> None:
        with pytest.raises(ValueError, match="SBS_BOOTSTRAP_TOKEN"):
            Settings(bootstrap_token="zu-kurz")

    def test_geheimnis_erscheint_nicht_in_settings_ausgabe(self) -> None:
        geheimnis = "test-bootstrap-secret-with-at-least-32-characters"
        settings = Settings(bootstrap_token=geheimnis)
        assert geheimnis not in repr(settings)


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
