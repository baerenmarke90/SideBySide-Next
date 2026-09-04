"""Privacy-class based retention cleanup shared by lifecycle workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from sqlalchemy import CursorResult

from sidebyside.authorization.privacy import PrivacyClass
from sidebyside.db.base import Base

# Attachment rows are always OWNER_ONLY technical upload records, but a bound
# attachment may belong to retained SPACE_SHARED content. The attachment
# binding/MediaStore lifecycle therefore owns those rows and must decide using
# the parent reference rather than owner_id alone.
_OWNER_ONLY_CLEANUP_EXCLUSIONS = frozenset({"attachments"})


@dataclass(frozen=True, slots=True)
class OwnerOnlyCleanupResult:
    total: int
    by_table: dict[str, int]


def _register_privacy_models() -> None:
    """Populate Base.metadata with every production privacy-aware domain model.

    Imports stay local to avoid turning the authorization package into a module
    initialization hub. Tests may register additional probe tables; those are
    intentionally discovered by the metadata scan as well.
    """
    from sidebyside.attachments import models as _attachments  # noqa: F401
    from sidebyside.chapters import models as _chapters  # noqa: F401
    from sidebyside.collections import models as _collections  # noqa: F401
    from sidebyside.comments import models as _comments  # noqa: F401
    from sidebyside.gift_ideas import models as _gift_ideas  # noqa: F401
    from sidebyside.heart_moments import models as _heart_moments  # noqa: F401
    from sidebyside.memories import models as _memories  # noqa: F401
    from sidebyside.milestones import models as _milestones  # noqa: F401
    from sidebyside.people import models as _people  # noqa: F401
    from sidebyside.places import models as _places  # noqa: F401
    from sidebyside.plans import models as _plans  # noqa: F401
    from sidebyside.private_collections import models as _private_collections  # noqa: F401
    from sidebyside.private_notes import models as _private_notes  # noqa: F401
    from sidebyside.profiles import models as _profiles  # noqa: F401
    from sidebyside.reminders import models as _reminders  # noqa: F401
    from sidebyside.wishes import models as _wishes  # noqa: F401


def owner_only_cleanup_table_names() -> tuple[str, ...]:
    """Return the current privacy-aware tables covered by Account cleanup."""
    _register_privacy_models()
    return tuple(
        table.name
        for table in reversed(Base.metadata.sorted_tables)
        if table.name not in _OWNER_ONLY_CLEANUP_EXCLUSIONS
        and "owner_id" in table.c
        and "privacy_class" in table.c
    )


def hard_delete_owner_only(session: Session, owner_id: UUID) -> OwnerOnlyCleanupResult:
    """Hard-delete every OWNER_ONLY row belonging to one Account.

    The privacy class is the authoritative predicate. Shared rows owned or
    authored by the same Account are deliberately untouched. Foreign-key-safe
    reverse metadata order removes child privacy-aware rows before parents;
    non-privacy children continue to use their existing database cascades.
    """
    _register_privacy_models()
    counts: dict[str, int] = {}

    for table in reversed(Base.metadata.sorted_tables):
        if table.name in _OWNER_ONLY_CLEANUP_EXCLUSIONS:
            continue
        if "owner_id" not in table.c or "privacy_class" not in table.c:
            continue

        result = cast(
            "CursorResult[Any]",
            session.execute(
                delete(table).where(
                    table.c.owner_id == owner_id,
                    table.c.privacy_class == PrivacyClass.OWNER_ONLY.value,
                )
            ),
        )
        affected = int(result.rowcount or 0)
        if affected:
            counts[table.name] = affected

    return OwnerOnlyCleanupResult(total=sum(counts.values()), by_table=counts)
