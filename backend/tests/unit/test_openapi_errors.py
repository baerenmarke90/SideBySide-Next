"""Der OpenAPI-Vertrag beschreibt die tatsaechlichen Fehlerpfade der v1-API."""

from __future__ import annotations

from typing import Any

from sidebyside.main import create_app

PROBLEM_DETAILS_REF = "#/components/schemas/ProblemDetails"
READINESS_REF = "#/components/schemas/Readiness"

EXPECTED_PROBLEM_RESPONSES: dict[tuple[str, str], set[int]] = {
    ("/api/v1/auth/register", "post"): {403, 409, 422, 429},
    ("/api/v1/auth/sign-in", "post"): {401, 422, 429},
    ("/api/v1/auth/refresh", "post"): {401, 422, 429},
    ("/api/v1/auth/sign-out", "post"): {401},
    ("/api/v1/auth/password", "post"): {401, 422},
    ("/api/v1/auth/me", "get"): {401},
    ("/api/v1/auth/magic-link/request", "post"): {422, 429},
    ("/api/v1/auth/magic-link/consume", "post"): {422},
    ("/api/v1/auth/email/verification/request", "post"): {401, 429},
    ("/api/v1/auth/email/verification/confirm", "post"): {422},
    ("/api/v1/auth/recovery/request", "post"): {422, 429},
    ("/api/v1/auth/recovery/consume", "post"): {422},
    ("/api/v1/spaces/{spaceId}/invitations", "post"): {401, 404, 409},
    ("/api/v1/spaces/{spaceId}/invitations", "get"): {401, 404},
    ("/api/v1/spaces/{spaceId}/invitations/{invitationId}", "delete"): {401, 404},
    ("/api/v1/invitations/accept", "post"): {401, 409, 422},
    ("/api/v1/spaces/{spaceId}", "get"): {401, 404},
    ("/api/v1/spaces/{spaceId}/profile", "get"): {401, 404},
    ("/api/v1/spaces/{spaceId}/profile", "put"): {401, 404, 409, 422},
}


def _response_schema(response: dict[str, Any]) -> dict[str, Any]:
    return response.get("content", {}).get("application/json", {}).get("schema", {})


def test_v1_endpunkte_dokumentieren_nur_ihre_tatsaechlichen_problem_details() -> None:
    schema = create_app().openapi()

    for (path, method), erwartet in EXPECTED_PROBLEM_RESPONSES.items():
        responses = schema["paths"][path][method]["responses"]
        dokumentiert = {
            int(status)
            for status, response in responses.items()
            if _response_schema(response).get("$ref") == PROBLEM_DETAILS_REF
        }
        assert dokumentiert == erwartet, f"{method.upper()} {path}"


def test_request_validation_verweist_nicht_mehr_auf_fastapi_defaultmodell() -> None:
    schema = create_app().openapi()

    for (path, method), statuses in EXPECTED_PROBLEM_RESPONSES.items():
        responses = schema["paths"][path][method]["responses"]
        if 422 in statuses:
            assert _response_schema(responses["422"]) == {"$ref": PROBLEM_DETAILS_REF}
        else:
            # FastAPI erfindet fuer reine str-Path-Parameter ebenfalls einen
            # generischen 422. SideBySide mappt solche IDs absichtlich auf
            # 404; der unmoegliche Framework-Default darf nicht im Vertrag stehen.
            assert "422" not in responses

    schemas = schema["components"]["schemas"]
    assert "HTTPValidationError" not in schemas
    assert "ValidationError" not in schemas


def test_readiness_503_hat_sein_tatsaechliches_betriebsmodell() -> None:
    schema = create_app().openapi()
    response = schema["paths"]["/api/v1/health/ready"]["get"]["responses"]["503"]

    assert _response_schema(response) == {"$ref": READINESS_REF}
