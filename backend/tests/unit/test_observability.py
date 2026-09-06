"""Unit tests for observability, structured logging, request correlation, and redaction."""

from __future__ import annotations

import asyncio
import json
import logging

import pytest
from starlette.responses import PlainTextResponse

from sidebyside.config import Environment, LogFormat, Settings
from sidebyside.core.ids import new_id
from sidebyside.observability import (
    REDACTED,
    ConsoleLogFormatter,
    JsonLogFormatter,
    RedactingFilter,
    RequestIdMiddleware,
    bind_actor_context,
    configure_logging,
    get_account_id,
    get_correlation_id,
    get_request_id,
    get_space_id,
    reset_context,
    safe_exception_summary,
    sanitize_error_code,
    scrub_data,
    scrub_headers,
    scrub_message,
    scrub_url,
    set_account_id,
    set_correlation_id,
    set_request_id,
    set_space_id,
)


class TestContextVariables:
    def setup_method(self) -> None:
        reset_context()

    def teardown_method(self) -> None:
        reset_context()

    def test_request_and_correlation_id_lifecycle(self) -> None:
        assert get_request_id() is None
        assert get_correlation_id() is None

        set_request_id("req-123")
        set_correlation_id("corr-456")

        assert get_request_id() == "req-123"
        assert get_correlation_id() == "corr-456"

        reset_context()
        assert get_request_id() is None
        assert get_correlation_id() is None

    def test_actor_and_space_binding(self) -> None:
        account_uuid = new_id()
        space_uuid = new_id()

        bind_actor_context(account_id=account_uuid, space_id=space_uuid)
        assert get_account_id() == str(account_uuid)
        assert get_space_id() == str(space_uuid)

        reset_context()
        assert get_account_id() is None
        assert get_space_id() is None

    @pytest.mark.asyncio
    async def test_context_isolation_across_tasks(self) -> None:
        async def task_worker(task_id: str) -> tuple[str | None, str | None]:
            set_request_id(f"req-{task_id}")
            set_correlation_id(f"corr-{task_id}")
            await asyncio.sleep(0.01)
            return get_request_id(), get_correlation_id()

        result_a, result_b = await asyncio.gather(task_worker("A"), task_worker("B"))

        assert result_a == ("req-A", "corr-A")
        assert result_b == ("req-B", "corr-B")


class TestRedaction:
    def test_scrub_url_query_params(self) -> None:
        url_with_tokens = (
            "https://example.com/api/v1/auth/callback?code=secret123&state=xyz&other=safe"
        )
        scrubbed = scrub_url(url_with_tokens)

        assert "secret123" not in scrubbed
        assert f"code={REDACTED}" in scrubbed
        assert "other=safe" in scrubbed

    def test_scrub_s3_presigned_url(self) -> None:
        s3_url = (
            "https://bucket.s3.amazonaws.com/media/photo.jpg?"
            "X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7EXAMPLE&"
            "X-Amz-Signature=d2c6e8f4a1b2c3d4e5f6"
        )
        scrubbed = scrub_url(s3_url)

        assert "d2c6e8f4a1b2c3d4e5f6" not in scrubbed
        assert "AKIAIOSFODNN7EXAMPLE" not in scrubbed
        assert f"X-Amz-Signature={REDACTED}" in scrubbed
        assert f"X-Amz-Credential={REDACTED}" in scrubbed

    def test_scrub_headers(self) -> None:
        headers = {
            "Authorization": "Bearer secret_bearer_token",
            "Cookie": "session=secret_cookie_value",
            "X-Bootstrap-Token": "secret_bootstrap",
            "X-Cursor-Key": "secret_cursor",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        scrubbed = scrub_headers(headers)

        assert scrubbed["Authorization"] == REDACTED
        assert scrubbed["Cookie"] == REDACTED
        assert scrubbed["X-Bootstrap-Token"] == REDACTED
        assert scrubbed["X-Cursor-Key"] == REDACTED
        assert scrubbed["Content-Type"] == "application/json"
        assert scrubbed["Accept"] == "application/json"

    def test_scrub_message_patterns(self) -> None:
        msg = (
            "Caller authenticated via Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz "
            "and password: 'myPassword123'"
        )
        scrubbed = scrub_message(msg)

        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz" not in scrubbed
        assert "myPassword123" not in scrubbed
        assert f"Bearer {REDACTED}" in scrubbed
        assert f"password={REDACTED}" in scrubbed

    def test_scrub_nested_data_and_domain_content(self) -> None:
        sensitive_payload = {
            "password": "super-secret-password",
            "bootstrap_token": "bootstrap-32-chars-long-secret",
            "body": "Private journal entry with very intimate memories",
            "text": "Heart moment text that should never be logged",
            "location": "Paris, 5th arrondissement",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "metadata": {
                "client_secret": "oidc-secret-value",
                "safe_field": 42,
                "nested_list": [
                    {"token": "token-in-list", "status": "active"},
                ],
            },
        }
        scrubbed = scrub_data(sensitive_payload)

        assert scrubbed["password"] == REDACTED
        assert scrubbed["bootstrap_token"] == REDACTED
        assert scrubbed["body"] == REDACTED
        assert scrubbed["text"] == REDACTED
        assert scrubbed["location"] == REDACTED
        assert scrubbed["latitude"] == REDACTED
        assert scrubbed["longitude"] == REDACTED
        assert scrubbed["metadata"]["client_secret"] == REDACTED
        assert scrubbed["metadata"]["safe_field"] == 42
        assert scrubbed["metadata"]["nested_list"][0]["token"] == REDACTED
        assert scrubbed["metadata"]["nested_list"][0]["status"] == "active"

    def test_redacting_filter_on_log_record(self) -> None:
        redacting_filter = RedactingFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="User failed auth with Bearer mySecretToken123",
            args=("Bearer tokenInArg456",),
            exc_info=None,
        )

        redacting_filter.filter(record)
        assert record.msg == "User failed auth with Bearer [REDACTED]"
        assert record.args == ("Bearer [REDACTED]",)


