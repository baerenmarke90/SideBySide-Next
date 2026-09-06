"""Privacy-safe technical diagnostics for logs and persisted failure state.

Structured log traceback formatting (``formatting.py``) and the background
job/outbox failure-persistence boundaries (``jobs.queue.fail``,
``outbox.service.mark_failed``) both face the same problem: an *unexpected*
exception's own text is not developer-authored. It can be a provider's error
body, a database driver's rendering of a query, or a library echoing back
whatever a caller passed it — any of which can already contain a token, a
signed URL, or private content, none of which this module can enumerate in
advance.

The contract is therefore an allowlist, not a blocklist: only a bounded,
explicit technical code survives; anything else is reduced to the exception's
class name alone. This is deliberately the same rule
``engagement.push.sanitize_error_code`` already relies on for provider codes —
one canonical pattern, not a parallel one — extended here to exception text in
general. A blocklist of secret *patterns* (see ``redaction.scrub_message``) is
the right tool for a human-composed log message where most of the text is
supposed to survive; it is the wrong tool here, because it can only catch
secret shapes someone has already thought to write a rule for, and this
boundary specifically exists for content nobody has reviewed at all.
"""

from __future__ import annotations

import re
import traceback
from types import TracebackType

_TECHNICAL_CODE = re.compile(r"[A-Z0-9_-]{1,64}\Z")

UNKNOWN_CODE = "UNKNOWN"

_MAX_CHAIN_DEPTH = 10
_MAX_TRACEBACK_FRAMES = 50
_MAX_TRACEBACK_CHARS = 20_000

_CAUSE_HEADER = "\nThe above exception was the direct cause of the following exception:\n\n"
_CONTEXT_HEADER = "\nDuring handling of the above exception, another exception occurred:\n\n"


def sanitize_error_code(value: str, *, default: str = UNKNOWN_CODE) -> str:
    """Return `value` unchanged if it is a bounded technical code, else `default`.

    A technical code is developer-authored and never built from runtime data:
    ``ACCOUNT_UNAVAILABLE``, ``PROVIDER_ERROR``. The pattern is intentionally
    the whole contract rather than a maintained list of known-safe codes,
    exactly as ``engagement.push`` already relied on before this module
    existed; anything that is not a short, bounded, uppercase-alnum token is
    treated as unreviewed content, however short or plausible it looks.
    """
    candidate = value.strip().upper()
    if _TECHNICAL_CODE.fullmatch(candidate) is None:
        return default
    return candidate


def safe_exception_summary(exc: BaseException) -> str:
    """A bounded, privacy-safe one-line summary of `exc`.

    Always includes the exception's class name, which is written by a
    developer and never carries runtime data. The exception's own message is
    appended only when it already is a bounded technical code; otherwise it is
    dropped entirely rather than pattern-matched for known secret shapes, so
    an exception whose text happens not to look like a token or a URL is not
    mistaken for safe. This replaces the ``f"{type(exc).__name__}: {exc}"``
    pattern that previously persisted arbitrary exception prose into
    ``jobs.last_error`` / ``outbox_events.last_error``.

    Never raises: a `str(exc)` that itself fails (a badly written `__str__`)
    still yields the class name rather than propagating or falling back to
    something unsanitized.
    """
    name = type(exc).__name__
    try:
        text = str(exc).strip()
    except Exception:
        return name
    if not text:
        return name
    code = sanitize_error_code(text, default="")
    if code:
        return f"{name}: {code}"
    return name


def safe_traceback_text(
    exc_info: tuple[type[BaseException] | None, BaseException | None, TracebackType | None],
) -> str:
    """Render `exc_info` the way `logging.Formatter.formatException` would,
    except every exception's own message is replaced by
    `safe_exception_summary` first.

    Stack frames — file, line, function name, and the literal source line
    `linecache` reads for it — are kept as-is. They are code the developers
    wrote, not data a caller supplied, so unlike an exception's `str()` they
    cannot carry a token or private text pasted in from elsewhere; keeping
    them is what makes this a redaction of the message rather than a blanket
    replacement of the whole traceback. The cause/context chain and its two
    standard connecting sentences are preserved the same way, so a chained
    exception still reads as one, just without either exception's own prose.

    Bounded on three axes so a pathological exception cannot make logging
    itself expensive: chain depth, frames rendered per traceback, and the
    total rendered length. Never raises and never returns the unredacted
    original: if rendering itself fails for any reason, the result is a fixed
    placeholder string, not a fallback to `traceback.format_exception`.
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
    # Negative keeps the tail: the frames nearest the raise, which is what a
    # truncated traceback still needs to be useful. A positive limit keeps
    # the head (the entry point) instead, which is the wrong end to lose.
    lines.extend(traceback.format_tb(exc.__traceback__, limit=-_MAX_TRACEBACK_FRAMES))
    lines.append(safe_exception_summary(exc) + "\n")
    return lines
