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

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from sidebyside.api.schema import ApiModel
from sidebyside.core.errors import DomainError, ErrorCode

log = logging.getLogger(__name__)


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


def problem(status: int, type_: str, title: str, detail: str, code: str) -> JSONResponse:
    body = ProblemDetails(type=type_, title=title, status=status, detail=detail, code=code)
    return JSONResponse(status_code=status, content=body.model_dump())


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
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
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