class TestFormatters:
    def setup_method(self) -> None:
        reset_context()

    def teardown_method(self) -> None:
        reset_context()

    def test_json_formatter_structure(self) -> None:
        formatter = JsonLogFormatter()
        set_request_id("req-test-json")
        set_correlation_id("corr-test-json")
        set_account_id("acc-test-json")
        set_space_id("space-test-json")

        record = logging.LogRecord(
            name="sidebyside.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=20,
            msg="Operation succeeded for item %d",
            args=(123,),
            exc_info=None,
        )
        record.__dict__["extra_key"] = "extra_value"

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["level"] == "INFO"
        assert data["logger"] == "sidebyside.test"
        assert data["message"] == "Operation succeeded for item 123"
        assert data["request_id"] == "req-test-json"
        assert data["correlation_id"] == "corr-test-json"
        assert data["account_id"] == "acc-test-json"
        assert data["space_id"] == "space-test-json"
        assert data["extra"]["extra_key"] == "extra_value"
        assert "timestamp" in data

    def test_console_formatter_output(self) -> None:
        formatter = ConsoleLogFormatter()
        set_request_id("req-console")

        record = logging.LogRecord(
            name="sidebyside.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=20,
            msg="Hello console",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        assert "INFO sidebyside.test [req=req-console] Hello console" in formatted

    def test_effective_log_format_in_settings(self) -> None:
        dev_settings = Settings(environment=Environment.DEVELOPMENT)
        assert dev_settings.effective_log_format == LogFormat.TEXT

        prod_settings = Settings(
            environment=Environment.PRODUCTION,
            allowed_hosts=["app.example"],
            cursor_signing_key="a" * 32,
            public_base_url="https://app.example",
            mail_transport="smtp",
        )
        assert prod_settings.effective_log_format == LogFormat.JSON

        explicit_settings = Settings(
            environment=Environment.DEVELOPMENT,
            log_format=LogFormat.JSON,
        )
        assert explicit_settings.effective_log_format == LogFormat.JSON


class TestMiddlewares:
    @pytest.mark.asyncio
    async def test_request_id_middleware_generates_and_propagates_id(self) -> None:
        captured_request_id: str | None = None
        captured_correlation_id: str | None = None

        async def inner_app(scope: dict, receive: object, send: object) -> None:
            nonlocal captured_request_id, captured_correlation_id
            captured_request_id = get_request_id()
            captured_correlation_id = get_correlation_id()
            response = PlainTextResponse("OK")
            await response(scope, receive, send)

        middleware = RequestIdMiddleware(inner_app)

        sent_messages: list[dict] = []

        async def fake_send(message: dict) -> None:
            sent_messages.append(message)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/health",
            "headers": [],
        }

        await middleware(scope, lambda: None, fake_send)

        assert captured_request_id is not None
        assert captured_correlation_id == captured_request_id
        # Response headers contain X-Request-ID
        start_message = next(msg for msg in sent_messages if msg["type"] == "http.response.start")
        header_dict = {
            k.decode("latin1").lower(): v.decode("latin1") for k, v in start_message["headers"]
        }
        assert header_dict.get("x-request-id") == captured_request_id

        # Context is cleaned up after request
        assert get_request_id() is None
        assert get_correlation_id() is None

    @pytest.mark.asyncio
    async def test_request_id_middleware_preserves_valid_incoming_id(self) -> None:
        captured_request_id: str | None = None

        async def inner_app(scope: dict, receive: object, send: object) -> None:
            nonlocal captured_request_id
            captured_request_id = get_request_id()
            response = PlainTextResponse("OK")
            await response(scope, receive, send)

        middleware = RequestIdMiddleware(inner_app)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/health",
            "headers": [(b"x-request-id", b"custom-client-id-12345")],
        }

        sent_messages: list[dict] = []

        async def fake_send(message: dict) -> None:
            sent_messages.append(message)

        await middleware(scope, lambda: None, fake_send)

        assert captured_request_id == "custom-client-id-12345"
        start_message = next(msg for msg in sent_messages if msg["type"] == "http.response.start")
        header_dict = {
            k.decode("latin1").lower(): v.decode("latin1") for k, v in start_message["headers"]
        }
        assert header_dict.get("x-request-id") == "custom-client-id-12345"

    @pytest.mark.asyncio
    async def test_request_id_middleware_replaces_invalid_incoming_id(self) -> None:
        captured_request_id: str | None = None

        async def inner_app(scope: dict, receive: object, send: object) -> None:
            nonlocal captured_request_id
            captured_request_id = get_request_id()
            response = PlainTextResponse("OK")
            await response(scope, receive, send)

        middleware = RequestIdMiddleware(inner_app)

        # Invalid characters (spaces, special chars)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/health",
            "headers": [(b"x-request-id", b"invalid id with spaces and <script>")],
        }

        sent_messages: list[dict] = []

        async def fake_send(message: dict) -> None:
            sent_messages.append(message)

        await middleware(scope, lambda: None, fake_send)

        assert captured_request_id != "invalid id with spaces and <script>"
        assert len(captured_request_id) > 10


