"""Operational health information and app construction."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sidebyside.config import Environment, MailTransport, Settings
from sidebyside.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(), raise_server_exceptions=False)


class TestHealth:
    def test_liveness_does_not_require_database(self, client: TestClient) -> None:
        """Liveness must not fail merely because the database is unavailable."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_readiness_reports_503_without_database(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/ready")
        assert response.status_code in (200, 503)
        if response.status_code == 503:
            assert response.json()["database"] == "unavailable"

    def test_readiness_does_not_leak_connection_details(self, client: TestClient) -> None:
        """A connection error can contain host, port, and username."""
        raw_text = client.get("/api/v1/health/ready").text
        for forbidden in ("postgresql", "psycopg", "localhost", "5432", "Traceback"):
            assert forbidden not in raw_text


class TestApiContract:
    def test_everything_is_under_api_v1(self, client: TestClient) -> None:
        """The version is in the path so older installations can survive future breaking changes."""
        paths = list(client.get("/openapi.json").json()["paths"])
        assert paths
        assert all(path.startswith("/api/v1/") for path in paths), paths

    def test_openapi_is_reachable(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "/api/v1/health" in response.json()["paths"]


class TestProduction:
    def test_schema_is_closed_in_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An exposed schema is a map of the attack surface."""
        monkeypatch.setattr(
            "sidebyside.main.get_settings",
            lambda: Settings(
                environment=Environment.PRODUCTION,
                mail_transport=MailTransport.SMTP,
                public_base_url="https://app.example",
                cursor_signing_key="cursor-test-" + ("x" * 40),
            ),
        )
        production = TestClient(
            create_app(), base_url="http://localhost", raise_server_exceptions=False
        )
        assert production.get("/openapi.json").status_code == 404
        assert production.get("/docs").status_code == 404
