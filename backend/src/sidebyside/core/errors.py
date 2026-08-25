"""Fachliche Fehler und ihr Weg nach außen.

Jeder Fehler, der eine Anfrage beendet, trägt einen stabilen Code. Der Code
ist Teil des API-Vertrags: Clients dürfen darauf verzweigen, während der
Text sich ändern und übersetzt werden darf.

Die Abbildung auf HTTP steht hier und nicht in den Routen, damit dieselbe
Bedingung überall dieselbe Antwort erzeugt.
"""

from __future__ import annotations

from http import HTTPStatus


class DomainError(Exception):
    """Basis aller fachlichen Fehler.

    `type` ist ein maschinenlesbarer Kurzname der Fehlerklasse, `code` die
    genaue Ursache. Beide erscheinen in der Antwort.
    """

    status: int = HTTPStatus.INTERNAL_SERVER_ERROR
    type: str = "internal_error"
    title: str = "Internal error"

    def __init__(self, detail: str, code: str) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code


class BadRequestError(DomainError):
    status = HTTPStatus.BAD_REQUEST
    type = "bad_request"
    title = "Bad request"


class ValidationError(DomainError):
    status = HTTPStatus.UNPROCESSABLE_ENTITY
    type = "validation_error"
    title = "Invalid request"


class UnauthenticatedError(DomainError):
    status = HTTPStatus.UNAUTHORIZED
    type = "unauthenticated"
    title = "Authentication required"


class ForbiddenError(DomainError):
    status = HTTPStatus.FORBIDDEN
    type = "forbidden"
    title = "Not allowed"


class NotFoundError(DomainError):
    """Nicht gefunden - oder nicht sichtbar.

    Bei privatsphäre-relevanten Ressourcen wird dieser Fehler bewusst auch
    dort verwendet, wo fachlich ein 403 richtiger wäre. Ein 403 bestätigt
    die Existenz; wer fremde IDs durchprobiert, soll nicht erfahren, welche
    davon es gibt. Siehe docs/SECURITY.md.
    """

    status = HTTPStatus.NOT_FOUND
    type = "not_found"
    title = "Not found"


class ConflictError(DomainError):
    """Der Zustand hat sich seit dem Lesen geändert.

    Antwort auf eine verletzte Versionsprüfung bei Optimistic Concurrency.
    """

    status = HTTPStatus.CONFLICT
    type = "conflict"
    title = "Conflict"


class UnsupportedMediaTypeError(DomainError):
    status = HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    type = "unsupported_media_type"
    title = "Unsupported media type"


class PayloadTooLargeError(DomainError):
    status = HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    type = "payload_too_large"
    title = "Payload too large"


class RateLimitedError(DomainError):
    status = HTTPStatus.TOO_MANY_REQUESTS
    type = "rate_limited"
    title = "Too many requests"


class ErrorCode:
    """Stabile Fehlercodes.

    Ein Code wird nicht umbenannt, sobald er ausgeliefert ist - Clients
    verzweigen darauf. Neue Ursachen bekommen neue Codes.
    """

    INTERNAL = "INTERNAL_ERROR"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    MALFORMED_ID = "MALFORMED_ID"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    RESOURCE_VERSION_CONFLICT = "RESOURCE_VERSION_CONFLICT"
    INVALID_CURSOR = "INVALID_CURSOR"
    IF_MATCH_MALFORMED = "IF_MATCH_MALFORMED"
    ATTACHMENT_TYPE_NOT_ALLOWED = "ATTACHMENT_TYPE_NOT_ALLOWED"
    ATTACHMENT_TOO_LARGE = "ATTACHMENT_TOO_LARGE"
    ATTACHMENT_VALIDATION_FAILED = "ATTACHMENT_VALIDATION_FAILED"
    ATTACHMENT_NOT_READY = "ATTACHMENT_NOT_READY"
    RATE_LIMITED = "RATE_LIMITED"
