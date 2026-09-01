"""Log formatters and logging configuration.

Supports structured JSON formatting for production/cloud and human-readable
text formatting for local development and tests, with automatic context
enrichment (request_id, correlation_id, actor_id, space_id) and redaction.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from sidebyside.config import LogFormat, Settings
from sidebyside.observability.context import (
    get_account_id,
    get_correlation_id,
    get_request_id,
    get_space_id,
)
from sidebyside.observability.redaction import RedactingFilter, scrub_data

_STANDARD_LOG_RECORD_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


class JsonLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON with context enrichment."""

    def format(self, record: logging.LogRecord) -> str:
        record_message = record.getMessage()

        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record_message,
        }

        request_id = getattr(record, "request_id", None) or get_request_id()
        if request_id:
            entry["request_id"] = request_id

        correlation_id = getattr(record, "correlation_id", None) or get_correlation_id()
        if correlation_id:
            entry["correlation_id"] = correlation_id

        account_id = getattr(record, "account_id", None) or get_account_id()
        if account_id:
            entry["account_id"] = account_id

        space_id = getattr(record, "space_id", None) or get_space_id()
        if space_id:
            entry["space_id"] = space_id

        extra_fields: dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if (
                key not in _STANDARD_LOG_RECORD_ATTRIBUTES
                and key not in entry
                and not key.startswith("_")
            ):
                extra_fields[key] = value

        if extra_fields:
            entry["extra"] = scrub_data(extra_fields)

        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)


class ConsoleLogFormatter(logging.Formatter):
    """Human-readable text formatter for local development and test runs."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s %(levelname)s %(name)s%(context_tag)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        req_id = getattr(record, "request_id", None) or get_request_id()
        corr_id = getattr(record, "correlation_id", None) or get_correlation_id()

        tags: list[str] = []
        if req_id:
            tags.append(f"req={req_id}")
        if corr_id and corr_id != req_id:
            tags.append(f"corr={corr_id}")

        if tags:
            record.context_tag = " [" + " ".join(tags) + "]"
        else:
            record.context_tag = ""

        return super().format(record)


def configure_logging(settings: Settings) -> None:
    """Configure the root logger with the desired format and redaction filter."""
    root_logger = logging.getLogger()

    try:
        level = getattr(logging, settings.log_level.upper(), logging.INFO)
    except Exception:
        level = logging.INFO

    root_logger.setLevel(level)

    # Remove existing handlers to prevent duplicate output
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.addFilter(RedactingFilter())

    if settings.effective_log_format == LogFormat.JSON:
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(ConsoleLogFormatter())

    root_logger.addHandler(handler)
