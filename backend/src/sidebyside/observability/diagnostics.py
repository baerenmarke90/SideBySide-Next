"""Privacy-safe technical diagnostics for logs and persisted failure state.

Unexpected exception text is untrusted runtime data. It can contain provider
bodies, database renderings, signed URLs, tokens, or private product content.
The generic exception boundary therefore never treats a value as safe merely
because it *looks* like a machine code.

A very small explicit compatibility allowlist may retain developer-authored
codes that were already part of the application's diagnostic contract. Every
other unexpected exception is reduced to its class name. Stable job/provider
codes continue to use their existing explicit code paths instead of being
recovered heuristically from ``str(exc)``.

Tracebacks retain bounded structural context (file basename, line number and
function name) but intentionally omit source-code lines. This keeps the stack
useful without copying another text surface into logs.
"""

from __future__ import annotations

import re
from collections import deque
from pathlib import Path
from types import TracebackType

_TECHNICAL_CODE = re.compile(r"[A-Z0-9_-]{1,64}\Z")

UNKNOWN_CODE = "UNKNOWN"

# These values are developer-authored compatibility codes, not a pattern-based
# trust decision. Do not add provider/user-derived values here.
_EXPLICIT_SAFE_EXCEPTION_CODES: dict[str, str] = {
    "ACCOUNT_UNAVAILABLE": "ACCOUNT_UNAVAILABLE",
    "ACCOUNT_DELETION_CONVERGENCE_FAILED": "ACCOUNT_DELETION_CONVERGENCE_FAILED",
}

_MAX_CHAIN_DEPTH = 10
_MAX_TRACEBACK_FRAMES = 50
_MAX_TRACEBACK_CHARS = 20_000
_MAX_FRAME_NAME_CHARS = 128
_MAX_FILENAME_CHARS = 256

_CAUSE_HEADER = "\nThe above exception was the direct cause of the following exception:\n\n"
_CONTEXT_HEADER = "\nDuring handling of the above exception, another exception occurred:\n\n"


def sanitize_error_code(value: str, *, default: str = UNKNOWN_CODE) -> str:
    """Normalize a value already known by its caller to be a technical code.

    This helper is deliberately *not* an exception-message sanitizer. Callers
    must already own the authority to classify ``value`` as a technical code;
    arbitrary exception/provider prose must not be passed here as a way to
    decide whether it is safe.
    """
    candidate = value.strip().upper()
    if _TECHNICAL_CODE.fullmatch(candidate) is None:
        return default
    return candidate


def safe_exception_summary(exc: BaseException) -> str:
    """Return a bounded, privacy-safe one-line summary of ``exc``.

    The exception class name is developer-authored structural metadata. The
    exception message is untrusted and is never returned directly. Two legacy
    developer-authored codes are retained through an explicit constant map;
    all other messages, including values that happen to match the technical
    code regex, are dropped.

    A broken ``__str__`` cannot break logging or persistence: it simply falls
    back to the class name.
    """
    name = type(exc).__name__
    try:
        message = str(exc).strip()
    except Exception:
        return name

    safe_code = _EXPLICIT_SAFE_EXCEPTION_CODES.get(message)
    if safe_code is not None:
        return f"{name}: {safe_code}"
    return name


def safe_traceback_text(
    exc_info: tuple[type[BaseException] | None, BaseException | None, TracebackType | None],
) -> str:
    """Render a bounded traceback without untrusted exception/source text.

    Cause/context relationships are preserved. Each stack retains only file
    basename, line number, and function name; literal source-code lines are not
    copied into the diagnostic. Exception messages are reduced through
    :func:`safe_exception_summary`.

    The renderer is bounded on chain depth, frames per traceback, frame-field
    length, and total output length. It never falls back to the stdlib's raw
    exception formatting if sanitization fails.
    """
    try:
        _, exc_value, _ = exc_info
        if exc_value is None:
            return ""
        rendered = "".join(_render_chain(exc_value, seen=set(), depth=0))
        if len(rendered) > _MAX_TRACEBACK_CHARS:
            rendered = rendered[:_MAX_TRACEBACK_CHARS] + "...<truncated>\n"
        return rendered
    except Exception:
        return "<traceback sanitization failed>"


def _render_chain(exc: BaseException, seen: set[int], depth: int) -> list[str]:
    if depth > _MAX_CHAIN_DEPTH or id(exc) in seen:
        return []
    seen.add(id(exc))

    lines: list[str] = []
    cause = exc.__cause__
    context = exc.__context__
    if cause is not None:
        lines.extend(_render_chain(cause, seen, depth + 1))
        lines.append(_CAUSE_HEADER)
    elif context is not None and not exc.__suppress_context__:
        lines.extend(_render_chain(context, seen, depth + 1))
        lines.append(_CONTEXT_HEADER)

    lines.append("Traceback (most recent call last):\n")
    lines.extend(_render_frames(exc.__traceback__))
    lines.append(safe_exception_summary(exc) + "\n")
    return lines


def _render_frames(tb: TracebackType | None) -> list[str]:
    """Render only structural frame metadata, keeping the tail nearest raise."""
    frames: deque[tuple[str, int, str]] = deque(maxlen=_MAX_TRACEBACK_FRAMES)
    cursor = tb
    while cursor is not None:
        code = cursor.tb_frame.f_code
        filename = Path(code.co_filename).name[:_MAX_FILENAME_CHARS] or "<unknown>"
        function = code.co_name[:_MAX_FRAME_NAME_CHARS] or "<unknown>"
        frames.append((filename, cursor.tb_lineno, function))
        cursor = cursor.tb_next

    return [
        f'  File "{filename}", line {line_number}, in {function}\n'
        for filename, line_number, function in frames
    ]
