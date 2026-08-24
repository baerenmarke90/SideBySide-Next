"""Ein einziges Fehlerformat, fuer jeden Fehler.

Ein Client, der eine Fehlermeldung anzeigen will, braucht dafuer genau
einen Weg. Geprueft wird ueber eine echte App mit echten Routen, nicht
gegen die Handler-Funktionen - die Registrierung selbst ist Teil dessen,
was schiefgehen kann.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from sidebyside.api.errors import register_error_handlers
from sidebyside.core.errors import (
    ConflictError,
    ErrorCode,
    ForbiddenError,
    NotFoundError,
    UnauthenticatedError,
    ValidationError,
)

PFLICHTFELDER = {"type", "title", "status", "detail", "code"}


class Body(BaseModel):
    title: str


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/not-found")
    def _not_found() -> None:
        raise NotFoundError("Memory not found.", "MEMORY_NOT_FOUND")

    @app.get("/api/v1/domain-not-found")
    def _api_domain_not_found() -> None:
        raise NotFoundError("Space not found.", "SPACE_NOT_FOUND")

    @app.get("/forbidden")
    def _forbidden() -> None:
        raise ForbiddenError("Not allowed.", "SPACE_ACCESS_DENIED")

    @app.get("/unauthenticated")
    def _unauth() -> None:
        raise UnauthenticatedError("Sign in.", ErrorCode.AUTHENTICATION_REQUIRED)

    @app.get("/conflict")
    def _conflict() -> None:
        raise ConflictError("Changed meanwhile.", ErrorCode.VERSION_CONFLICT)

    @app.get("/invalid")
    def _invalid() -> None:
        raise ValidationError("The title must not be empty.", "MEMORY_TITLE_REQUIRED")

    @app.get("/boom")
    def _boom() -> None:
        raise RuntimeError("Verbindung zu postgres://benutzer:geheim@host fehlgeschlagen")

    @app.post("/body")
    def _body(body: Body) -> dict[str, str]:
        return {"title": body.title}

    return TestClient(app, raise_server_exceptions=False)


class TestFormat:
    @pytest.mark.parametrize(
        ("pfad", "status", "typ", "code"),
        [
            ("/not-found", 404, "not_found", "MEMORY_NOT_FOUND"),
            ("/forbidden", 403, "forbidden", "SPACE_ACCESS_DENIED"),
            ("/unauthenticated", 401, "unauthenticated", "AUTHENTICATION_REQUIRED"),
            ("/conflict", 409, "conflict", "VERSION_CONFLICT"),
            ("/invalid", 422, "validation_error", "MEMORY_TITLE_REQUIRED"),
        ],
    )
    def test_fachliche_fehler(
        self, client: TestClient, pfad: str, status: int, typ: str, code: str
    ) -> None:
        antwort = client.get(pfad)
        assert antwort.status_code == status
        koerper = antwort.json()
        assert set(koerper) == PFLICHTFELDER
        assert koerper["type"] == typ
        assert koerper["status"] == status
        assert koerper["code"] == code

    def test_unbekannte_route(self, client: TestClient) -> None:
        antwort = client.get("/gibt-es-nicht")
        assert antwort.status_code == 404
        assert set(antwort.json()) == PFLICHTFELDER

    def test_ungueltiger_koerper(self, client: TestClient) -> None:
        antwort = client.post("/body", json={})
        assert antwort.status_code == 422
        koerper = antwort.json()
        assert koerper["code"] == ErrorCode.VALIDATION_FAILED
        assert "title" in koerper["detail"]


class TestApiRouteMisses:
    def test_unbekannte_api_route_hat_problem_details(self, client: TestClient) -> None:
        antwort = client.get("/api/v1/gibt-es-nicht")
        assert antwort.status_code == 404
        assert antwort.json() == {
            "type": "not_found",
            "title": "Not found",
            "status": 404,
            "detail": "Not Found",
            "code": "HTTP_404",
        }

    def test_route_miss_durch_zusaetzliches_pfadsegment_hat_problem_details(
        self, client: TestClient
    ) -> None:
        antwort = client.get("/api/v1/domain-not-found/unerwartetes-segment")
        assert antwort.status_code == 404
        assert set(antwort.json()) == PFLICHTFELDER
        assert antwort.json()["code"] == "HTTP_404"

    def test_fachliche_api_404_behaelt_domain_code(self, client: TestClient) -> None:
        antwort = client.get("/api/v1/domain-not-found")
        assert antwort.status_code == 404
        assert set(antwort.json()) == PFLICHTFELDER
        assert antwort.json()["code"] == "SPACE_NOT_FOUND"
        assert antwort.json()["detail"] == "Space not found."


class TestKeineInternenDetails:
    def test_unerwarteter_fehler_wird_zu_einem_neutralen_500(self, client: TestClient) -> None:
        antwort = client.get("/boom")
        assert antwort.status_code == 500
        assert antwort.json()["code"] == ErrorCode.INTERNAL

    def test_ausnahmetext_erreicht_den_client_nicht(self, client: TestClient) -> None:
        """Eine Ausnahmemeldung kann Zugangsdaten und Pfade tragen."""
        rohtext = client.get("/boom").text
        for verboten in ("geheim", "postgres://", "RuntimeError", "Traceback"):
            assert verboten not in rohtext

    def test_eingesendete_werte_werden_nicht_zurueckgespiegelt(self, client: TestClient) -> None:
        """Ein ungueltiger Wert kann sensibel sein - der Feldname genuegt."""
        rohtext = client.post("/body", json={"title": 12345, "x": "geheimnis"}).text
        assert "geheimnis" not in rohtext
