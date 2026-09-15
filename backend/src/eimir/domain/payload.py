"""Boundary between metadata and protected content.

The first release has NO end-to-end encryption. This module does not implement
it and must not be presented as if it did.

What it does is draw the boundary now so it does not need to be introduced
throughout the whole application later.

    Metadata                 ProtectedPayload
    ------------------       -----------------
    id, space_id             title
    author_id                body
    happened_on              other sensitive fields
    created_at
    crypto_version

In version 1 the payload is plaintext, `crypto_version = 0`. Later the same
field can contain ciphertext produced by the client, which the server never
sees in plaintext.

The consequence for everything built on top of this boundary: dashboards,
recaps, rules, and notifications should work from metadata. Anything requiring
plaintext will stop working after that transition, and that dependency should
be visible while writing the feature rather than years later.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict

CRYPTO_VERSION_PLAINTEXT = 0
"""Plaintext. Product version 1."""

CRYPTO_VERSION_CLIENT_SEALED = 1
"""Reserved for client-side encryption. Not implemented yet."""


class ProtectedPayload(BaseModel):
    """Base class for the protected part of a domain object.

    Domain objects derive from this class and add their sensitive fields. The
    rest of the object - everything needed for sorting, filtering, and linking
    - remains outside it.
    """

    model_config = ConfigDict(extra="forbid")

    crypto_version: ClassVar[int] = CRYPTO_VERSION_PLAINTEXT

    def seal(self) -> dict[str, Any]:
        """Convert the payload to its persisted representation.

        Today this is a lossless JSON mapping. Later this is the boundary where
        plaintext becomes ciphertext - or where it becomes explicit that the
        server no longer possesses plaintext at all.
        """
        return self.model_dump(mode="json")

    @classmethod
    def unseal(cls, stored: dict[str, Any] | None) -> Self:
        """Read a stored payload.

        A missing payload produces an empty object rather than an exception:
        after a transition to real encryption there may be rows the server
        cannot read. Such rows must not break an entire list.
        """
        return cls.model_validate(stored or {})


def is_readable_by_server(crypto_version: int) -> bool:
    """Return whether the server can read this row's content.

    Intended for derived features that depend on plaintext. They should be
    able to skip the row rather than guess.
    """
    return crypto_version == CRYPTO_VERSION_PLAINTEXT
