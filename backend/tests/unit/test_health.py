"""Betriebsauskunft und App-Aufbau."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sidebyside.config import Environment, Settings
from sidebyside.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(), raise_server_exceptions=False)


class TestHealth:
    def test_lebendigkeit_braucht_keine_datenbank(self, client: TestClient) -> None:
        """Sonst startet ein Orchestrator den Container neu, nur weil die
        Datenbank gerade nicht erreichbar ist."""
        antwort = client.get("/api/v1/health")
        assert antwort.status_code == 200
        assert antwort.json() == {"status": "ok"}

    def test_bereitschaft_meldet_503_ohne_datenbank(self, client: TestClient) -> None:
        antwort = client.get("/api/v1/health/ready")
        assert antwort.status_code in (200, 503)
        if antwort.status_code == 503:
            assert antwort.json()["database"] == "unavailable"

    def test_bereitschaft_verraet_keine_verbindungsdaten(self, client: TestClient) -> None:
        """Eine Verbindungsmeldung enthaelt Host, Port und Benutzernamen."""
        rohtext = client.get("/api/v1/health/ready").text
        for verboten in ("postgresql", "psycopg", "localhost", "5432", "Traceback"):
            assert verboten not in rohtext


class TestApiVertrag:
    def test_alles_liegt_unter_api_v1(self, client: TestClient) -> None:
        """Die Version steht im Pfad, damit aeltere Installationen
        weiterlaufen, wenn spaeter brechend geaendert wird."""
        pfade = list(client.get("/openapi.json").json()["paths"])
        assert pfade
        assert all(p.startswith("/api/v1/") for p in pfade), pfade

    def test_openapi_ist_erreichbar(self, client: TestClient) -> None:
        antwort = client.get("/openapi.json")
        assert antwort.status_code == 200
        assert "/api/v1/health" in antwort.json()["paths"]


class TestProduktion:
    def test_schema_ist_in_produktion_verschlossen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ein offenes Schema ist eine Landkarte der Angriffsflaeche."""
        monkeypatch.setattr(
            "sidebyside.main.get_settings",
            lambda: Settings(environment=Environment.PRODUCTION),
        )
        produktion = TestClient(create_app(), raise_server_exceptions=False)
        assert produktion.get("/openapi.json").status_code == 404
        assert produktion.get("/docs").status_code == 404
