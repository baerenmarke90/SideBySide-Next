"""OpenAPI-Anpassungen fuer den tatsaechlichen SideBySide-HTTP-Vertrag.

FastAPI fuegt fuer Routen mit Path-/Body-Parametern automatisch eine 422-
Antwort mit ``HTTPValidationError`` ein. SideBySide liefert zur Laufzeit
aber ausschliesslich ``ProblemDetails``. Ausserdem sind manche automatisch
ergänzten 422 bei bewusst als ``str`` entgegengenommenen IDs gar nicht
erreichbar: fehlgeformte IDs werden aus Privacy-Gruenden fachlich zu 404.

Tatsaechliche 422-Pfade werden deshalb an der Route explizit dokumentiert.
Nur den verbleibenden, von FastAPI implizit erzeugten Default entfernen wir
hier aus dem Schema.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute

_HTTP_VALIDATION_REF = "#/components/schemas/HTTPValidationError"
_VALIDATION_ERROR_REF = "#/components/schemas/ValidationError"


def _response_schema_ref(response: dict[str, Any]) -> str | None:
    schema = response.get("content", {}).get("application/json", {}).get("schema", {})
    ref = schema.get("$ref")
    return ref if isinstance(ref, str) else None


def _paths_reference(schema: dict[str, Any], ref: str) -> bool:
    """Pruefen, ob irgendeine Operation noch auf ein Schema verweist."""
    stack: list[Any] = [schema.get("paths", {})]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            if current.get("$ref") == ref:
                return True
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return False


def _remove_implicit_fastapi_validation(schema: dict[str, Any], routes: list[Any]) -> None:
    for route in routes:
        if not isinstance(route, APIRoute):
            continue

        # Nur ein an der Route explizit deklarierter 422 ist Teil unseres
        # Vertrags. Er verwendet bereits ProblemDetails und bleibt erhalten.
        declared_responses = {str(status) for status in route.responses}
        if "422" in declared_responses:
            continue

        path_item = schema.get("paths", {}).get(route.path, {})
        for method in route.methods or ():
            operation = path_item.get(method.lower())
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses", {})
            implicit = responses.get("422")
            if (
                isinstance(implicit, dict)
                and _response_schema_ref(implicit) == _HTTP_VALIDATION_REF
            ):
                del responses["422"]

    schemas = schema.get("components", {}).get("schemas", {})
    if isinstance(schemas, dict):
        if not _paths_reference(schema, _HTTP_VALIDATION_REF):
            schemas.pop("HTTPValidationError", None)
        if not _paths_reference(schema, _VALIDATION_ERROR_REF):
            schemas.pop("ValidationError", None)


class SideBySideFastAPI(FastAPI):
    """FastAPI mit dem bereinigten, produktiven Fehlervertrag."""

    def openapi(self) -> dict[str, Any]:
        schema = super().openapi()
        _remove_implicit_fastapi_validation(schema, self.routes)
        return schema
