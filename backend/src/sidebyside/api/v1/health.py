"""Betriebsauskunft.

Zwei getrennte Fragen, weil sie unterschiedliche Antworten verlangen:

- `/health` - läuft der Prozess? Ohne Datenbankzugriff, damit ein
  Orchestrator den Container nicht neu startet, nur weil die Datenbank
  gerade nicht erreichbar ist.
- `/health/ready` - kann der Prozess Anfragen bedienen? Mit Datenbank.
"""

from __future__ import annotations

from fastapi import APIRouter, Response
from sqlalchemy import text

from sidebyside.api.schema import ApiModel
from sidebyside.db.session import get_engine

router = APIRouter(tags=["health"])


class Health(ApiModel):
    status: str


class Readiness(ApiModel):
    status: str
    database: str


@router.get("/health", response_model=Health)
def health() -> Health:
    return Health(status="ok")


@router.get("/health/ready", response_model=Readiness)
def readiness(response: Response) -> Readiness:
    try:
        with get_engine().connect() as verbindung:
            verbindung.execute(text("SELECT 1"))
    except Exception:
        # Kein Ausnahmetext nach außen: eine Verbindungsmeldung enthält
        # Host, Port und Benutzernamen.
        response.status_code = 503
        return Readiness(status="unavailable", database="unavailable")

    return Readiness(status="ok", database="ok")
