"""Operational health endpoints.

Two separate questions require two different answers:

- ``/health``: is the process running? This does not touch the database, so an
  orchestrator does not restart the container merely because the database is
  temporarily unavailable.
- ``/health/ready``: can the process serve requests? This checks the database.
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


@router.get(
    "/health/ready",
    response_model=Readiness,
    responses={
        503: {
            "model": Readiness,
            "description": "The process is running, but the database is unavailable.",
        }
    },
)
def readiness(response: Response) -> Readiness:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        # Do not expose exception text: a connection error can contain host,
        # port, and username details.
        response.status_code = 503
        return Readiness(status="unavailable", database="unavailable")

    return Readiness(status="ok", database="ok")
