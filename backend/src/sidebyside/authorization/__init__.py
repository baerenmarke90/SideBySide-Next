"""Owner- und Privacy-Autorisierung.

Die zweite Haelfte der Zugriffsfrage. Der Tenant Guard in
`sidebyside.relationship.service` klaert, ob ein Account zu einem Space
gehoert; erst danach beginnt hier die Frage, was er innerhalb dieses Space
sehen und aendern darf.

Eine Domaene braucht drei Dinge:

    class PrivateNote(IdMixin, TimestampMixin, PrivateResourceMixin, Base):
        __tablename__ = "private_notes"
        privacy_absence: ClassVar[ResourceAbsence] = ResourceAbsence(
            "Note not found.", "PRIVATE_NOTE_NOT_FOUND"
        )

    note = require_readable(session, PrivateNote, context, note_id)
    notes = session.execute(readable(PrivateNote, context)).scalars().all()

Mehr nicht. Es gibt keinen Ort, an dem eine Domaene ihre eigene
Sichtbarkeitsbedingung formuliert.
"""

from __future__ import annotations

from sidebyside.authorization.guard import (
    readable,
    require_readable,
    require_writable,
    require_writable_locked,
    writable,
)
from sidebyside.authorization.models import PrivateResource, PrivateResourceMixin
from sidebyside.authorization.privacy import (
    ENFORCEABLE_PRIVACY_CLASSES,
    AuthorizationContext,
    AuthorizationErrorCode,
    ContentVisibility,
    PrivacyClass,
    ResourceAbsence,
    SharedWrite,
    privacy_class_type,
    privacy_for,
    visibility_of,
)
from sidebyside.authorization.rules import Access, access_clause, privacy_clause

__all__ = [
    "ENFORCEABLE_PRIVACY_CLASSES",
    "Access",
    "AuthorizationContext",
    "AuthorizationErrorCode",
    "ContentVisibility",
    "PrivacyClass",
    "PrivateResource",
    "PrivateResourceMixin",
    "ResourceAbsence",
    "SharedWrite",
    "access_clause",
    "privacy_class_type",
    "privacy_clause",
    "privacy_for",
    "readable",
    "require_readable",
    "require_writable",
    "require_writable_locked",
    "visibility_of",
    "writable",
]