SECRET_BEARER_TOKEN = "super-secret-token"
SECRET_SIGNED_URL_VALUE = "SECRET123"
PRIVATE_CONTENT_CANARY = "KANARIENPRIVATEINHALT"
SECRET_PASSWORD_VALUE = "very-secret"


def _canary_message() -> str:
    return (
        f"Bearer {SECRET_BEARER_TOKEN} "
        f"https://storage.example/object?X-Amz-Signature={SECRET_SIGNED_URL_VALUE} "
        f"private relationship text: {PRIVATE_CONTENT_CANARY} "
        f"password={SECRET_PASSWORD_VALUE}"
    )


def _assert_no_canaries(text: str) -> None:
    assert SECRET_BEARER_TOKEN not in text
    assert SECRET_SIGNED_URL_VALUE not in text
    assert PRIVATE_CONTENT_CANARY not in text
    assert SECRET_PASSWORD_VALUE not in text


class _ListHandler(logging.Handler):
    """Captures formatted output instead of writing anywhere, for assertions."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(self.format(record))


def _log_exception_with_formatter(formatter: logging.Formatter, message: str) -> str:
    """Exercise the real production path: a filtered, formatted `log.exception(...)` call.

    Mirrors `configure_logging()`'s own handler wiring (`RedactingFilter` plus
    one of the two registered formatters) rather than constructing a
    `LogRecord` by hand, so this proves the actual formatter output, not just
    the underlying `scrub_message`/`safe_traceback_text` helpers in isolation.
    """
    logger = logging.getLogger("sidebyside.test.exception_redaction")
    logger.setLevel(logging.ERROR)
    logger.propagate = False
    handler = _ListHandler()
    handler.addFilter(RedactingFilter())
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    try:
        try:
            raise RuntimeError(message)
        except RuntimeError:
            logger.exception("job failed", extra={"job_id": "job-1", "kind": "demo"})
    finally:
        logger.removeHandler(handler)
    assert handler.records, "log.exception(...) did not produce a record"
    return handler.records[0]


class TestExceptionTracebackRedaction:
    """#680: `record.exc_info` is formatted after `RedactingFilter` has already
    run, so a secret embedded only in an exception's message — never in the
    plain log message text — previously reached both the JSON and console
    sinks unredacted.
    """

    def test_json_log_exception_never_leaks_canaries_from_the_traceback(self) -> None:
        formatted = _log_exception_with_formatter(JsonLogFormatter(), _canary_message())
        _assert_no_canaries(formatted)

        data = json.loads(formatted)
        assert data["message"] == "job failed"
        assert "RuntimeError" in data["exception"]

    def test_console_log_exception_never_leaks_canaries_from_the_traceback(self) -> None:
        formatted = _log_exception_with_formatter(ConsoleLogFormatter(), _canary_message())
        _assert_no_canaries(formatted)
        assert "RuntimeError" in formatted
        assert "job failed" in formatted

    def test_retains_safe_stack_frame_information(self) -> None:
        """Not a blanket `[REDACTED]` traceback: file/line/function context survives."""
        formatted = _log_exception_with_formatter(JsonLogFormatter(), _canary_message())
        data = json.loads(formatted)
        assert "Traceback (most recent call last):" in data["exception"]
        assert "test_observability.py" in data["exception"]
        assert "_log_exception_with_formatter" in data["exception"]

    def test_chained_exception_omits_both_causes_own_message(self) -> None:
        logger = logging.getLogger("sidebyside.test.chained_exception_redaction")
        logger.setLevel(logging.ERROR)
        logger.propagate = False
        handler = _ListHandler()
        handler.addFilter(RedactingFilter())
        handler.setFormatter(JsonLogFormatter())
        logger.addHandler(handler)
        try:
            try:
                try:
                    raise ValueError(f"password={SECRET_PASSWORD_VALUE}")
                except ValueError as cause:
                    raise RuntimeError(f"Bearer {SECRET_BEARER_TOKEN}") from cause
            except RuntimeError:
                logger.exception("job failed")
        finally:
            logger.removeHandler(handler)

        formatted = handler.records[0]
        assert SECRET_PASSWORD_VALUE not in formatted
        assert SECRET_BEARER_TOKEN not in formatted
        data = json.loads(formatted)
        assert "ValueError" in data["exception"]
        assert "RuntimeError" in data["exception"]
        assert "direct cause" in data["exception"]

    def test_exception_message_that_is_itself_a_safe_code_survives(self) -> None:
        """Retryable/stable technical errors keep a useful diagnostic code."""
        formatted = _log_exception_with_formatter(JsonLogFormatter(), "ACCOUNT_UNAVAILABLE")
        data = json.loads(formatted)
        assert "ACCOUNT_UNAVAILABLE" in data["exception"]

    def test_str_raising_on_the_exception_does_not_crash_or_leak(self) -> None:
        class ExplodingError(Exception):
            def __str__(self) -> str:  # pragma: no cover - exercised via format
                raise RuntimeError(f"str raised with {SECRET_BEARER_TOKEN}")

        logger = logging.getLogger("sidebyside.test.pathological_exception")
        logger.setLevel(logging.ERROR)
        logger.propagate = False
        handler = _ListHandler()
        handler.addFilter(RedactingFilter())
        handler.setFormatter(JsonLogFormatter())
        logger.addHandler(handler)
        try:
            try:
                raise ExplodingError()
            except ExplodingError:
                logger.exception("job failed")
        finally:
            logger.removeHandler(handler)

        formatted = handler.records[0]
        assert SECRET_BEARER_TOKEN not in formatted
        data = json.loads(formatted)
        assert "ExplodingError" in data["exception"]


class TestSafeExceptionSummary:
    def test_class_name_always_present(self) -> None:
        assert safe_exception_summary(ValueError("not a bounded code")) == "ValueError"

    def test_arbitrary_prose_is_dropped_entirely(self) -> None:
        summary = safe_exception_summary(RuntimeError(_canary_message()))
        _assert_no_canaries(summary)
        assert summary == "RuntimeError"

    def test_bounded_technical_code_is_retained(self) -> None:
        summary = safe_exception_summary(RuntimeError("ACCOUNT_DELETION_CONVERGENCE_FAILED"))
        assert summary == "RuntimeError: ACCOUNT_DELETION_CONVERGENCE_FAILED"

    def test_empty_message_is_just_the_class_name(self) -> None:
        assert safe_exception_summary(RuntimeError()) == "RuntimeError"

    def test_str_failure_falls_back_to_the_class_name_only(self) -> None:
        class ExplodingError(Exception):
            def __str__(self) -> str:
                raise RuntimeError("boom")

        assert safe_exception_summary(ExplodingError()) == "ExplodingError"


class TestSanitizeErrorCode:
    def test_bounded_code_survives(self) -> None:
        assert sanitize_error_code("provider_timeout") == "PROVIDER_TIMEOUT"

    def test_free_text_is_replaced(self) -> None:
        assert sanitize_error_code("Connection refused by upstream") == "UNKNOWN"

    def test_custom_default_is_honored(self) -> None:
        assert sanitize_error_code("not a code!", default="FALLBACK") == "FALLBACK"


class TestUvicornLoggingBoundary:
    """#680: production starts via the bare `uvicorn` CLI, which runs its own
    `logging.config.dictConfig(...)` (inside `Config.__init__`) before this
    application's `configure_logging()` ever runs (`Config.load()`, which
    imports `sidebyside.main:app`, happens later in `Server.serve()`). Left
    alone, `uvicorn`/`uvicorn.access`/`uvicorn.error` each carry their own
    unredacted handler with `propagate=False`, bypassing this module's
    redaction boundary entirely.
    """

    def _production_settings(self) -> Settings:
        return Settings(
            environment=Environment.PRODUCTION,
            allowed_hosts=["app.example"],
            cursor_signing_key="a" * 32,
            public_base_url="https://app.example",
            mail_transport="smtp",
        )

    def _simulate_uvicorn_then_app_startup(self) -> None:
        import logging.config

        import uvicorn.config as uvicorn_config

        logging.config.dictConfig(uvicorn_config.LOGGING_CONFIG)
        configure_logging(self._production_settings())

    def teardown_method(self) -> None:
        for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
            logger = logging.getLogger(name)
            logger.handlers = []
            logger.propagate = True
        for handler in list(logging.getLogger().handlers):
            logging.getLogger().removeHandler(handler)

    def test_uvicorn_access_log_is_silenced_not_merely_unredacted(self, capsys) -> None:  # type: ignore[no-untyped-def]
        self._simulate_uvicorn_then_app_startup()

        logging.getLogger("uvicorn.access").info(
            '%s - "%s" %d',
            "127.0.0.1:12345",
            f"GET /api/v1/thing?token={SECRET_BEARER_TOKEN} HTTP/1.1",
            200,
        )

        output = capsys.readouterr().out
        assert SECRET_BEARER_TOKEN not in output
        # Silenced, not merely redacted-into-safety: nothing from this call
        # reaches the sink at all, since a raw request-line string cannot be
        # safely told apart from an ordinary query parameter after the fact.
        assert "GET /api/v1/thing" not in output

    def test_uvicorn_error_exception_reaches_the_redacted_sink(self, capsys) -> None:  # type: ignore[no-untyped-def]
        self._simulate_uvicorn_then_app_startup()

        try:
            raise RuntimeError(f"Bearer {SECRET_BEARER_TOKEN}")
        except RuntimeError:
            logging.getLogger("uvicorn.error").exception("Exception in ASGI application")

        output = capsys.readouterr().out
        assert SECRET_BEARER_TOKEN not in output
        # It must actually reach a sink (not also silently dropped): this is
        # the application's own redacted handler, proven by its JSON shape.
        assert "RuntimeError" in output
        assert "Exception in ASGI application" in output

    def test_uvicorn_startup_banner_reaches_the_redacted_sink(self, capsys) -> None:  # type: ignore[no-untyped-def]
        self._simulate_uvicorn_then_app_startup()

        logging.getLogger("uvicorn").info("Uvicorn running on http://0.0.0.0:8000")

        output = capsys.readouterr().out
        assert "Uvicorn running" in output
