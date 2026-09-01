"""Observability, structured logging, request correlation, and redaction."""

from __future__ import annotations

from sidebyside.observability.context import (
    account_id_var,
    bind_actor_context,
    correlation_id_var,
    get_account_id,
    get_correlation_id,
    get_request_id,
    get_space_id,
    request_id_var,
    reset_context,
    set_account_id,
    set_correlation_id,
    set_request_id,
    set_space_id,
    space_id_var,
)
from sidebyside.observability.formatting import (
    ConsoleLogFormatter,
    JsonLogFormatter,
    configure_logging,
)
from sidebyside.observability.middleware import (
    RequestIdMiddleware,
    RequestLoggingMiddleware,
)
from sidebyside.observability.redaction import (
    REDACTED,
    RedactingFilter,
    scrub_data,
    scrub_headers,
    scrub_message,
    scrub_url,
)

__all__ = [
    "REDACTED",
    "ConsoleLogFormatter",
    "JsonLogFormatter",
    "RedactingFilter",
    "RequestIdMiddleware",
    "RequestLoggingMiddleware",
    "account_id_var",
    "bind_actor_context",
    "configure_logging",
    "correlation_id_var",
    "get_account_id",
    "get_correlation_id",
    "get_request_id",
    "get_space_id",
    "request_id_var",
    "reset_context",
    "scrub_data",
    "scrub_headers",
    "scrub_message",
    "scrub_url",
    "set_account_id",
    "set_correlation_id",
    "set_request_id",
    "set_space_id",
    "space_id_var",
]
