"""Fehlerausgabe im Problem-Details-Stil.

Ein einziges Antwortformat für jeden Fehler. Ein Client, der eine
Fehlermeldung anzeigen will, braucht dafür genau einen Weg.

    {
      "type": "validation_error",
      "title": "Invalid request",
      "status": 422,
      "detail": "The title must not be empty.",
      "code": "MEMORY_TITLE_REQUIRED"
    }
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from sidebyside.api.schema import ApiModel
from sidebyside.core.errors import DomainError, ErrorCode

log = logging.getLogger(__name__)

_API_V1_PREFIX = "/api/v1"


class ProblemDetails(ApiModel):
    """Der Rumpf jeder Fehlerantwort.

    Dasselbe Modell erzeugt die Antwort und beschreibt sie im OpenAPI-
    Vertrag. Getrennt gepflegt wuerden beide irgendwann auseinanderlaufen,
    und der Vertrag beschriebe dann einen Fehler, den es so nicht gibt.
    """

    type: str
    title: str
    status: int
    detail: str
    code: str


_STATUS_TYPES: dict[int, tuple[str, str]] = {
    400: ("bad_request", "Bad request"),
    401: ("unauthenticated", "Authentication required"),
    403: ("forbidden", "Not allowed"),
    404: ("not_found", "Not found"),
    405: ("method_not_allowed", "Method not allowed"),
    409: ("conflict", "Conflict"),
    422: ("validation_error", "Invalid request"),
    429: ("rate_limited", "Too many requests"),
}

_PROBLEM_RESPONSE_DESCRIPTIONS: dict[int, str] = {
    400: "Die Anfrage ist syntaktisch gueltig, kann aber so nicht verarbeitet werden.",
    401: "Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen.",
    403: "Der Aufrufer ist authentifiziert, aber fuer diesen Vorgang nicht berechtigt.",
    404: "Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar.",
    405: "Die HTTP-Methode ist fuer diese Ressource nicht vorgesehen.",
    409: "Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource.",
    413: "Der Inhalt ueberschreitet die serverseitige Groessengrenze.",
    415: "Der Medientyp steht nicht auf der Allowlist.",
    422: "Anfrageparameter oder fachliche Eingaben sind ungueltig.",
    429: "Zu viele Versuche innerhalb des erlaubten Zeitfensters.",
}


def problem_responses(
    *status_codes: int,
    descriptions: Mapping[int, str] | None = None,
) -> dict[int | str, dict[str, Any]]:
    """Wiederverwendbare OpenAPI-Antworten fuer bekannte ProblemDetails.

    Die Route nennt nur Fehler, die ihr produktiver Pfad tatsaechlich
    ausloesen kann. So bleibt der Vertrag vollstaendig, ohne moegliche
    Fehler zu erfinden. Ein explizites 422 ersetzt zugleich FastAPIs
    Standard-HTTPValidationError durch unser tatsaechliches Runtime-Modell.
    """
    overrides = descriptions or {}
    antworten: dict[int | str, dict[str, Any]] = {}
    for status_code in status_codes:
        standard = _PROBLEM_RESPONSE_DESCRIPTIONS.get(status_code)
        if standard is None:
            raise ValueError(f"No ProblemDetails OpenAPI description for HTTP {status_code}.")
        antworten[status_code] = {
            "model": ProblemDetails,
            "description": overrides.get(status_code, standard),
        }
    return antworten


def problem(status: int, type_: str, title: str, detail: str, code: str) -> JSONResponse:
    body = ProblemDetails(type=type_, title=title, status=status, detail=detail, code=code)
    return JSONResponse(status_code=status, content=body.model_dump())


def _is_api_v1_path(path: str) -> bool:
    """Nur echte API-v1-Pfade treffen die explizite Route-Miss-Regel."""
    return path == _API_V1_PREFIX or path.startswith(f"{_API_V1_PREFIX}/")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(_: Request, exc: DomainError) -> JSONResponse:
        return problem(exc.status, exc.type, exc.title, exc.detail, exc.code)

    @app.exception_handler(RequestValidationError)
    async def _request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Die Feldpfade sind für den Aufrufer nützlich; die eingesendeten
        # Werte werden bewusst nicht zurückgespiegelt, weil sie sensibel
        # sein können.
        felder = ", ".join(
            ".".join(str(teil) for teil in fehler.get("loc", ())[1:]) for fehler in exc.errors()
        )
        detail = f"Invalid fields: {felder}" if felder else "Invalid request body."
        return problem(
            422,
            "validation_error",
            "Invalid request",
            detail,
            ErrorCode.VALIDATION_FAILED,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Ein Router-Miss erreicht keine fachliche Route und kann deshalb
        # keinen NotFoundError mit einem Domain-Code erzeugen. Fuer /api/v1
        # wird der Framework-404 hier ausdruecklich als ProblemDetails
        # festgeschrieben. Fachliche 404 laufen weiterhin ueber _domain.
        if exc.status_code == 404 and _is_api_v1_path(request.url.path):
            return problem(404, "not_found", "Not found", str(exc.detail), "HTTP_404")

        # Das bisherige Verhalten fuer alle anderen Framework-Fehler und
        # fuer Pfade ausserhalb /api/v1 bleibt unveraendert.
        type_, title = _STATUS_TYPES.get(exc.status_code, ("error", "Error"))
        return problem(
            exc.status_code,
            type_,
            title,
            str(exc.detail),
            f"HTTP_{exc.status_code}",
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Die Ursache gehört ins Log, nicht in die Antwort: eine
        # Ausnahmemeldung kann Pfade, Abfragen oder Nutzerinhalte tragen.
        log.exception("unhandled error", extra={"path": request.url.path, "method": request.method})
        return problem(
            500,
            "internal_error",
            "Internal error",
            "An unexpected error occurred.",
            ErrorCode.INTERNAL,
        )
