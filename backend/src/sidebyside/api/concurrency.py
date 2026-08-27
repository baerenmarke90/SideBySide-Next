"""Optimistic concurrency at the HTTP boundary.

A resource version is sent as an ETag and returns in ``If-Match``. Conflict
checking therefore lives where HTTP already defines it instead of being a
special field in every request body.

A write without ``If-Match`` is rejected rather than silently accepted. A
missing header would otherwise be exactly how a client accidentally disables
conflict protection and causes an unnoticed lost update.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header

from sidebyside.core.errors import ErrorCode, ValidationError


def etag_for(version: int) -> str:
    """Encode a resource version as a strong ETag."""
    return f'"{version}"'


def parse_if_match(value: str) -> int:
    """Read the expected version from an ``If-Match`` header.

    Exactly one strong ETag is accepted, with or without quotes because both
    forms occur in practice.

    An empty value is treated as unusable because it does not name a version.

    Explicitly rejected:

    - ``*``, which only means "any current representation" and would bypass
      conflict protection;
    - weak validators such as ``W/\"...\"``, which are invalid for
      ``If-Match`` anyway;
    - multiple values, because a resource has exactly one version.
    """
    raw = value.strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        raw = raw[1:-1]

    if not (raw.isascii() and raw.isdigit()):
        raise ValidationError(
            "The If-Match header must carry a single concrete version.",
            ErrorCode.IF_MATCH_MALFORMED,
        )

    return int(raw)


def if_match_version(
    if_match: Annotated[
        str,
        Header(
            alias="If-Match",
            description=(
                "The last-read resource version, encoded as a strong ETag. "
                "Writes are rejected without this header."
            ),
        ),
    ],
) -> int:
    """Require and parse the optimistic-concurrency header.

    There is deliberately no default value, so OpenAPI also marks the header
    as required. Describing it as optional would invite clients to omit it,
    which would defeat conflict protection.
    """
    return parse_if_match(if_match)


IfMatchVersion = Annotated[int, Depends(if_match_version)]
