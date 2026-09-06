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

from sidebyside.config import LogFormat, MailTransport, Settings
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
    """Configure log sinks, with one explicit local mail-delivery exception.

    Normal application records always pass through ``RedactingFilter``. The
    development ``LOG`` mail adapter is different: its message body is itself
    the configured delivery medium, so its one-time authentication link must
    remain usable. Only that adapter's module logger receives an unredacted,
    non-propagating handler, and only while ``MailTransport.LOG`` is active in a
    non-public runtime. SMTP, disabled mail, Production, and Demo all fall back
    to the ordinary redacted root sink.
    """
    root_logger = logging.getLogger()

    try:
        level = getattr(logging, settings.log_level.upper(), logging.INFO)
    except Exception:
        level = logging.INFO

    root_logger.setLevel(level)

    # Silence noisy HTTP client and connection pool loggers
    for noisy in ("httpx", "httpx2", "httpcore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Remove existing handlers to prevent duplicate output
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    if settings.effective_log_format == LogFormat.JSON:
        formatter: logging.Formatter = JsonLogFormatter()
    else:
        formatter = ConsoleLogFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.addFilter(RedactingFilter())
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # ``sidebyside.mail.log`` is the implementation of SBS_MAIL_TRANSPORT=log.
    # Its body is intentionally the local delivery channel for one-time auth
    # links. Keep the bypass attached to this exact logger instead of teaching
    # the global redaction filter how to skip records.
    mail_delivery_logger = logging.getLogger("sidebyside.mail.log")
    for mail_handler in list(mail_delivery_logger.handlers):
        mail_delivery_logger.removeHandler(mail_handler)
    mail_delivery_logger.setLevel(logging.NOTSET)
    mail_delivery_logger.propagate = True

    if settings.mail_transport is MailTransport.LOG and not settings.is_production:
        mail_handler = logging.StreamHandler(sys.stdout)
        mail_handler.setLevel(level)
        mail_handler.setFormatter(formatter)
        mail_delivery_logger.addHandler(mail_handler)
        mail_delivery_logger.propagate = False
