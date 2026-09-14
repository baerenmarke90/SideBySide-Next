"""Registry and persistence for personal Dashboard presentation preferences.

Every separately rendered Today/Dashboard content module is centrally
registered here (#817). A module's key, default visibility and (where
applicable) item-limit capability live in one place so Settings and Today
composition cannot silently drift apart; both consume `CATALOG` rather than
duplicating module identity.

The App Shell/navigation and Today's "new space" empty state are not
Dashboard modules; the empty state only ever stands in for the configurable
module stack, never as a member of it. `RELATIONSHIP_PRESENCE` (the Today
Couple Presence hero) is registered like any other module - #817 makes no
core/high-priority exception - it is simply the one whose Today rendering
also carries the page's `<h1>`; see `web/src/components/TodayPage.tsx` for
how hiding it preserves an accessible heading without an empty hero shell.

This catalog's key order/identity is cross-checked against
`web/src/client/dashboardModuleCatalog.contract.json` by
`tests/unit/test_dashboard_catalog_parity.py`, and the Web catalog in
`web/src/client/dashboardModules.ts` is checked against the same file, so the
two layers cannot silently drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from sidebyside.core.errors import NotFoundError, ValidationError
from sidebyside.core.ids import new_id
from sidebyside.dashboard.models import DashboardModulePreference


class DashboardModuleKey(StrEnum):
    """Stable internal product keys for registered Dashboard modules."""

    RELATIONSHIP_PRESENCE = "relationship_presence"
    UPCOMING = "upcoming"
    KEEPSAKE = "keepsake"
    RELATIONSHIP_SIGNAL = "relationship_signal"
    MONTHLY_HIGHLIGHTS = "monthly_highlights"
    RECENT_SHARED = "recent_shared"


class DashboardPreferenceErrorCode:
    MODULE_NOT_FOUND = "DASHBOARD_MODULE_NOT_FOUND"
    FACET_NOT_SUPPORTED = "DASHBOARD_MODULE_FACET_NOT_SUPPORTED"


DashboardItemLimit = Literal[1, 2, 3]


@dataclass(frozen=True)
class ItemLimitCapability:
    """Optional per-module item-limit facet, owned by #848, not #817."""

    default: DashboardItemLimit
    allowed: frozenset[DashboardItemLimit]


@dataclass(frozen=True)
class DashboardModuleDefinition:
    key: DashboardModuleKey
    default_visible: bool
    item_limit: ItemLimitCapability | None = None


@dataclass(frozen=True)
class DashboardModuleState:
    key: DashboardModuleKey
    visible: bool
    item_limit: DashboardItemLimit | None


# Deterministic Settings/Today order, matching the accepted #850 Today
# composition (`web/src/components/TodayPage.tsx`): relationship_presence
# (the Couple Presence hero), then upcoming, keepsake, relationship_signal,
# monthly_highlights, recent_shared. #848 established `UPCOMING` with an
# item-limit facet; #817 adds mandatory visibility to every module,
# including `UPCOMING` itself.
#
# `SHARED_STORY_SUMMARY` (#809) is deliberately absent: it is not merged to
# `main`, and #817 does not implement #809 on its behalf. Once #809 lands, its
# module registers here the same way every other module did and automatically
# participates in this mechanism.
CATALOG: tuple[DashboardModuleDefinition, ...] = (
    DashboardModuleDefinition(key=DashboardModuleKey.RELATIONSHIP_PRESENCE, default_visible=True),
    DashboardModuleDefinition(
        key=DashboardModuleKey.UPCOMING,
        default_visible=True,
        item_limit=ItemLimitCapability(default=1, allowed=frozenset({1, 2, 3})),
    ),
    DashboardModuleDefinition(key=DashboardModuleKey.KEEPSAKE, default_visible=True),
    DashboardModuleDefinition(key=DashboardModuleKey.RELATIONSHIP_SIGNAL, default_visible=True),
    DashboardModuleDefinition(key=DashboardModuleKey.MONTHLY_HIGHLIGHTS, default_visible=True),
    DashboardModuleDefinition(key=DashboardModuleKey.RECENT_SHARED, default_visible=True),
)

_DEFINITIONS = {definition.key: definition for definition in CATALOG}


def module_definition(module_key: str) -> DashboardModuleDefinition:
    """Resolve a wire key through the typed registry or fail closed."""
    try:
        key = DashboardModuleKey(module_key)
    except ValueError as error:
        raise NotFoundError(
            "Dashboard module not found.",
            DashboardPreferenceErrorCode.MODULE_NOT_FOUND,
        ) from error
    definition = _DEFINITIONS.get(key)
    if definition is None:
        raise NotFoundError(
            "Dashboard module not found.",
            DashboardPreferenceErrorCode.MODULE_NOT_FOUND,
        )
    return definition


def read_module_preferences(
    session: Session,
    *,
    account_id: UUID,
    space_id: UUID,
) -> list[DashboardModuleState]:
    """Return effective preferences for every centrally registered module."""
    keys = [definition.key.value for definition in CATALOG]
    rows = session.execute(
        select(DashboardModulePreference).where(
            DashboardModulePreference.account_id == account_id,
            DashboardModulePreference.space_id == space_id,
            DashboardModulePreference.module_key.in_(keys),
        )
    ).scalars()
    overrides = {DashboardModuleKey(row.module_key): row for row in rows}
    return [_effective_state(definition, overrides.get(definition.key)) for definition in CATALOG]


def _effective_state(
    definition: DashboardModuleDefinition,
    override: DashboardModulePreference | None,
) -> DashboardModuleState:
    """Absence of an explicit override resolves to the catalog product default."""
    visible = (
        override.visible
        if override is not None and override.visible is not None
        else definition.default_visible
    )
    item_limit: DashboardItemLimit | None = None
    if definition.item_limit is not None:
        candidate = override.item_limit if override is not None else None
        item_limit = (
            candidate
            if candidate in definition.item_limit.allowed
            else definition.item_limit.default
        )
    return DashboardModuleState(key=definition.key, visible=visible, item_limit=item_limit)


def set_module_preference(
    session: Session,
    *,
    account_id: UUID,
    space_id: UUID,
    module_key: str,
    visible: bool | None,
    item_limit: int | None,
) -> DashboardModuleState:
    """Persist one private Account+Space override with a PostgreSQL-safe upsert.

    Only the facets a module actually supports may be set; requesting an
    unsupported facet (for example an item limit on a visibility-only module)
    fails closed rather than silently persisting inert state. Setting one
    facet never disturbs the other's already-persisted value.
    """
    definition = module_definition(module_key)

    if visible is None and item_limit is None:
        raise ValidationError(
            "At least one of visible or itemLimit must be supplied.",
            DashboardPreferenceErrorCode.FACET_NOT_SUPPORTED,
        )
    if item_limit is not None and definition.item_limit is None:
        raise ValidationError(
            f"The '{definition.key.value}' Dashboard module does not support an item limit.",
            DashboardPreferenceErrorCode.FACET_NOT_SUPPORTED,
        )
    if (
        item_limit is not None
        and definition.item_limit is not None
        and item_limit not in definition.item_limit.allowed
    ):
        raise ValidationError(
            "itemLimit must be validated at the API boundary",
            DashboardPreferenceErrorCode.FACET_NOT_SUPPORTED,
        )

    values: dict[str, object] = {
        "id": new_id(),
        "account_id": account_id,
        "space_id": space_id,
        "module_key": definition.key.value,
    }
    changes: dict[str, object] = {"updated_at": func.now()}
    if visible is not None:
        values["visible"] = visible
        changes["visible"] = visible
    if item_limit is not None:
        values["item_limit"] = item_limit
        changes["item_limit"] = item_limit

    statement = (
        insert(DashboardModulePreference)
        .values(**values)
        .on_conflict_do_update(
            constraint="uq_dashboard_module_preferences_account_space_module",
            set_=changes,
        )
        .returning(
            DashboardModulePreference.visible,
            DashboardModulePreference.item_limit,
        )
    )
    persisted_visible, persisted_item_limit = session.execute(statement).one()
    session.flush()

    effective_visible = (
        persisted_visible if persisted_visible is not None else definition.default_visible
    )
    effective_item_limit: DashboardItemLimit | None = None
    if definition.item_limit is not None:
        effective_item_limit = (
            cast(DashboardItemLimit, persisted_item_limit)
            if persisted_item_limit in definition.item_limit.allowed
            else definition.item_limit.default
        )
    return DashboardModuleState(
        key=definition.key,
        visible=effective_visible,
        item_limit=effective_item_limit,
    )
